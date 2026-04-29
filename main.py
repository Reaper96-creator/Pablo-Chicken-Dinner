import discord
from discord.ext import tasks
import requests
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUBG_API_KEY = os.getenv("PUBG_API_KEY")

CHANNEL_ID = 1497295033169219724

PLAYERS = ["xXx_ZibeX_PL_xXx","Aserocik","xxXx_Reaper_xXxx","gosiaa_95","Czajurka","iamwojteak","Szaki_71","BOBER_POS","Stiven01_","Dariusz_-_","ACEMUNDPL","AvangardoPoland","BabciazZusu","fedek1","DarekCSW","Hangman1990","Hangman90","hogis320","karolr92","karpiu223","kejku","Konrad_Ak47","LowcaBobrow","lucek-23","Mannia1991","Misiaczek89","Radeusz","Rodriguez_Lopez","SEBIX777","SIWYDYM91_","StaryKefir","SuperLosiek","Witruoz","Zablakany69"]

CHECK_INTERVAL = 120

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

client = discord.Client(intents=discord.Intents.default())
checked_matches = set()

MAPS = {
    "Baltic_Main": "Erangel",
    "Desert_Main": "Miramar",
    "Savage_Main": "Sanhok",
    "DihorOtok_Main": "Vikendi",
    "Tiger_Main": "Taego",
    "Heaven_Main": "Paramo",
    "Kiki_Main": "Deston"
}

# 🔥 NOWE – wykrywanie platformy
def get_player(name):
    for shard in ["steam", "console"]:
        url = f"https://api.pubg.com/shards/{shard}/players?filter[playerNames]={name}"
        r = requests.get(url, headers=HEADERS)

        if r.status_code == 200:
            data = r.json()["data"]
            if data:
                print(f"✅ {name} -> {shard}")
                return data[0], shard

    print(f"❌ NIE ZNALEZIONO: {name}")
    return None, None


def get_match(match_id, shard):
    url = f"https://api.pubg.com/shards/{shard}/matches/{match_id}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("BŁĄD API MATCH:", r.text)
        return None

    return r.json()


def parse_team(match_data, player_name):
    included = match_data["included"]

    player_id = None

    for i in included:
        if i["type"] == "participant":
            if i["attributes"]["stats"]["name"].lower() == player_name.lower():
                player_id = i["id"]

    if not player_id:
        print("NIE ZNALEZIONO ID:", player_name)
        return None, []

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
                            "damage": int(s["damageDealt"]),
                            "headshots": s.get("headshotKills", 0),
                            "longest_kill": round(s.get("longestKill", 0), 1),
                            "revives": s.get("revives", 0)
                        })

                return rank, team

    return None, []


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_matches():
    print("🔍 SPRAWDZAM MECZE...")

    for player in PLAYERS:
        try:
            print("➡️ GRACZ:", player)

            p, shard = get_player(player)
            if not p:
                continue

            matches = p["relationships"]["matches"]["data"][:5]

            print("📦 MECZE:", len(matches))

            for m in matches:
                match_id = m["id"]

                if match_id in checked_matches:
                    continue

                match_data = get_match(match_id, shard)
                if not match_data:
                    continue

                map_name = match_data["data"]["attributes"]["mapName"]
                game_mode = match_data["data"]["attributes"]["gameMode"]

                map_name = MAPS.get(map_name, map_name)

                rank, team = parse_team(match_data, player)

                if rank == 1:
                    print("🏆 WIN!")

                    checked_matches.add(match_id)

                    channel = client.get_channel(CHANNEL_ID)
                    if not channel:
                        print("❌ BRAK KANAŁU")
                        return

                    team.sort(key=lambda x: x["damage"], reverse=True)

                    total_kills = sum(p["kills"] for p in team)
                    max_kill = max(p["longest_kill"] for p in team)

                    embed = discord.Embed(
                        title="🏆 WINNER WINNER CHICKEN DINNER!",
                        description=f"🔥 {player} i drużyna wygrali!",
                        color=0xf1c40f
                    )

                    embed.add_field(name="🗺️ Mapa", value=map_name, inline=True)
                    embed.add_field(name="🎮 Tryb", value=game_mode, inline=True)

                    embed.add_field(
                        name="📊 Drużyna",
                        value=f"🔪 Kille: {total_kills}",
                        inline=False
                    )

                    embed.add_field(
                        name="🎯 Najdalszy kill",
                        value=f"{max_kill} m",
                        inline=False
                    )

                    for i, p in enumerate(team):
                        tag = "🔥 MVP" if i == 0 else ""

                        embed.add_field(
                            name=f"{p['name']} {tag}",
                            value=f"K:{p['kills']} | A:{p['assists']} | HS:{p['headshots']} | REV:{p['revives']} | DMG:{p['damage']} | 🎯 {p['longest_kill']}m",
                            inline=False
                        )

                    await channel.send(embed=embed)

        except Exception as e:
            print("❌ ERROR:", e)


@client.event
async def on_ready():
    print(f"✅ BOT: {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send("✅ BOT DZIAŁA")
    else:
        print("❌ BRAK KANAŁU")

    check_matches.start()


client.run(DISCORD_TOKEN)
