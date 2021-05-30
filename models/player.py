import time
from dataclasses import dataclass
from typing import Union


@dataclass
class Player:
    id = 0
    nickname = "UNKNOWN_PLAYER"
    last_voice: Union[int, None] = None
    num_react = 0
    num_voice = 0
    num_message = 0
    tickets = 0
    boosts = 0

    @classmethod
    def fromBasic(cls, new_id: int, name: str):
        return Player({'nickname': name, 'id': new_id})

    def __init__(self, base_dict: dict):
        self.__dict__.update(base_dict)

    def __str__(self):
        return "Player({0}, {1}, [{2}|{3}|{4}] @ {5})" \
            .format(self.id, self.nickname, self.num_react, self.num_voice, self.num_message, self.last_voice)

    def start_counter(self):
        self.last_voice = int(time.time())

    def stop_counter(self):
        if self.last_voice is None:
            return
        self.num_voice += int(time.time()) - self.last_voice
        self.last_voice = None

    def cycle_counter(self):
        self.stop_counter()
        self.start_counter()

    def weight(self, max_react, max_voice, max_message):
        agg = ((self.num_react / max_react) + (self.num_voice / max_voice) + (self.num_message / max_message)) / 2
        pre = 1 + agg
        boosted = pre * (1 + (0.2 * self.boosts))
        return boosted

    def reset(self):
        self.num_react = 0
        self.num_voice = 0
        self.num_message = 0

