import discord
from discord.ext import tasks
import requests
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUBG_API_KEY = os.getenv("PUBG_API_KEY")
CHANNEL_ID = 1497295033169219724

PLAYERS = ["xxXx_Reaper_xXxx","gosiaa_95","Czajurka","iamwojteak","Szaki_71","TikTok--RoMi","BOBER_POS","Stiven01_","Dariusz_-_"]

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

client = discord.Client(intents=discord.Intents.default())

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
async def check_matches():
    for player in PLAYERS:
        try:
            p = get_player(player)

            # 🔥 POBIERAMY 5 OSTATNICH MECZÓW
            matches = p["relationships"]["matches"]["data"][:5]

            for m in matches:
                match_id = m["id"]

                if match_id in checked_matches:
                    continue

                match_data = get_match(match_id)
                rank, team = parse_team(match_data, player)

                if True:
                    checked_matches.add(match_id)

                    channel = client.get_channel(CHANNEL_ID)

                    # sortowanie MVP
                    team.sort(key=lambda x: x["damage"], reverse=True)

                    embed = discord.Embed(
                        title="🏆 WINNER WINNER CHICKEN DINNER!",
                        description=f"🔥 Wygrana drużyny ({player})",
                        color=0xf1c40f
                    )

                    total_kills = sum(p["kills"] for p in team)

                    embed.add_field(
                        name="📊 Team stats",
                        value=f"🔪 Total kills: {total_kills}",
                        inline=False
                    )

                    for i, p in enumerate(team):
                        tag = "🔥 MVP" if i == 0 else ""

                        embed.add_field(
                            name=f"{p['name']} {tag}",
                            value=f"K: {p['kills']} | A: {p['assists']} | DMG: {p['damage']}",
                            inline=False
                        )

                    await channel.send(embed=embed)

        except Exception as e:
            print("ERROR:", e)


@client.event
async def on_ready():
    print("BOT DZIAŁA")
    check_matches.start()


client.run(DISCORD_TOKEN)
