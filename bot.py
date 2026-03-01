import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CHECKIN_CHANNEL_ID = 123456789012345678
LOG_CHANNEL_ID = 123456789012345678
ADMIN_CHANNEL_ID = 1315024239220232264  # روم الإدارة

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"users": {}, "last_reset": str(datetime.now())}

checkins = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@bot.event
async def on_ready():
    print(f"تم تشغيل البوت {bot.user}")
    if not reset_check.is_running():
        reset_check.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == CHECKIN_CHANNEL_ID:

        if message.content == "دخول":
            if message.author.id in checkins:
                await message.channel.send("❌ أنت مسجل دخول بالفعل")
                return

            checkins[message.author.id] = datetime.now()
            await message.channel.send(f"✅ {message.author.mention} تم تسجيل دخولك")

        elif message.content == "خروج":
            if message.author.id in checkins:
                start_time = checkins.pop(message.author.id)
                duration = datetime.now() - start_time
                seconds = int(duration.total_seconds())

                user_id = str(message.author.id)
                data["users"][user_id] = data["users"].get(user_id, 0) + seconds
                save_data()

                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                await message.channel.send(
                    f"🔴 {message.author.mention} تم تسجيل خروجك\n"
                    f"⏱️ مدة جلستك: {hours} ساعة {minutes} دقيقة {seconds} ثانية"
                )
            else:
                await message.channel.send("❌ ما عندك تسجيل دخول")

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(f"🎤 {member.name} دخل الروم {after.channel.name}")

@bot.command()
async def ترتيب(ctx):
    if not data["users"]:
        await ctx.send("📊 ما فيه بيانات حالياً")
        return

    sorted_users = sorted(data["users"].items(), key=lambda x: x[1], reverse=True)
    leaderboard = "🏆 **ترتيب الأعضاء (الأعلى ساعات):**\n\n"

    for index, (user_id, total_seconds) in enumerate(sorted_users[:10], start=1):
        member = ctx.guild.get_member(int(user_id))
        if member:
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            leaderboard += (
                f"{index}- {member.mention} | "
                f"{hours} ساعة {minutes} دقيقة {seconds} ثانية\n"
            )

    await ctx.send(leaderboard)

# ------------------ أوامر الإدارة ------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def تصفير(ctx):
    if ctx.channel.id != ADMIN_CHANNEL_ID:
        await ctx.send("❌ هذا الأمر مخصص لروم الإدارة فقط")
        return

    data["users"] = {}
    save_data()
    await ctx.send("✅ تم تصفير جميع الساعات بنجاح")

@bot.command()
@commands.has_permissions(administrator=True)
async def اضافة(ctx, member: discord.Member, hours: int):
    if ctx.channel.id != ADMIN_CHANNEL_ID:
        await ctx.send("❌ استخدم الأمر في روم الإدارة فقط")
        return

    user_id = str(member.id)
    data["users"][user_id] = data["users"].get(user_id, 0) + (hours * 3600)
    save_data()

    await ctx.send(f"✅ تم إضافة {hours} ساعة لـ {member.mention}")

# ----------------------------------------------------

@tasks.loop(hours=24)
async def reset_check():
    last_reset = datetime.fromisoformat(data["last_reset"])
    if datetime.now() - last_reset >= timedelta(days=14):
        data["users"] = {}
        data["last_reset"] = str(datetime.now())
        save_data()

        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send("📅 تم تصفير الجرد (بداية فترة جديدة)")

bot.run(os.getenv("TOKEN"))
