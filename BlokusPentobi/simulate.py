import time
from .PentobiGTP import PentobiGTP

def play_game(players, game, verbose=False, timeout=60) -> PentobiGTP:
    """
    Given a PentobiGTP game and a list of players,
    play the game until it is finished or the timeout is reached.
    Args:
        players: A list of players participating in the game.
        game : The PentobiGTP object representing the game.
        verbose: Whether to print verbose output during the game. Defaults to False.
        timeout: Maximum time allowed for each move in seconds. Defaults to 60.

    Returns:
        game: The PentobiGTP object representing the game.
    """
    for player in players:
        player.set_pentobi_session(game)
    
    start_time = time.time()
    while not game.is_game_finished() and time.time() - start_time < timeout:
        # Get the current player
        player = players[game.current_player - 1]
        player.play_move()
        if verbose:
            print(game.board_as_text)
    return game

def play_game_with_args(players, game_kwargs, verbose=False, timeout=60) -> PentobiGTP:
    """
    Given a list of players and the initialization arguments for the game, play the game.
    Args:
        players: A list of players participating in the game.
        game_kwargs: Keyword arguments for configuring the game.
        verbose: Whether to print verbose output during the game. Defaults to False.
        timeout: Maximum time allowed for each move in seconds. Defaults to 60.

    Returns:
        game: The PentobiGTP object representing the game.
    """
    game = PentobiGTP(**game_kwargs)
    return play_game(players, game, verbose, timeout)

def play_game_with_args_and_save_result(players, game_kwargs, verbose=False, timeout=60, result_file="result.blksgf") -> PentobiGTP:
    """
    Play a game with the given arguments and save the result.

    Args:
        players: A list of players participating in the game.
        game_kwargs: Keyword arguments for configuring the game.
        verbose: Whether to print verbose output during the game. Defaults to False.
        timeout: Maximum time allowed for each move in seconds. Defaults to 60.
        result_file: File path to save the result in SGF format. Defaults to "result.blksgf".

    Returns:
        game: The PentobiGTP object representing the game.

    """
    game = play_game_with_args(players, game_kwargs, verbose, timeout)
    game.save_sgf(result_file)
    return game

    
