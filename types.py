# type: ignore
from dataclasses import dataclass
from enum import Enum

class SongStatus(Enum):
    APP: "APP"
    AP: "AP"
    FC: "FC"
    NONE: "NONE"

class SongDifficulty(Enum):
    I: "I"
    II: "II"
    III: "III"
    IV: "IV"
    IV_Alpha: "IV_Alpha"
    Meow: "Meow"
    E: "E"
    What: "??"

@dataclass
class Song:
    id: str
    title: str
    score: int
    rating: float
    _rating: float = None
    status: SongStatus
    nextPointScore: int
    isCleared: bool
    level: float
    difficulty: SongDifficulty

@dataclass
class Player:
    rating: float
    name: str
    avatarID: str
    backgroundID: str
    characterID: str
    OTHER = None
