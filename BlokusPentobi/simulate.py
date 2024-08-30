import time
from .PentobiGTP import PentobiGTP

def play_game(players, game, verbose=False, timeout=60):
    """
    Play a game between the players.
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

def play_game_with_args(players, game_kwargs, verbose=False, timeout=60):
    """
    Play a game between the players.
    """
    game = PentobiGTP(**game_kwargs)
    return play_game(players, game, verbose, timeout)

def play_game_with_args_and_save_result(players, game_kwargs, verbose=False, timeout=60, result_file="result.blksgf"):
    """
    Play a game between the players.
    """
    game = play_game_with_args(players, game_kwargs, verbose, timeout)
    game.save_sgf(result_file)
    return game

    
