from . import types
from typing import Tuple, List

def getSave(userData: dict) -> Tuple[List[types.Song], types.Player]:
    # Do someththing with userData ...
    songs = [types.Song() for _ in range(10)]
    player = types.Player()
    return songs, player
