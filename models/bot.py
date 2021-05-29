from discord import Guild, Member, VoiceState, Message

from discord.ext import commands

from models import config
from models.raffle import Raffle


class MyClient(commands.Bot):

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

        self.home: Guild
        self.raffle: Raffle = Raffle()


    async def on_ready(self):
        config.load_data(self.raffle)
        print('Logged on as {0}!'.format(self.user))

        # noinspection PyAttributeOutsideInit
        self.home = self.get_guild(config.config_data["guild"])

        self.raffle.members = self.home.members
        for vc in self.home.voice_channels:
            member: Member
            for member in vc.members:
                print(member.nick)
                self.raffle.get_player(member).start_counter()
                print("Starting counter for {0}".format(self.raffle.get_player(member)))
        self.raffle.sync_games()
        print('Bot should be ready now.')

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if before.channel is None and after.channel is not None:
            self.raffle.get_player(member).start_counter()
            print("VS Enter: {0}".format(member.display_name))
        elif after.channel is None and before.channel is not None:
            self.raffle.get_player(member).stop_counter()
            print("VS Exit: {0}".format(member.display_name))

    async def on_message_delete(self, message: Message):
        player = self.raffle.get_player(message.author)
        player.num_message = max(1, player.num_message + 1)

    async def on_message(self, message: Message):

        if message.author == self.user:
            return

        if message.author.id != config.config_data["owner"]:
            return

        # Increment message counter
        if message.guild == self.home:
            print("{0}: {1}".format(message.author.display_name, message.content))

            self.raffle.get_player(message.author).num_message += 1

        if message.content.startswith('$check'):
            await message.channel.send(self.raffle.get_player(message.author))

        if message.content.startswith('$fin'):
            finals = self.raffle.get_final_players()
            await message.channel.send("## Finalists: ##")
            for finalist in finals:
                final_str = "`Finalist: {0} (wgt: {1})`".format(finalist, self.raffle.get_weight(finalist))
                await message.channel.send(final_str)

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

        if message.content.startswith('$path'):
            print(config.config_data)

        if message.content.startswith('$games'):
            print(self.raffle.games)

        if message.content.startswith('$save'):
            config.save_data(self.raffle)

        if message.content.startswith('$shut'):
            for vc in self.home.voice_channels:
                member: Member
                for member in vc.members:
                    print(member.nick)
                    self.raffle.get_player(member).stop_counter()
                    print("Stopping counter for {0}".format(self.raffle.get_player(member)))

            config.save_data(self.raffle)
            await message.channel.send('Raffalo is shutting down!')
            await self.close()
