import discord
from discord.ext import tasks
from discord import app_commands
import requests
import os
import asyncio
import json
from datetime import datetime

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUBG_API_KEY = os.getenv("PUBG_API_KEY")

CHANNEL_ID = 1497295033169219724
MVP_ROLE_ID = 123456789012345678  # 🔥 WSTAW ID ROLI MVP

PLAYERS = ["xXx_ZibeX_PL_xXx","Aserocik","xxXx_Reaper_xXxx","gosiaa_95","Czajurka","iamwojteak","Szaki_71","BOBER_POS","Stiven01_","Dariusz_-_","ACEMUNDPL","AvangardoPoland","BabciazZusu","fedek1","DarekCSW","Hangman1990","Hangman90","hogis320","karolr92","karpiu223","kejku","Konrad_Ak47","LowcaBobrow","lucek-23","Mannia1991","Misiaczek89","Radeusz","Rodriguez_Lopez","SEBIX777","SIWYDYM91_","StaryKefir","SuperLosiek","Witruoz","Zablakany69"]

CHECK_INTERVAL = 300

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =========================
# 📂 PLIKI AUTO
# =========================

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

last_matches = load_json("matches.json")
player_stats = load_json("stats.json")

def get_week():
    return datetime.utcnow().strftime("%Y-%U")

# =========================
# 🔎 API
# =========================

def get_player(name):
    for shard in ["steam", "console"]:
        try:
            url = f"https://api.pubg.com/shards/{shard}/players?filter[playerNames]={name}"
            r = requests.get(url, headers=HEADERS)

            if r.status_code == 200:
                data = r.json()["data"]
                if data:
                    return data[0], shard
        except:
            pass

    print("❌ NIE ZNALEZIONO:", name)
    return None, None


def get_match(match_id, shard):
    try:
        url = f"https://api.pubg.com/shards/{shard}/matches/{match_id}"
        r = requests.get(url, headers=HEADERS)

        if r.status_code == 200:
            return r.json()
    except:
        pass

    return None

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
                            "damage": int(s["damageDealt"])
                        })

                return rank, team

    return None, []

# =========================
# 🏆 MVP
# =========================

async def check_mvp():
    week = get_week()
    ranking = []

    for player, weeks in player_stats.items():
        if week in weeks:
            s = weeks[week]
            score = s["kills"] + s["wins"] * 10
            ranking.append((player, score))

    if not ranking:
        return

    winner = sorted(ranking, key=lambda x: x[1], reverse=True)[0][0]

    channel = client.get_channel(CHANNEL_ID)
    guild = channel.guild
    role = guild.get_role(MVP_ROLE_ID)

    for member in guild.members:
        if role in member.roles:
            await member.remove_roles(role)

    for member in guild.members:
        if member.name.lower() == winner.lower():
            await member.add_roles(role)

    await channel.send(f"🏆 MVP TYGODNIA: {winner}")

# =========================
# 🔁 MATCH CHECK
# =========================

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_matches():
    print("🔍 CHECK...")

    for player in PLAYERS:
        try:
            p, shard = get_player(player)
            if not p:
                continue

            latest = p["relationships"]["matches"]["data"][0]["id"]

            if last_matches.get(player) == latest:
                continue

            last_matches[player] = latest
            save_json("matches.json", last_matches)

            match = get_match(latest, shard)
            if not match:
                continue

            rank, team = parse_team(match, player)
            if not team:
                continue

            week = get_week()

            if player not in player_stats:
                player_stats[player] = {}

            if week not in player_stats[player]:
                player_stats[player][week] = {"wins":0,"kills":0,"damage":0}

            for t in team:
                if t["name"].lower() == player.lower():
                    player_stats[player][week]["kills"] += t["kills"]
                    player_stats[player][week]["damage"] += t["damage"]

                    if rank == 1:
                        player_stats[player][week]["wins"] += 1

            save_json("stats.json", player_stats)

            if rank == 1:
                channel = client.get_channel(CHANNEL_ID)
                await channel.send(f"🏆 {player} wygrał mecz!")

            await asyncio.sleep(1)

        except Exception as e:
            print("❌ ERROR:", e)

# =========================
# 💬 SLASH KOMENDY
# =========================

@tree.command(name="top", description="Ranking klanu")
async def top(interaction: discord.Interaction):
    ranking = []

    for p, weeks in player_stats.items():
        total = sum(w["kills"] for w in weeks.values())
        ranking.append((p, total))

    ranking.sort(key=lambda x: x[1], reverse=True)

    if not ranking:
        await interaction.response.send_message("Brak danych 😢")
        return

    text = "🏆 TOP KLANU:\n\n"

    for i, (p, k) in enumerate(ranking[:10], 1):
        text += f"{i}. {p} - {k} kills\n"

    await interaction.response.send_message(text)


@tree.command(name="stats", description="Statystyki gracza")
async def stats(interaction: discord.Interaction, nick: str):
    nick = nick.lower()

    for player, weeks in player_stats.items():
        if player.lower() == nick:
            total_kills = sum(w["kills"] for w in weeks.values())
            total_wins = sum(w["wins"] for w in weeks.values())
            total_dmg = sum(w["damage
