import discord
import random
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

DRUNK_MODE = True

# 🔥 DUŻA BAZA TEKSTÓW
drunk_texts = [
    "stary ja nie jestem pijany tylko mapa się kręci",
    "kto zabrał moje piwo… oddawaj 🍺",
    "ja tylko jedno miałem wypić… przysięgam",
    "ej a jakbyśmy tak teraz kebsa zamówili?",
    "życie to jest jak loot… niby dropi ale nie dla mnie",
    "ja jestem MVP tylko nikt nie widzi potencjału",
    "cooo? kto mnie wołał?",
    "nie patrz tak na mnie ja wiem co robię",
    "czy my gramy czy ja śnię?",
    "ja bym teraz spał ale też bym grał",
    "dobra plan jest taki… nie ma planu",
    "ktoś coś mówił czy to był mój brzuch",
    "ja tu tylko przyszedłem na chwilę… 3 godziny temu",
    "jak wygramy to pijemy… a jak przegramy to też",
    "halo policja? ktoś mi zabrał godność",
    "to nie ja gram źle to gra mnie sabotuje",
    "ja mam taktykę… tylko nie pamiętam jaką",
    "czemu ja jestem martwy znowu",
    "kto mnie zabił? ja go znajdę",
    "ej serio to było blisko… chyba",
]

# 🔥 REAKCJE NA SŁOWA
keyword_responses = {
    "piwo": ["kto powiedział PIWO?! 🍺", "nalej mi też", "ja już lecę do lodówki"],
    "kebab": ["bierzemy kebsa?", "ja bym zjadł dwa", "sos mieszany obowiązkowo"],
    "win": ["NO I TO MI SIĘ PODOBA 🏆", "wiedziałem że wygramy", "easy game"],
    "przegr": ["to było ustawione", "lagi były", "ja grałem dobrze"],
    "sleep": ["ja nie śpię ja odpoczywam oczami"],
}

def drunkify(text):
    dodatki = ["...", " 🤪", " 🍺", " 😵", " 💀"]
    if random.random() < 0.5:
        text += random.choice(dodatki)
    return text


@client.event
async def on_ready():
    print(f"🍺 BOT PIJANY ONLINE: {client.user}")


@client.event
async def on_message(message):
    global DRUNK_MODE

    if message.author == client.user:
        return

    msg = message.content.lower()

    # 🔥 KOMENDY
    if msg == "!drunk on":
        DRUNK_MODE = True
        await message.channel.send("🍺 tryb pijany WŁĄCZONY")
        return

    if msg == "!drunk off":
        DRUNK_MODE = False
        await message.channel.send("😴 tryb pijany WYŁĄCZONY")
        return

    if msg == "!piwo":
        await message.channel.send("🍺 stawiam wszystkim!")
        return

    if not DRUNK_MODE:
        return

    # 🔥 REAKCJA NA SŁOWA
    for key in keyword_responses:
        if key in msg:
            reply = random.choice(keyword_responses[key])
            await message.channel.send(drunkify(reply))
            return

    # 🔥 LOSOWE ODPOWIEDZI
    if random.random() < 0.25:
        reply = random.choice(drunk_texts)
        await message.channel.send(drunkify(reply))


client.run(DISCORD_TOKEN)
