import json
import os
import random
import time
from json import JSONEncoder
from typing import List, Dict, Union

import requests
from discord import Member, TextChannel, DMChannel, Message
from discord.abc import Messageable
from discord.ext.commands import Bot

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
        self.game: Union[Game, None] = None

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
            new_game = Game({})
            new_game.id = item["id"]
            fields = item["fields"]
            new_game.name = fields["Game Name"]
            new_game.is_mystery = fields.get("Is Mystery?", False)
            new_game.keys = [key_part.strip() for key_part in fields["Humble Gift Keys"].split('\n')]
            new_game.picked = fields.get("Picked", False)
            new_game.text = fields.get("Raffle Text", None)
            new_game.steam_id = fields.get("SteamId", None)
            new_game.submitters = fields.get("Discord Ids", None)
            # print(new_game.name)
            self.games.append(new_game)

    def is_finalist(self, member: Member) -> bool:
        fin_player = self.get_player(member)
        return not member.bot and (
                fin_player.num_voice != 0 or fin_player.num_react != 0 or fin_player.num_message != 0)

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

    def choose_finalist(self, finalists: List[Member]) -> Member:
        pop = finalists
        maxes = self.get_maxes(pop)

        return random.choices(
            population=pop,
            weights=[self.get_player(fin).weight(maxes[0], maxes[1], maxes[2]) for fin in pop],
            k=1
        )[0]

    def reset_players(self):
        for player in self.players.values():
            player.reset()

    def save_backup(self):
        self.save_data("{0}.json".format(time.time()))  # backup

    # Interaction

    async def start(self, frm: Messageable, days: int):
        msg = ""
        pickable_games = [game for game in self.games if not game.picked]

        if len(pickable_games) == 0:
            await frm.send("There are no unpicked games to raffle off!!")
            return

        picked = pickable_games[0]

        self.game = picked

        self.save_backup()
        self.reset_players()

        msg += "Hello! Welcome to today's raffle! It will last for: {0} day(s).".format(days)

        if picked.is_mystery:
            msg += "\nThis raffle is a mystery!"

            if picked.text.strip() != "":
                msg += " The raffle hint is:"
                msg += "\n\n`{0}`".format(picked.text)
        else:
            msg += "\nThis week's raffle is a known game! The game is named:\n\n`{0}`".format(picked.name)
            msg += "\n\nhttps://store.steampowered.com/app/{0}/".format(picked.steam_id)

        msg += "\n\nThe more you interact with our server, the better your odds!"

        sent = await frm.send(msg)
        pins: List[Message] = await sent.channel.pins()

        for pin in pins:
            await pin.unpin()

        await sent.pin()

    async def end(self, frm: Messageable):
        finalists = self.get_finalists()
        self.save_backup()

        if self.game is None:
            await frm.send("There is no raffle to end!")
            return

        if len(finalists) == 0:
            await frm.send("No finalists have participated!")
            return

        # TODO Role Pinging for new raffles
        # await frm.send("Hello to <@{0}>!".format(self.config_data["roleToPing"]))

        msg = "The raffle has ended!"
        msg += "\nThe possible winners are: {0}".format(", ".join([fin.display_name for fin in finalists]))
        msg += "\nThe winner has been chosen, and it turns out to be:"

        winner = self.choose_finalist(finalists)

        msg += "\n\n`{0}`!".format(winner.display_name)
        msg += "\nCongrats!"

        if self.game.is_mystery:
            msg += "\nYou won this game: \n\n\nhttps://store.steampowered.com/app/{0}/".format(self.game.steam_id)

        if len(self.game.keys) == 0:
            "\n\nAsk {0} for your prize!".format(" or ".join(["<@{0}>".format(sub) for sub in self.game.submitters]))
        else:
            "\n\nThe prize will be sent to you via a DM!"

        self.game = None

        await frm.send(msg)

    # Data loading

    def save_data(self, location: str = 'save.json'):
        info = {'players': self.players, 'game': self.game}
        with open(location, 'w+') as save_file:
            json.dump(info, save_file, indent=4, cls=MyEncoder)
        save_file.close()

    def load_data(self):
        with open('save.json', 'r') as load_file:
            new_players: List[Player] = []
            loaded = json.load(load_file)

            # Player loading
            players = list(loaded['players'].values())
            for player in players:
                created = Player(player)
                print("appending player ${0}!".format(created))
                new_players.append(created)
            self.players.clear()
            for player in new_players:
                self.players[player.id] = player

            # Game loading

            if "game" in loaded and loaded['game'] is not None:
                new_game = loaded['game']
                created_game = Game(new_game)
                print('Loading file game to current game')
                self.game = created_game
                print('Current game is now: {0}'.format(self.game.name))
