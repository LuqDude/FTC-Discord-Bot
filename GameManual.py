import json
from typing import List

import discord
from discord import app_commands
from discord.app_commands import Choice

imgs = {}
img_choices = []

definitions = {}
rules = {}


class GameManual(app_commands.Group):
    def __init__(self):
        super().__init__()
        if len(imgs) == 0:
            GameManual.load_manual()
        print('GameManual loaded')

    @staticmethod
    def load_manual():
        global imgs
        global img_choices
        global definitions
        global rules

        with open('manual/definitions.json', 'r', encoding='utf-8') as jsondef:
            definitions = json.load(jsondef)

        with open('manual/rules.json', 'r', encoding='utf-8') as grules:
            rules = json.load(grules)

        with open("manual/img_index.json", "r", encoding='utf-8') as index:
            imgs = json.load(index)
            img_keys = imgs.keys()

        for key in img_keys:
            img_choices.append(Choice(name=key, value=key))

    @app_commands.command()
    @app_commands.describe(img='The image to grab from the game manual')
    @app_commands.choices(img=img_choices)
    async def img(self, interaction: discord.Interaction, img: Choice[str]):
        index = imgs[img.value]
        if type(index) is dict:
            first = True
            for path in index.values():
                if first:
                    first = False
                    await interaction.response.send_message(file=discord.File(path))
                else:
                    await interaction.channel.send(file=discord.File(path))
        else:
            await interaction.response.send_message(file=discord.File(index))

    @app_commands.command()
    async def link(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            'Traditional: https://firstinspiresst01.blob.core.windows.net/first-forward-ftc/game-manual-part-2'
            '-traditional.pdf')
        await interaction.channel.send('Remote: https://firstinspiresst01.blob.core.windows.net/first-forward-ftc'
                                       '/game-manual-part-2-remote.pdf')

    @app_commands.command()
    @app_commands.describe(term='The definition to grab from the game manual')
    async def define(self, interaction: discord.Interaction, term: str):
        if term in definitions:
            await interaction.response.send_message(f'**{term}**: {definitions[term]}')
        else:
            await interaction.response.send_message('No definition found for ' + term)
            await interaction.channel.send(f'The list of terms are: {", ".join(definitions.keys())}')

    @define.autocomplete('term')
    async def define_autocomplete(self, interaction: discord.Interaction, current: str,
                                  namespace: app_commands.Namespace) -> List[app_commands.Choice[str]]:
        auto = [Choice(name=term, value=term) for term in definitions.keys() if current.lower() in term.lower()]
        if len(auto) > 25:
            auto = auto[:25]
        return auto

    @app_commands.command()
    @app_commands.describe(rule='The rule to grab from the game manual')
    async def rule(self, interaction: discord.Interaction, rule: str):
        if rule in rules:
            await interaction.response.send_message(f'**{rule}**: {rules[rule]}')
        else:
            await interaction.response.send_message(f'Rule {rule} not found')
            await interaction.channel.send(f'The list of rules are: {", ".join(rules.keys())}')

    @rule.autocomplete('rule')
    async def define_autocomplete(self, interaction: discord.Interaction, current: str,
                                  namespace: app_commands.Namespace) -> List[app_commands.Choice[str]]:
        auto = [Choice(name=term, value=term) for term in rules.keys() if current.lower() in term.lower()]
        if len(auto) > 25:
            auto = auto[:25]
        return auto
