import os
import random
import subprocess
import multiprocessing
from typing import List
import numpy as np
from .utils import parse_gtp_board_to_matrix, EmptyLock


# Contains shared GTP sessions, that are only used for generating moves
_GTP_MOVE_SESSIONS = {}

def get_pentobi_move_session(starting_kwargs = {}):
    """ Get a shared PentobiGTP session, that is only used for generating moves.
        Args:
            level (int): The level of the GTP session. If you are using players that match the level of the session,
            the players are faster.
            starting_kwargs (dict, optional): Additional keyword arguments for the GTP session. Defaults to {}.

        Returns:
            PentobiGTP: The GTP session for generating moves with Pentobi.
    """
    global _GTP_MOVE_SESSIONS
    default_kwargs = {
        "gtp_path" : None,
        "level" : 1,
        "book" : None,
        "config" : None,
        "game" : "classic",
        "seed" : None,
        "showboard" : False,
        "nobook" : False,
        "noresign" : True,
        "threads" : 1,
    }
    # Create a hash from the starting kwargs, the order of the kwargs does not matter
    starting_kwargs = {**default_kwargs, **starting_kwargs}
    starting_kwargs_hash = hash(frozenset(starting_kwargs.items()))
    if starting_kwargs_hash not in _GTP_MOVE_SESSIONS:
        # We need to create a new session
        sess = PentobiGTP(**starting_kwargs)
        #print(f"Created new PentobiGTP args: {starting_kwargs}")
        _GTP_MOVE_SESSIONS[starting_kwargs_hash] = sess
    return _GTP_MOVE_SESSIONS[starting_kwargs_hash]

