import asyncio

import discord
import json

from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

from models.bot import MyClient
from models.config import config_data
from models.player import Player

client = MyClient(command_prefix="!", intents=discord.Intents.all())

slash = SlashCommand(client, sync_commands=False)


@slash.slash(name="ping",
             guild_ids=[config_data['guild']],
             description="Pings Raffalo."
             )
async def _ping(ctx: SlashContext):
    res = await ctx.send("doot!")
    await res.add_reaction('\N{TABLE TENNIS PADDLE AND BALL}')
    await asyncio.sleep(1)
    await res.clear_reactions()


@slash.slash(name="fetch",
             guild_ids=[config_data['guild']],
             description="Fetches Stuff.")
async def _fetch(ctx: SlashContext):
    print("Hello!")
    client.raffle.sync_games()


client.run(config_data['bot_token'])
