import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

ADMIN_ROLE = 1465006200889413663

VOICE_CHANNELS = [
1465008031149326550,
1465008034781859941,
1465008038485426186,
1465008041710588168,
1465008045498302686,
1465008049662988380,
1465008053563953214,
1465008060433961095,
1465008064141983920,
1465008156169212177,
1465008159780372591,
1465008164452962478,
1465008169154510974,
1465008172497633430,
1465008175840493569,
1465008152628953291
]

RANK_CHANNEL = 1477709730028982373
LOG_CHANNEL = 1477709730028982373

DATA_FILE = "data.json"
SESSIONS = {}

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE,"w") as f:
        json.dump({},f)

def load():
    with open(DATA_FILE,"r") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE,"w") as f:
        json.dump(data,f)

@bot.event
async def on_voice_state_update(member, before, after):

    if member.bot:
        return

    guild = member.guild
    log_channel = guild.get_channel(LOG_CHANNEL)

    has_role = any(role.id == ADMIN_ROLE for role in member.roles)

    if not has_role:
        return

    if after.channel and after.channel.id in VOICE_CHANNELS:

        SESSIONS[member.id] = datetime.utcnow()

        if log_channel:
            await log_channel.send(f"🟢 {member.mention} دخل روم الجرد")

    if before.channel and before.channel.id in VOICE_CHANNELS and not after.channel:

        start = SESSIONS.get(member.id)

        if start:

            seconds = (datetime.utcnow() - start).total_seconds()

            data = load()

            uid = str(member.id)

            if uid not in data:
                data[uid] = 0

            data[uid] += int(seconds)

            if seconds >= 14400:
                data[uid] += 3600

            save(data)

            del SESSIONS[member.id]

        if log_channel:
            await log_channel.send(f"🔴 {member.mention} خرج من روم الجرد")

@tasks.loop(minutes=5)
async def update_panel():

    data = load()

    ranking = sorted(data.items(), key=lambda x: x[1], reverse=True)

    guild = bot.guilds[0]
    channel = guild.get_channel(RANK_CHANNEL)

    if not channel:
        return

    medals = ["👑","🥈","🥉"]

    top = ""
    board = ""

    pos = 1

    for i,(uid,sec) in enumerate(ranking):

        member = guild.get_member(int(uid))

        if not member:
            continue

        hours = round(sec/3600,2)

        if i < 3:
            top += f"{medals[i]} {member.name} | {hours} ساعة\n"

        if pos <= 10:
            board += f"{pos}- {member.name} | {hours} ساعة\n"
            pos += 1

    embed = discord.Embed(
        title="🏆 لوحة ترتيب الإداريين",
        color=0x2f3136
    )

    embed.add_field(
        name="🔥 أفضل 3 إداريين",
        value=top if top else "لا يوجد بيانات",
        inline=False
    )

    embed.add_field(
        name="📊 Top 10",
        value=board if board else "لا يوجد بيانات",
        inline=False
    )

    async for msg in channel.history(limit=10):
        if msg.author == bot.user:
            await msg.edit(embed=embed)
            return

    await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot ready {bot.user}")
    update_panel.start()

bot.run(TOKEN)