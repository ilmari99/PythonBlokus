import numpy as np

def rotate_board_to_perspective(board, perspective_pid) -> np.ndarray:
    """ Rotate the board to the perspective of perspective_pid.
    That means, the perspective_pid will be at the top left corner of the board.
    Args:
        board: np.array of shape (20, 20) where each element is the player id of the player that has a piece in that cell, and empty cells are -1.
        perspective_pid: The player id of the player that we want to have the perspective of.
    """
    # First, we find the corner that has the perspective_pid
    top_left_pid = board[0,0]
    top_right_pid = board[0,-1]
    bottom_right_pid = board[-1,-1]
    bottom_left_pid = board[-1,0]
    corner_pids = [top_left_pid, top_right_pid, bottom_right_pid, bottom_left_pid]
    #print(f"Corner pids: {corner_pids}")
    
    # Find the index of the corner that has the perspective_pid
    if perspective_pid not in corner_pids:
        corner_index = 0
        print(f"Perspective pid {perspective_pid} not found in the corners: {corner_pids}")
    else:
        corner_index = corner_pids.index(perspective_pid)
    
    # Rotate the board to make the corner with the perspective_pid the top left corner
    board = np.rot90(board, k=corner_index)
    #print(board)
    return board

def normalize_board_to_perspective(board, perspective_pid) -> np.ndarray:
    """ Given a board, modify the so that the perspective_pid is always 0, the next player is 1, and so on.
    """
    # Add 4 - perspective_pid to each element of the board,
    # so that the perspective_pid is always 0, the next player is 1, and so on.
    perspective_full = 4 - np.full(board.shape, perspective_pid)
    # Get a mask that describes where the board == -1
    mask = board == -1
    
    # Now, we can add the perspective pid to each element
    # of the board and take mod 3
    # This makes the perspective_pid 0, the next player will be 1, and the next 2 ...
    board = board + perspective_full
    board = np.mod(board, 4)
    
    # In the add and mod we lose the -1's, so we need to set them back
    board = np.where(mask, -1, board)
    
    board = rotate_board_to_perspective(board, 0)
    
    return board