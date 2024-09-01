import os
import random
from typing import List
import warnings
import numpy as np

from .PentobiGTP import PentobiGTP, get_pentobi_move_session

    
class PentobiInternalPlayer:
    def __init__(self,
                 pid : int,
                 pentobi_sess : PentobiGTP = None,
                 level=1,
                 move_selection_strategy="best",
                 move_selection_kwargs={},
                 name="PentobiInternalPlayer"
                 ):
        """
        Initializes a PentobiInternalPlayer object. This player can only play moves using a PentobiGTP session.
        Args:
            pid (int): The player ID.
            pentobi_sess (PentobiGTP, optional): A separate PentobiGTP session to get moves from a session with different (level) settings. If None, then the player will use the session it is provided with. Defaults to None.
            level (int, optional): The level of the player. Defaults to 1.
            move_selection_strategy (str, optional): The move selection strategy. Can be "best", "random", or "epsilon_greedy". Defaults to "best".
            move_selection_kwargs (dict, optional): Additional keyword arguments for the move selection strategy. Defaults to {}.
            name (str, optional): The name of the player. Defaults to "PentobiInternalPlayer".
        """
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
        """ Create a PentobiGTP session for getting the next move.
        """
        if self.has_separate_pentobi_sess:
            print(f"Creating PentobiGTP session for player {self.pid} with level {level}")
            return get_pentobi_move_session({"level": level})
        return self.pentobi_sess

    def set_move_session_state(self, lock_process=True):
        """ Set the state of the get_move_pentobi_sess to the state of the pentobi_sess,
        to prepare for getting the next move from the get_move_pentobi_sess.
        """
        if not self.has_separate_pentobi_sess:
            return
        self.move_pentobi_sess.set_to_state(self.pentobi_sess, lock_process=lock_process)
    
    def _make_move_with_pentobi_sess(self):
        """ Get the next move from the get_move_pentobi_sess."""
        # We need to wait for the lock for the get_move_pentobi_sess
        # because it is shared.
        # We already have the lock for the pentobi_sess
        with self.move_pentobi_sess.lock:
            # Once we have the lock, we set the state of the get_move_pentobi_sess to the state of the 'pentobi_sess'
            self.set_move_session_state(lock_process=False)
            mv = self.move_pentobi_sess.generate_internal_move(self.pid, lock_process=False)
        return mv
    
    def play_move(self):
        """ Play a move using the pentobi_sess and the move_selection_strategy.
        """
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
    def __init__(self,
                 pid : int,
                 pentobi_sess : PentobiGTP,
                 move_selection_strategy="best",
                 move_selection_kwargs={},
                 name="PentobiExternalPlayer"
                 ):
        """ Initializes a PentobiExternalPlayer object.
        This player can play moves using simple external evaluation functions or heuristics.
        A custom player can be created by inheriting from this class and implementing the evaluate_board method.
        Args:
            pid (int): The player ID.
            pentobi_sess (PentobiGTP): A PentobiGTP session to play moves with.
            move_selection_strategy (str, optional): The move selection strategy. Can be "best", "random", or "epsilon_greedy". Defaults to "best".
            move_selection_kwargs (dict, optional): Additional keyword arguments for the move selection strategy. Defaults to {}.
            name (str, optional): The name of the player. Defaults to "PentobiExternalPlayer".
        """
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


    def calc_next_states(self, moves, lock_process=True) -> List[np.ndarray]:
        """ Calculate the next states of the board after playing each move in 'moves'.
        """
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
        """ Make a move using the external player evaluation function.
        """
        next_states = self.calc_next_states(moves, lock_process=lock_process)
        values = [self.evaluate_board(board) for board in next_states]
        best_move_idx = np.argmax(values)
        return moves[best_move_idx]
    
    
    def play_move(self):
        """
        Plays a move for the player.
        This method selects a move from the available legal moves based on the move selection strategy specified during initialization.
        The move can be selected randomly, using an epsilon-greedy strategy, or by choosing the best move.
        """
        
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
    
class GreedyExternalPlayer(PentobiExternalPlayer):
    """ A simple external player that plays the move that maximizes the number of pieces of the player
    and minimizes the number of pieces of the opponent.
    """
    def evaluate_board(self, board):
        """ Evaluate the board by counting the number of pieces of the player and the opponent.
        """
        player_count = np.sum(board == self.pid)
        opponent_count = np.sum(board == 4 - self.pid)
        return player_count - opponent_count
            