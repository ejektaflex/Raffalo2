import json
import os
from json import JSONEncoder
from typing import List

from models.player import Player
from models.raffle import Raffle


class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


os.chdir('data')
print(os.listdir())

config_data = json.load(open('config.json'))

saved: dict


def save_data(raffle: Raffle):
    info = {'players': raffle.players}
    with open('save.json', 'w+') as save_file:
        json.dump(info, save_file, indent=4, cls=MyEncoder)
    save_file.close()


def load_data(raffle: Raffle):
    with open('save.json', 'r') as load_file:
        # Player loading
        new_players: List[Player] = []
        loaded = json.load(load_file)
        players = list(loaded['players'].values())
        for player in players:
            created = Player(player)
            print("appending player ${0}!".format(created))
            new_players.append(created)
        raffle.players.clear()
        for player in new_players:
            raffle.players[player.id] = player
