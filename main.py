import discord
from discord.ext import tasks
import requests
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUBG_API_KEY = os.getenv("PUBG_API_KEY")
CHANNEL_ID = 123456789012345678

PLAYERS = ["xxXx_Reaper_xXxx","gosiaa_95","Czajurka","iamwojteak","Szaki_71","TikTok--RoMi","BOBER_POS","Stiven01_","Dariusz_-_"]

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

checked_matches = set()

def get_player(name):
    url = f"https://api.pubg.com/shards/steam/players?filter[playerNames]={name}"
    return requests.get(url, headers=HEADERS).json()["data"][0]

def get_match(match_id):
    url = f"https://api.pubg.com/shards/steam/matches/{match_id}"
    return requests.get(url, headers=HEADERS).json()

def parse_team(match_data, player_name):
    included = match_data["included"]
    player_id = None

    for i in included:
        if i["type"] == "participant":
            if i["attributes"]["stats"]["name"].lower() == player_name.lower():
                player_id = i["id"]

    for i in included:
        if i["type"] == "roster":
            participants = [p["id"] for p in i["relationships"]["participants"]["data"]]
            if player_id in participants:
                rank = i["attributes"]["stats"]["rank"]
                team = []

                for p in included:
                    if p["type"] == "participant" and p["id"] in participants:
                        s = p["attributes"]["stats"]
                        team.append({
                            "name": s["name"],
                            "kills": s["kills"],
                            "assists": s["assists"],
                            "damage": int(s["damageDealt"])
                        })

                return rank, team

    return None, []

@tasks.loop(minutes=2)
async def check():
    for player in PLAYERS:
        try:
            p = get_player(player)
            match_id = p["relationships"]["matches"]["data"][0]["id"]

            if match_id in checked_matches:
                continue

            match_data = get_match(match_id)
            rank, team = parse_team(match_data, player)

            if rank == 1:
                checked_matches.add(match_id)
                channel = client.get_channel(CHANNEL_ID)

                embed = discord.Embed(
                    title="🏆 CHICKEN DINNER!",
                    color=0xf1c40f
                )

                for p in team:
                    embed.add_field(
                        name=p["name"],
                        value=f"Kille: {p['kills']} | DMG: {p['damage']}",
                        inline=False
                    )

                await channel.send(embed=embed)

        except Exception as e:
            print(e)

@client.event
async def on_ready():
    print("Bot działa")
    check.start()

client.run(DISCORD_TOKEN)
