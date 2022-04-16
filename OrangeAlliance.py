import os
from typing import Optional

import aiohttp
import discord.app_commands
import requests
from discord import app_commands
from discord.app_commands import Choice
from dotenv import load_dotenv

load_dotenv()
TOA_API_KEY = os.getenv("ORANGE_ALLIANCE_TOKEN")
headers = {
    'X-TOA-KEY': TOA_API_KEY,
    'X-Application-Origin': 'Spatula Bot',
    'Content-Type': 'application/json'
}
URL = 'https://theorangealliance.org/api'

seasons = {}
season_choices = []
teams = []


class OrangeAlliance(app_commands.Group):

    def __init__(self):
        global seasons
        global season_choices
        super().__init__()

        self.get_seasons()

    def get_seasons(self):
        global seasons

        response = requests.get(URL + '/seasons', headers=headers)
        seasons = response.json()

        for season in seasons:
            season_choices.append(discord.app_commands.Choice(value=season['season_key'], name=season['description']))

    @app_commands.command()
    @app_commands.describe(num='The team number to get information for')
    @app_commands.choices(season=season_choices)
    @app_commands.describe(season='The season to get information for')
    async def team(self, interaction: discord.Interaction, num: int, season: Optional[Choice[str]]):
        await interaction.response.defer()
        season = season or None
        if season is not None:
            await self.toa_season(interaction, num, season.name, season.value)
            return

        url = f'https://theorangealliance.org/teams/{num}'
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False, force_close=True)) as cs:
            async with cs.get(f'{URL}/team/{num}', headers=headers) as r:
                res = (await r.json())
                res = res[0]
                name = res['team_name_short']
                yr = res['rookie_year']
                loc = f"{res['city']},{res['state_prov']},{res['country']}"
                last = res['last_active']
                last = f'20{last[0:2]}-20{last[2:4]}'
            async with cs.get(f'{URL}/team/{num}/wlt', headers=headers) as r:
                res = await r.json()
                res = res[0]
                wlt = f"{res['wins']}-{res['losses']}-{res['ties']}"

        embed = discord.Embed(title=f'Team {num} - {name}', url=url)
        embed.add_field(name='Rookie Year', value=yr, inline=True)
        embed.add_field(name='Location', value=loc, inline=True)
        embed.add_field(name='Last Season', value=last, inline=True)
        embed.add_field(name='W-L-T', value=wlt, inline=True)

        await interaction.followup.send(embed=embed)

    async def toa_season(self, interaction: discord.Interaction, num: int, season_name: str, season_key: str):
        pOPR = -1
        OPR = -1
        totalWin = 0
        totalLoss = 0
        totalTie = 0
        url = f'https://theorangealliance.org/teams/{num}'
        matches = []

        print(season_key)
        # get OPR and events
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False, force_close=True)) as cs:
            async with cs.get(f'{URL}/team/{num}/results/{season_key}', headers=headers) as r:
                events = await r.json()
                # print(events)
                name = events[0]['team']['team_name_short']
                for event in events:
                    pOPR = max(int(event['opr']), pOPR)
                    OPR = max(int(event['np_opr']), OPR)
                print('opr done')
                events = []

            # get events
            async with cs.get(f'{URL}/team/{num}/events/{season_key}', headers=headers) as r:
                event_json = await r.json()
                for event in event_json:
                    # print(event)
                    events.append(event['event_key'])
                print('events done')
            #
            # for event in events:
            #     print(event)

            # get matches and team
            for event in events:
                async with cs.get(f'{URL}/event/{event}/matches', headers=headers, params={'type': 'elims'}) as r:
                    all_matches = await r.json()
                    for match in all_matches:
                        # print(match)
                        # print('im abt to crash lol')
                        for participant in match['participants']:
                            print(participant)
                            if participant['team_key'] == str(num):
                                team = participant['match_participant_key']
                                team = team[len(team) - 2:len(team) - 1]
                                matches.append(match)

            unsorted = ''
            # get awards
            async with cs.get(f'{URL}/team/{num}/awards/{season_key}', headers=headers) as r:
                awards = await r.json()
                for award in awards:
                    # print(award)
                    unsorted += award['award_name'] + '\n'

        # calc
        for match in matches:
            for participant in match['participants']:
                if participant['team_key'] == str(num):
                    team = participant['match_participant_key']
                    team = team[len(team) - 2:len(team) - 1]

            red = int(match['red_score'])
            blue = int(match['blue_score'])
            if team == 'B':
                if blue > red:
                    totalWin += 1
                elif blue < red:
                    totalLoss += 1
                else:
                    totalTie += 1
            else:
                if red > blue:
                    totalWin += 1
                elif red < blue:
                    totalLoss += 1
                else:
                    totalTie += 1

        embed = discord.Embed(title=f'Team {num} - {name}', description=f'{season_name}', url=url)
        embed.add_field(name='W-L-T', value=f'{totalWin}-{totalLoss}-{totalTie}', inline=True)
        embed.add_field(name='OPR (No Penalty)', value=OPR, inline=True)
        embed.add_field(name='OPR (Penalty)', value=pOPR, inline=True)
        embed.add_field(name='Awards', value=unsorted, inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(description='Get the world record for a season')
    @app_commands.choices(season=season_choices)
    @app_commands.describe(season='The season to get the world record for. Defaults to current season.')
    async def wr(self, interaction: discord.Interaction, season: Optional[Choice[str]]):
        await interaction.response.defer()
        season = season or season_choices[len(seasons) - 1]

        # get season
        season_name = season.name
        season_key = season.value
        params = {
            'type': 'all',
            'season_key': season_key,
            'penalty': 'false'
        }

        teams = ''
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True, ssl=False)) as cs:
            async with cs.get(f'{URL}/match/high-scores', headers=headers, params=params) as s:
                r = (await s.json())[0]
                red = int(r['red_score'])
                blue = int(r['blue_score'])
                color = 'R'
                if blue > red:
                    color = 'B'
                key = r['match_key']
                score = max(red, blue)

            url = f'https://theorangealliance.org/matches/{key}'

            async with cs.get(f'{URL}/match/{key}', headers=headers) as s:
                r = (await s.json())[0]
                name = r['match_name']
                participants = r['participants']
                for participant in participants:
                    part_key = participant['match_participant_key']
                    if part_key[len(part_key) - 2:len(part_key) - 1] == color:
                        teams += participant['team']['team_key'] + '\n'
                key = r['event_key']

            async with cs.get(f'{URL}/event/{key}',
                              headers=headers) as s:
                r = (await s.json(content_type=None))[0]
                name = r['event_name'] + ' ' + name

        embed = discord.Embed(title=f'{season_name} World Record', url=url, description=name)
        embed.add_field(name='Score', value=score, inline=True)
        embed.add_field(name='Teams', value=teams, inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command()
    @app_commands.describe(name='The team name to search for')
    async def search(self, interaction: discord.Interaction, name: str):
        global teams
        await interaction.response.defer()
        results = []
        if not bool(teams):
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True, ssl=False)) as cs:
                async with cs.get(f'{URL}/team', headers=headers) as s:
                    r = (await s.json())
                    teams = r

        for team in teams:
            if name.lower() in str(team['team_name_short']).lower():
                results.append(team)

        if bool(results):
            embed = discord.Embed(title=f'Search Results {min(10, len(results))}/{len(results)}',
                                  description=f'{name} could refer to:')
            for result in results[:10]:
                embed.add_field(name=f'{result["team_key"]} - {result["team_name_short"]}', value='​', inline=False)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f'Could not find a team by the name {name}')
