import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from GameManual import GameManual
from OrangeAlliance import OrangeAlliance

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents, activity=discord.Game(name="FIRST Tech Challenge", type=5))
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await setup_groups()
    print(f'{client.user} has connected to Discord!')


@app_commands.command()
async def test(interaction: discord.Interaction):
    await interaction.response.send_message('DISCORD.PY IS BACK WOOOOOOOOOOO')


async def setup_groups():
    # await client.http.bulk_upsert_guild_commands(client.application_id, 713863645565550642, [])

    tree.add_command(GameManual(), guild=discord.Object(id=713863645565550642))
    tree.add_command(OrangeAlliance(), guild=discord.Object(id=713863645565550642))
    tree.add_command(test, guild=discord.Object(id=713863645565550642))

    await tree.sync(guild=discord.Object(id=713863645565550642))
    await tree.sync()


client.run(os.getenv('DISCORD_TOKEN'))

