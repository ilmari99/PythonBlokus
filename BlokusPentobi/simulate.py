from collections import Counter
import gc
import json
import multiprocessing
import os
import random
import argparse
import time
from typing import Dict
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np
from PentobiGTP import PentobiGTP
from PentobiPlayers import PentobiInternalPlayer, PentobiExternalPlayer
import argparse

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



players = [PentobiInternalPlayer(pid=1, level=6, name="P1"),
           PentobiInternalPlayer(pid=2, level=1, name="P2"),
           PentobiInternalPlayer(pid=3, level=1, name="P3"),
           PentobiInternalPlayer(pid=4, level=1, name="P4")
           ]

game_kwargs = {}

play_game_with_args_and_save_result(players, game_kwargs, verbose=True, timeout=60, result_file="result.blksgf")
    