class PentobiGTP:
    """ Pentobi GTP interface wrapper.
    This class is used to start a Pentobi GTP process, and communicate with it.
    See more here: https://github.com/enz/pentobi/blob/main/pentobi_gtp/Pentobi-GTP.md
    """
    def __init__(self,
                 gtp_path=None,
                 book=None,
                 config=None,
                 game="classic",
                 level=1,
                 seed=None,
                 showboard=False,
                 nobook=False,
                 noresign=True,
                 threads=1,
                 ):
        """
        Starts a Pentobi GTP process and communicate with it.
        Args:
            gtp_path (str, optional): The file path to the Pentobi GTP binary. If not found, it is searched from the current directory. Defaults to None.
            book (str, optional): The file path to the opening book. Defaults to None.
            config (str, optional): The file path to the configuration file. Defaults to None.
            game (str, optional): The game mode. Only "classic" is supported. Defaults to "classic".
            level (int, optional): The level of the AI. Must be between 1 and 9. Defaults to 1.
            seed (int, optional): The seed for random number generation. Defaults to None.
            showboard (bool, optional): Whether to show the board. Defaults to False.
            nobook (bool, optional): Whether to disable the opening book. Defaults to False.
            noresign (bool, optional): Whether to disable resigning. Defaults to True.
            threads (int, optional): The number of threads to use. Defaults to 1.
        """
        
        if game != "classic":
            raise NotImplementedError("Only classic game is supported")
        if level < 1 or level > 9:
            raise ValueError("Level must be between 1 and 9")
        command = gtp_path if gtp_path else os.environ.get("PENTOBI_GTP")
        # Check that the command is not a valid file path
        if command is None or not os.path.isfile(command):
            print(f"Command {command} is not a valid file path, searching from current directory...")
            command = self._find_pentobi_gtp_binary()
            if command != None:
                print(f"Found command: {command}")
            else:
                raise ValueError("Pentobi GTP binary not found")
        self.level = level
        # Build the command to start the pentobi-gtp process
        command = [command]
        if book:
            command.append(f'--book {book}')
        if config:
            command.append(f'--config {config}')
        command.append(f'--game {game}')
        command.append(f'--level {level}')
        if seed:
            command.append(f'--seed {seed}')
        if showboard:
            command.append('--showboard')
        if nobook:
            command.append('--nobook')
        if noresign:
            command.append('--noresign')
        command.append(f'--threads {threads}')
        command = ' '.join(command)
        self.command = command
        #print(f"Starting pentobi-gtp with command: {command}")
        # Start the pentobi-gtp process in an invisible window
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=True,
        )
        self.previous_players = []
        self.current_player = 1
        # Lock to ensure thread-safe access to the process
        self.lock = multiprocessing.Lock()
        # Send showboard to get the initial board state
        test = self.send_command("showboard")
        # Check that the process is running, and what is the output
        if self.process.poll() is not None:
            raise ValueError(f"Error:  GTP process failed to start with code {self.process.returncode}")
        
    def _find_pentobi_gtp_binary(self) -> str:
        """
        Finds the path to a file named 'pentobi-gtp'. Searches from the current directory.
        """
        # From the currect directory, search for the pentobi-gtp binary
        current_dir = os.getcwd()
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                print(file)
                if file == "pentobi-gtp":
                    pent_gtp = os.path.join(root, file)
                    #os.environ["PENTOBI_GTP"] = pent_gtp
                    return pent_gtp
        return None
    
    @property
    def board_as_text(self) -> str:
        """ The current board state as text
        """
        return self.send_command("showboard")
    
    @property
    def board(self) -> np.ndarray:
        """ The current board state as a numpy matrix
        """
        return parse_gtp_board_to_matrix(self.board_as_text)
    
    @property
    def score(self) -> List[int]:
        """ The current score of the game
        """
        sc = self.send_command("final_score")
        #= 85 81 77 65
        sc = sc.split(" ")
        sc = [int(x) for x in sc[1:]]
        #if self.is_game_finished():
        #    winner_idx = np.argmax(sc)
        #    sc[winner_idx] += 50
        return sc
    
    def load_sgf(self, sgf_file, lock_process=True) -> None:
        """ Load a .blksgf file as the current state of the game.
        If you haven't already obtained the lock, then lock_process should be True, otherwise False.
        """
        if not os.path.isfile(sgf_file):
            raise ValueError(f"File {sgf_file} not found")
        assert sgf_file.endswith(".blksgf"), "File must be a .blksgf file"
        self.send_command(f"loadsgf {sgf_file}", lock_process=lock_process)
        
    def save_sgf(self, sgf_file, overwrite=True, lock_process=True) -> None:
        """ Save the current state of the game to a .blksgf file.
        If you haven't already obtained the lock, then lock_process should be True, otherwise False.
        """
        if os.path.isfile(sgf_file) and not overwrite:
            raise ValueError(f"File {sgf_file} already exists")
        assert sgf_file.endswith(".blksgf"), "File must be a .blksgf file"
        self.send_command(f"savesgf {sgf_file}",lock_process=lock_process)
        
    def set_to_state(self, other, lock_process=True) -> None:
        """ Copy the state of the other PentobiGTP instance to this one
        by saving the state of the other object to a file, and loading it.
        The other object is not modified.
        """
        temp_file_path = str(hash(str(other.board))) + str(random.randint(0, 2**32-1)) + ".blksgf"
        # Save the state of the other object to a file
        other.save_sgf(temp_file_path, overwrite=True, lock_process=lock_process)
        # Load the state of the other object to this object
        self.load_sgf(temp_file_path, lock_process=lock_process)
        self.current_player = other.current_player
        # Remove the temporary file
        os.remove(temp_file_path)
        
        
        
    def send_command(self, command, raise_errors=True, lock_process=True) -> str:
        """
        Sends a command to the process and returns the response.
        If you haven't already obtained the lock, then lock_process should be True, otherwise False.
        Args:
            command (str): The command to send to the process.
            raise_errors (bool): If True (default), raise an exception if the command fails.
        Returns:
            str: The response from the process.
        Raises:
            Exception: If the command fails and raise_errors is True.
            
        """
        lock = self.lock if lock_process else EmptyLock()
        with lock:
            # Send the command to the process
            self.process.stdin.write(command + '\n')
            self.process.stdin.flush()
            # Read the response from the process
            response = self._read_response()
            if "?" in response and raise_errors:
                raise Exception(f"Command '{command}' failed: {response}")
        return response

    def _read_response(self) -> str:
        """ Read the response (txt) from the process.
        """
        response = []
        while True:
            line = self.process.stdout.readline().strip()
            if line == '':
                break
            response.append(line)
        return '\n'.join(response)
    
    def _check_pid_has_turn(self,pid) -> bool:
        """ Check if the player has the turn.
        """
        if pid != self.current_player:
            print(f"Error: Player {pid} is not the current player")
            return False
        return True
    
    def _change_player(self, pid):
        self.current_player = (pid % 4) + 1
    
    def generate_internal_move(self, pid, lock_process=True) -> str:
        """ Generate a move for the player with pid (THE PID MUST BE IN TURN).
        If no move is possible, return 'pass'.
        The move selection algorithm is based on the level of THIS GTP session.
        """
        if not self._check_pid_has_turn(pid):
            raise ValueError(f"Player {pid} is not in turn!")
        out = self.send_command(f"reg_genmove {pid}", raise_errors=False, lock_process=lock_process)
        # = a1,b1 ...
        if "?" in out:
            return "pass"
        move = out.replace("= ", "")
        return move
    
    def undo_last_move(self, lock_process=True) -> None:
        """ Undo the last move.
        """
        if len(self.previous_players) == 0:
            return
        out = self.send_command("undo", lock_process=lock_process)
        if "?" in out:
            raise ValueError("Undo failed")
        self.current_player = self.previous_players.pop()
    
    def play_move(self, pid, move, lock_process=True) -> bool:
        """ Play a move for the player with pid (Has to be in turn).
        The move is specified as a string, e.g. 'a1,b1,b2'.
        If the move is 'pass', the player passes the turn.
        """
        if not self._check_pid_has_turn(pid):
            raise ValueError(f"Player {pid} is not in turn!")
        if move != "pass":
            self.send_command(f"play {pid} {move}", lock_process=lock_process)
        self.previous_players.append(pid)
        self._change_player(pid)
        return True
    
    def close(self, lock_process=True):
        """ Close the Pentobi GTP process.
        """
        self.send_command("quit", lock_process=lock_process)
        self.process.communicate()
        self.process.terminate()
        self.process.wait()
    
    def get_legal_moves(self, pid, lock_process=True) -> List[str]:
        """ Get a list of legal moves for the player with pid.
        """
        out = self.send_command(f"all_legal {pid}", lock_process=lock_process)
        moves = out.replace("=", "").split("\n")
        moves = list(map(lambda mv : mv.strip(),filter(lambda x: x != "", moves)))
        #print(f"Found moves: {moves}")
        if len(moves) == 0:
            #print(f"Player {pid} has no legal moves")
            moves = ["pass"]
        return moves
    
    def is_game_finished(self, lock_process=True) -> bool:
        """ Check if the game is finished. The game is finished if no players have remaining legal moves.
        """
        for pid in range(1,5):
            moves = self.get_legal_moves(pid, lock_process=lock_process)
            # If the response is empty, the player has no legal moves
            if len(moves) != 1 or moves[0] != "pass":
                return False
            else:
                pass
        return True

if __name__ == "__main__":
            
    def random_playout(proc : PentobiGTP, state_file, start_pid):
        """ Play a random game starting from the current state.
        """
        proc.send_command("clear_board")
        proc._change_player(start_pid)
        # Set the board to the state
        proc.send_command("loadsgf " + state_file)
        # Play random moves until the game is finished
        while not proc.is_game_finished():
            pid = proc.current_player
            moves = proc.get_legal_moves(pid)
            move = random.choice(moves)
            proc.play_move(pid, move)
        return proc.score
    

