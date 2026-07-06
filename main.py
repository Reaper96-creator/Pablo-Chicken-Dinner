import discord
from discord.ext import tasks
import requests
import os
import time

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUBG_API_KEY = os.getenv("PUBG_API_KEY")

CHANNEL_ID = 1497295033169219724

PLAYERS = [
    "Zardion","Foecee","Aserocik","xxXx_Reaper_xXxx","gosiaa_95",
    "Czajurka","iamwojteak","Szaki_71","BOBER_POS","Stiven01_",
    "Dariusz_-_","ACEMUNDPL","AvangardoPoland","BabciazZusu",
    "fedek1","DarekCSW","Hangman1990","Hangman90","hogis320",
    "karolr92","karpiu223","kejku","Konrad_Ak47","LowcaBobrow",
    "lucek-23","Mannia1991","Misiaczek89","Radeusz",
    "Rodriguez_Lopez","SEBIX777","SIWYDYM91_","StaryKefir",
    "SuperLosiek","Zablakany69","Mader81","Fabo84PL"
]

CHECK_INTERVAL = 120

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

client = discord.Client(intents=discord.Intents.default())

checked_matches = set()
player_shards = {}

MAPS = {
    "Baltic_Main": "Erangel",
    "Desert_Main": "Miramar",
    "Savage_Main": "Sanhok",
    "DihorOtok_Main": "Vikendi",
    "Tiger_Main": "Taego",
    "Heaven_Main": "Paramo",
    "Kiki_Main": "Deston",
    "Neon_Main": "Rondo"
}

# =========================
# REQUEST
# =========================

def safe_request(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)

            if r.status_code == 429:
                print("⏳ RATE LIMIT...")
                time.sleep(5)
                continue

            return r

        except Exception as e:
            print("REQUEST ERROR:", e)
            time.sleep(2)

    return None

# =========================
# PLAYER
# =========================

def get_player(name):

    if name in player_shards:
        shard = player_shards[name]

        url = f"https://api.pubg.com/shards/{shard}/players?filter[playerNames]={name}"
        r = safe_request(url)

        if r and r.status_code == 200:
            data = r.json()["data"]

            if data:
                return data[0], shard

    for shard in ["steam", "console", "kakao"]:

        url = f"https://api.pubg.com/shards/{shard}/players?filter[playerNames]={name}"

        r = safe_request(url)

        if not r:
            continue

        if r.status_code == 200:

            data = r.json()["data"]

            if data:
                player_shards[name] = shard
                print(f"✅ {name} -> {shard}")
                return data[0], shard

    print("❌ NIE ZNALEZIONO:", name)
    return None, None

# =========================
# MATCH
# =========================

def get_match(match_id, shard):

    url = f"https://api.pubg.com/shards/{shard}/matches/{match_id}"

    r = safe_request(url)

    if r and r.status_code == 200:
        return r.json()

    return None

# =========================
# TEAM
# =========================

def parse_team(match_data, player_name):

    included = match_data["included"]

    player_id = None

    for i in included:

        if i["type"] == "participant":

            if i["attributes"]["stats"]["name"].lower() == player_name.lower():

                player_id = i["id"]

    if not player_id:
        return None, []

    for i in included:

        if i["type"] == "roster":

            participants = [
                p["id"]
                for p in i["relationships"]["participants"]["data"]
            ]

            if player_id in participants:

                rank = i["attributes"]["stats"]["rank"]

                team = []

                for p in included:

                    if (
                        p["type"] == "participant"
                        and p["id"] in participants
                    ):

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

# =========================
# CHECK MATCHES
# =========================

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_matches():

    print("🔍 SPRAWDZAM MECZE...")

    for player in PLAYERS:

        try:

            print("➡️", player)

            p, shard = get_player(player)

            if not p:
                continue

            matches = p["relationships"]["matches"]["data"][:10]

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

                    checked_matches.add(match_id)

                    print("🏆 WIN:", player)

                    channel = client.get_channel(CHANNEL_ID)

                    if not channel:
                        continue

                    team.sort(
                        key=lambda x: x["damage"],
                        reverse=True
                    )

                    total_kills = sum(p["kills"] for p in team)

                    max_kill = max(
                        p["longest_kill"]
                        for p in team
                    )

                    embed = discord.Embed(
                        title="🏆 WINNER WINNER CHICKEN DINNER!",
                        description=f"🔥 Drużyna gracza {player} wygrała mecz!",
                        color=0xf1c40f
                    )

                    embed.add_field(
                        name="🗺️ Mapa",
                        value=map_name,
                        inline=True
                    )

                    embed.add_field(
                        name="🎮 Tryb",
                        value=game_mode,
                        inline=True
                    )

                    embed.add_field(
                        name="📊 Statystyki drużyny",
                        value=f"🔪 Kille: {total_kills}",
                        inline=False
                    )

                    embed.add_field(
                        name="🎯 Najdalsze zabójstwo",
                        value=f"{max_kill} m",
                        inline=False
                    )

                    for i, p in enumerate(team):

                        tag = "🔥 MVP" if i == 0 else ""

                        embed.add_field(
                            name=f"{p['name']} {tag}",
                            value=(
                                f"K: {p['kills']} | "
                                f"A: {p['assists']} | "
                                f"HS: {p['headshots']} | "
                                f"REV: {p['revives']} | "
                                f"DMG: {p['damage']} | "
                                f"🎯 {p['longest_kill']}m"
                            ),
                            inline=False
                        )

                    await channel.send(embed=embed)

                    await discord.utils.sleep_until(
                        discord.utils.utcnow()
                    )

        except Exception as e:

            print("❌ ERROR:", e)

# =========================
# READY
# =========================

@client.event
async def on_ready():

    print(f"✅ BOT ZALOGOWANY JAKO {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send("✅ BOT DZIAŁA I JEST ONLINE")

    check_matches.start()

client.run(DISCORD_TOKEN)
