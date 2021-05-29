from typing import List


class Game:
    id: str = "UNKNOWN_GAME_ID"
    name: str = "UNKNOWN_GAME_NAME"
    is_mystery: bool = False
    keys: List[str]
    picked: bool = False
    text: str = "UNKNOWN_GAME_TEXT"
    steam_id: int = 0
