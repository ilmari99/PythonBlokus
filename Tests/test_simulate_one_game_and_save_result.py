import time
from BlokusPentobi.PentobiPlayers import PentobiInternalPlayer
from BlokusPentobi.simulate import play_game_with_args_and_save_result

players = [PentobiInternalPlayer(pid=1, level=6, name="P1"),
           PentobiInternalPlayer(pid=2, level=1, name="P2"),
           PentobiInternalPlayer(pid=3, level=1, name="P3"),
           PentobiInternalPlayer(pid=4, level=1, name="P4")
           ]

game_kwargs_list = [{},
                    {"level":5},
                    {"threads":4, "level":5},
                    {"nobook":True, "noresign":False},
]
times_taken = []
for i, game_kwargs in enumerate(game_kwargs_list):
    start_t = time.time()
    play_game_with_args_and_save_result(players, game_kwargs, verbose=False, timeout=60, result_file="test.blksgf")
    end_t = time.time()
    times_taken.append(end_t - start_t)
    print(f"Game {i} took {end_t - start_t} seconds")

print(f"Times taken: {times_taken}")
