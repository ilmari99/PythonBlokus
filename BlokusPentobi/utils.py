import numpy as np

def parse_gtp_board_to_matrix(board):
    """
    Parse the board as printed by the GTP engine to a numpy matrix.
    
    Example:
    20 X X . X O O O O # # # # X X X X X . . O  Blue(X): 82!
    19 . X . X X . . # O . X X . . O O O X . O  I3 I4
    18 . X X # X . . # O . X X O . O X X O O O
    17 . # # X # # # . O X . . O O . O O X X X
    16 # . # X X # # . O X X X O . O O . O O X  Yellow(O): 82!
    15 # . # . X X . . O X O . O . O . . O . .  I3 Z4
    14 # # . X . . X X X O O . . O . O O . O O
    13 . # X X X X # # X O . O O O X . O O . O
    12 # X # # . # . # X O . O . . X X O X O O  Red(#): 77!
    11 # X # . # # # . # X X X . X X O X X X .  O T4 Z4
    10 # X # # @ # X # # # # X X>O . O . X O O
    9 @ X X @ @ @ X X @ . @ # . X O O O . O O
    8 @ @ @ X @ X @ @ @ . @ # X X X . . O . .  Green(@): 61!
    7 @ . . X X X @ X X @ @ # # # O O O O . .  I3 I4 L4 O P V3 Y
    6 . @ @ . @ @ X X X @ # @ @ O # # . . O .
    5 @ @ . @ @ # @ @ # # # @ O O @ # # O O .
    4 . . . @ . # # # . # . @ @ O @ @ # O O .
    3 @ @ @ . . # @ @ @ @ @ . O @ @ . @ # . .
    2 @ # # # # @ # # # # # O O O . @ @ # # #
    1 @ # . . . @ @ @ @ O O . O . @ . @ . . #
    A B C D E F G H I J K L M N O P Q R S T
    """
    # Substitute > or < with a space
    board = board.replace(">", " ").replace("<", " ")
    board_in_lines = board.split("\n")
    board_in_lines = board_in_lines[1:-1]
    board_in_lines_splitted = [line.split(" ") for line in board_in_lines]
    # remove empty elements
    board_in_lines_splitted = [list(filter(lambda x: x != "", line)) for line in board_in_lines_splitted]
    #print(board_in_lines_splitted)

    # Skip the row number, and only take the first 20 columns
    for i in range(0, len(board_in_lines_splitted)):
        #print(board_in_lines_splitted[i])
        board_in_lines_splitted[i] = board_in_lines_splitted[i][1:21]
        #print(board_in_lines_splitted[i])
    # Remove the last row
    #board_in_lines_splitted = board_in_lines_splitted[:-1]
    #print(board_in_lines_splitted)
    conversion_map = {
        "." : -1,
        "X" : 0,
        "O" : 1,
        "#" : 2,
        "@" : 3,
        "+" : -1,
    }
    board_matrix = []
    for line in board_in_lines_splitted:
        board_matrix.append([conversion_map[x] for x in line])
    return np.array(board_matrix)

class EmptyLock:
    """ A dummy lock that does nothing
    """
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_value, traceback):
        pass
    def acquire(self):
        pass
    def release(self):
        pass