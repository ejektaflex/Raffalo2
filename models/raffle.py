import json
import os
import random
from json import JSONEncoder
from typing import List, Dict

import requests
from discord import Member

from models.game import Game
from models.player import Player

os.chdir('data')
print(os.listdir())


class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class Raffle:

    def __init__(self):
        self.config_data = json.load(open('config.json'))
        self.members: List[Member] = []
        self.players: Dict[int, Player] = {}
        self.games: List[Game] = []

    def get_player(self, member: Member) -> Player:
        return self.players.setdefault(
            member.id,
            Player.fromBasic(member.id, member.display_name)
        )

    def sync_games(self):
        res = requests.get(
            "https://api.airtable.com/v0/{0}/Games?view=Grid%20view".format(self.config_data['airtable_table_key']),
            headers={"Authorization": "Bearer {0}".format(self.config_data['airtable_user_key'])}
            )
        response_dict = json.loads(res.content)["records"]
        print(response_dict)
        self.games.clear()
        for item in response_dict:
            new_game = Game()
            new_game.id = item["id"]
            fields = item["fields"]
            new_game.name = fields["Game Name"]
            new_game.is_mystery = fields.get("Is Mystery?", False)
            new_game.keys = [key_part.strip() for key_part in fields["Humble Gift Keys"].split('\n')]
            new_game.picked = fields.get("Picked", False)
            new_game.text = fields.get("Raffle Text", None)
            new_game.steam_id = fields.get("SteamId", None)
            print(new_game.name)
            self.games.append(new_game)

    def is_finalist(self, member: Member) -> bool:
        fin_player = self.get_player(member)
        return not member.bot and (fin_player.num_voice != 0 or fin_player.num_react != 0 or fin_player.num_message != 0)

    def get_finalists(self) -> List[Member]:
        ret = []
        for fin in self.members:
            if fin.voice is not None:
                print("Cycling {0}".format(fin.display_name))
                self.get_player(fin).cycle_counter()  # update voice
            if self.is_finalist(fin):
                ret.append(fin)
        return ret

    def get_final_players(self) -> List[Player]:
        return [self.get_player(fin) for fin in self.get_finalists()]

    def get_maxes(self, pop: List[Member]):
        max_react = max(1, max(self.get_player(fin).num_react for fin in pop))
        max_voice = max(1, max(self.get_player(fin).num_voice for fin in pop))
        max_message = max(1, max(self.get_player(fin).num_message for fin in pop))
        return [max_react, max_voice, max_message]

    def get_weight(self, player: Player):
        pop = self.get_finalists()
        maxes = self.get_maxes(pop)
        return player.weight(maxes[0], maxes[1], maxes[2])

    def choose_finalist(self) -> Member:
        pop = self.get_finalists()
        maxes = self.get_maxes(pop)

        return random.choices(
            population=pop,
            weights=[self.get_player(fin).weight(maxes[0], maxes[1], maxes[2]) for fin in pop],
            k=1
        )[0]

    def save_data(self):
        info = {'players': self.players}
        with open('save.json', 'w+') as save_file:
            json.dump(info, save_file, indent=4, cls=MyEncoder)
        save_file.close()

    def load_data(self):
        with open('save.json', 'r') as load_file:
            # Player loading
            new_players: List[Player] = []
            loaded = json.load(load_file)
            players = list(loaded['players'].values())
            for player in players:
                created = Player(player)
                print("appending player ${0}!".format(created))
                new_players.append(created)
            self.players.clear()
            for player in new_players:
                self.players[player.id] = player
