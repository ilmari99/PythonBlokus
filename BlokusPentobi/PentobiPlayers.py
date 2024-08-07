import os
import random
import warnings
import numpy as np

from PentobiGTP import PentobiGTP, get_pentobi_move_session

    
class PentobiInternalPlayer:
    def __init__(self,
                 pid : int,
                 pentobi_sess : PentobiGTP = None,
                 level=1,
                 move_selection_strategy="best",
                 move_selection_kwargs={},
                 name="PentobiInternalPlayer"
                 ):
        self.pid = pid
        self.pentobi_sess : PentobiGTP = pentobi_sess
        # We can provide a separate PentobiGTP session to get moves from a session with different (level) settings
        self.level = level
        self.name = name
        self.move_pentobi_sess = self.get_move_pentobi_sess(level)
        
        #if get_move_pentobi_sess is None:
        #    self.get_move_pentobi_sess : PentobiGTP = pentobi_sess
            
        self.move_selection_strategy = move_selection_strategy
        self.move_selection_kwargs = move_selection_kwargs
        assert move_selection_strategy in ["best", "random", "epsilon_greedy"], f"Invalid move selection strategy: {move_selection_strategy}"
        
        if move_selection_strategy != "epsilon_greedy":
            assert not move_selection_kwargs, f"move_selection_kwargs should be empty for move_selection_strategy: {move_selection_strategy}"
        
        if move_selection_strategy == "epsilon_greedy" and "epsilon" not in move_selection_kwargs:
            warnings.warn("No epsilon provided for epsilon_greedy move selection strategy. Defaulting to epsilon=0.1")
            self.move_selection_kwargs["epsilon"] = 0.1
            
    def set_pentobi_session(self, pentobi_sess):
        self.pentobi_sess = pentobi_sess
        self.move_pentobi_sess = self.get_move_pentobi_sess(self.level)
        return
    
    @property
    def has_separate_pentobi_sess(self):
        if self.pentobi_sess is None:
            return False
        return self.pentobi_sess.level != self.level
            
    def get_move_pentobi_sess(self, level):
        if self.has_separate_pentobi_sess:
            print(f"Creating PentobiGTP session for player {self.pid} with level {level}")
            return get_pentobi_move_session(level)
        return self.pentobi_sess

    def set_move_session_state(self, lock_process=True):
        """ Set the state of the get_move_pentobi_sess to the state of the pentobi_sess,
        to prepare for getting the next move from the get_move_pentobi_sess.
        """
        if not self.has_separate_pentobi_sess:
            return
        self.move_pentobi_sess.set_to_state(self.pentobi_sess, lock_process=lock_process)
    
    def _make_move_with_pentobi_sess(self):
        # We need to wait for the lock for the get_move_pentobi_sess
        # because it is shared.
        # We already have the lock for the pentobi_sess
        with self.move_pentobi_sess.lock:
            # Once we have the lock, we set the state of the äget_move_pentobi_sessä to the state of the 'pentobi_sess'
            self.set_move_session_state(lock_process=False)
            mv = self.move_pentobi_sess.generate_internal_move(self.pid, lock_process=False)
        return mv
    
    def play_move(self):
        if self.move_selection_strategy == "random":
            all_moves = self.pentobi_sess.get_legal_moves(self.pid)
            selected_move = random.choice(all_moves)
        elif self.move_selection_strategy == "epsilon_greedy":
            if np.random.rand() < self.move_selection_kwargs["epsilon"]:
                all_moves = self.pentobi_sess.get_legal_moves(self.pid)
                selected_move = random.choice(all_moves)
            else:
                selected_move = self._make_move_with_pentobi_sess()
        elif self.move_selection_strategy == "best":
            selected_move = self._make_move_with_pentobi_sess()
        #print(f"Player {self.pid} chose move: {selected_move}", flush=True)
        if selected_move == "=":
            selected_move = "pass"
        self.pentobi_sess.play_move(self.pid, selected_move)
        return
    


class PentobiExternalPlayer:
    """ An external player, that has to provide an evaluation of a board state, and then it can make a move.
    """
    def __init__(self,
                 pid : int,
                 pentobi_sess : PentobiGTP,
                 move_selection_strategy="best",
                 move_selection_kwargs={},
                 name="PentobiExternalPlayer"
                 ):
        self.pid = pid
        self.pentobi_sess : PentobiGTP = pentobi_sess
        self.name = name
        self.move_selection_strategy = move_selection_strategy
        self.move_selection_kwargs = move_selection_kwargs
        assert move_selection_strategy in ["best", "random", "epsilon_greedy"], f"Invalid move selection strategy: {move_selection_strategy}"
        
        if move_selection_strategy != "epsilon_greedy":
            assert not move_selection_kwargs, f"move_selection_kwargs should be empty for move_selection_strategy: {move_selection_strategy}"
            
        if move_selection_strategy == "epsilon_greedy" and "epsilon" not in move_selection_kwargs:
            warnings.warn("No epsilon provided for epsilon_greedy move selection strategy. Defaulting to epsilon=0.1")
            self.move_selection_kwargs["epsilon"] = 0.1
            
    def evaluate_board(self, board):
        """ This method returns a numeric value for the board state.
        The state with the highest value is considered the best.
        The evaluation should be done with the assumption, that
        this player has just played a move, and it is the opponent's turn.
        """
        raise NotImplementedError("evaluate_board method not implemented")


    def calc_next_states(self, moves, lock_process=True):
        next_states = []
        for move in moves:
            if move == "pass":
                continue
            self.pentobi_sess.play_move(self.pid, move, lock_process=lock_process)
            board = self.pentobi_sess.board
            next_states.append(board)
            self.pentobi_sess.undo_last_move(lock_process=lock_process)
        return next_states


    def _make_move_with_external_player(self, moves, lock_process=True):
        next_states = self.calc_next_states(moves, lock_process=False)
        values = [self.evaluate_board(board) for board in next_states]
        best_move_idx = np.argmax(values)
        return moves[best_move_idx]
    
    
    def play_move(self):
        # We can get the lock once here, and set lock_process = False for the rest of the calls
        with self.pentobi_sess.lock:
            all_moves = self.pentobi_sess.get_legal_moves(self.pid, lock_process=False)
            if self.move_selection_strategy == "random":
                selected_move = random.choice(all_moves)
            elif self.move_selection_strategy == "epsilon_greedy":
                if np.random.rand() < self.move_selection_kwargs["epsilon"]:
                    selected_move = random.choice(all_moves)
                else:
                    selected_move = self._make_move_with_external_player(all_moves, lock_process=False)
            elif self.move_selection_strategy == "best":
                selected_move = self._make_move_with_external_player(all_moves, lock_process=False)
            if selected_move == "=":
                selected_move = "pass"
            self.pentobi_sess.play_move(self.pid, selected_move, lock_process=False)
        return
            