import asyncio

import discord
from discord_slash import SlashCommand, SlashContext

from models.bot import MyClient

client = MyClient(command_prefix="!", intents=discord.Intents.all())

slash = SlashCommand(client, sync_commands=False)


@slash.slash(name="ping",
             guild_ids=[client.raffle.config_data['guild']],
             description="Pings Raffalo."
             )
async def _ping(ctx: SlashContext):
    res = await ctx.send("doot!")
    await res.add_reaction('\N{TABLE TENNIS PADDLE AND BALL}')
    await asyncio.sleep(1)
    await res.clear_reactions()


@slash.slash(name="fetch",
             guild_ids=[client.raffle.config_data['guild']],
             description="Fetches Stuff.")
async def _fetch(ctx: SlashContext):
    print("Hello!")
    client.raffle.sync_games()


client.run(client.raffle.config_data['bot_token'])
