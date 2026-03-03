import discord 
from discord.ext import commands, tasks 
from datetime import datetime, timedelta 
import json 
import os 
import asyncio 
from dotenv import load_dotenv 
from typing import Optional, Dict, Any, List 
import logging 
import traceback 
import sys 
import shutil 

load_dotenv() 

# Configure logging for console only 
logging.basicConfig( 
level=logging.INFO, 
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
handlers=[logging.StreamHandler(sys.stdout)] 
) 
logger = logging.getLogger(__name__) 

intents = discord.Intents.default() 
intents.message_content = True 
intents.voice_states = True 
intents.members = True 

bot = commands.Bot(command_prefix="-", intents=intents, help_command=None)

# ================= CONFIGURATION ================= 

class Config: 
# Channel IDs 
LOGIN_BLACK = 1477712613252272190 
LOGIN_SUPERME = 1477712637901930701 
LOG_CHANNEL = 1477711736390815816 

# Voice Channels 
BLACK_VOICES = [ 
1477712092688679066, 
1477712105346957344, 
1477712117229686834, 
1477712130861170940, 
1477712143326384158, 
1477712155800244467 
] 

SUPERME_VOICES = [ 
1477711818343317595, 
1477711831069102181, 
1477711851717660902, 
1477711864023617637, 
1477711875977510963, 
1477711736390815817 
] 

# Role IDs 
SUPERME_ROLE = 1477715785689333922 
BLACK_ROLE = 1477715822687289344 
ADMIN_ROLE = 1477712762397528216 

# Data file 
DATA_FILE = "database.json" 
BACKUP_FILE = "database_backup.json" 

# ==================== DATA MANAGEMENT ==================== 

class DataManager: 
def __init__(self): 
self.data_file = Config.DATA_FILE 
self.backup_file = Config.BACKUP_FILE 
self.data = self.load() 
self.active_sessions: Dict[str, Dict[str, Any]] = {} 
self.voice_sessions: Dict[str, Dict[str, Any]] = {} 
logger.info("Data Manager initialized") 

def load(self) -> Dict: 
try: 
if os.path.exists(self.data_file): 
with open(self.data_file, "r", encoding="utf-8") as f: 
content = f.read().strip() 
if not content: 
logger.warning("Data file is empty, creating new data") 
return self.get_default_data() 

data = json.loads(content) 

# Ensure all required keys exist 
if "users" not in data: 
data["users"] = {} 
if "last_reset" not in data: 
data["last_reset"] = str(datetime.now()) 
if "total_logins" not in data: 
data["total_logins"] = 0 
if "total_logouts" not in data: 
data["total_logouts"] = 0 
if "stats" not in data: 
data["stats"] = {"black_total": 0, "superme_total": 0} 

logger.info(f"Data loaded from {self.data_file}") 
return data 
else: 
logger.info("Data file not found, creating new data") 
return self.get_default_data() 

except json.JSONDecodeError as e: 
logger.error(f"JSON decode error: {e}") 
if os.path.exists(self.backup_file): 
try: 
with open(self.backup_file, "r", encoding="utf-8") as f: 
data = json.load(f) 
logger.info("Recovered data from backup") 
return data 
except: 
pass 
return self.get_default_data() 

except Exception as e: 
logger.error(f"Error loading data: {e}") 
traceback.print_exc() 
return self.get_default_data() 

def get_default_data(self) -> Dict: 
return { 
"users": {}, 
"last_reset": str(datetime.now()), 
"total_logins": 0, 
"total_logouts": 0, 
"stats": { 
"black_total": 0, 
"superme_total": 0 
} 
} 

def save(self): 
try: 
if os.path.exists(self.data_file): 
shutil.copy2(self.data_file, self.backup_file) 

with open(self.data_file, "w", encoding="utf-8") as f: 
json.dump(self.data, f, ensure_ascii=False, indent=4) 
logger.debug("Data saved successfully") 

except Exception as e: 
logger.error(f"Error saving data: {e}") 
traceback.print_exc() 

def add_time(self, user_id: str, seconds: int, admin_type: str): 
if "users" not in self.data: 
self.data["users"] = {} 

current = self.data["users"].get(user_id, 0) 
self.data["users"][user_id] = current + seconds 

if "stats" not in self.data: 
self.data["stats"] = {"black_total": 0, "superme_total": 0} 

if admin_type == "black": 
self.data["stats"]["black_total"] = self.data["stats"].get("black_total", 0) + seconds 
else: 
self.data["stats"]["superme_total"] = self.data["stats"].get("superme_total", 0) + seconds 

self.save() 
logger.info(f"Added {seconds} seconds to user {user_id}") 

def get_user_time(self, user_id: str) -> int: 
if "users" not in self.data: 
return 0 
return self.data["users"].get(user_id, 0) 

def reset_all(self): 
before_count = len(self.data.get("users", {})) 
before_total = sum(self.data.get("users", {}).values()) / 3600 

self.data["users"] = {} 
self.data["last_reset"] = str(datetime.now()) 
self.data["stats"] = {"black_total": 0, "superme_total": 0} 
self.save() 

logger.info(f"Reset all data - {before_count} users, {before_total:.1f} hours total") 
return before_count, before_total 

dm = DataManager() 

# ==================== EMBED UTILITIES ==================== 

class EmbedFactory: 
@staticmethod 
def success(title: str, description: str, footer: str = None) -> discord.Embed: 
embed = discord.Embed( 
title=f"✅ {title}", 
description=description, 
color=0x2B2D31 
) 
if footer: 
embed.set_footer(text=footer) 
return embed 

@staticmethod 
def error(title: str, description: str) -> discord.Embed: 
return discord.Embed( 
title=f"❌ {title}", 
description=description, 
color=0x2B2D31 
) 

@staticmethod 
def info(title: str, description: str, footer: str = None) -> discord.Embed: 
embed = discord.Embed( 
title=f"ℹ️ {title}", 
description=description, 
color=0x2B2D31 
) 
if footer: 
embed.set_footer(text=footer) 
return embed 

@staticmethod 
def stats(title: str, description: str, fields: List[tuple] = None) -> discord.Embed: 
embed = discord.Embed( 
title=f"📊 {title}", 
description=description, 
color=0x2B2D31 
) 
if fields: 
for name, value, inline in fields: 
embed.add_field(name=name, value=value, inline=inline) 
return embed 

# ==================== LOGGING SYSTEM ==================== 

class LogManager: 
def __init__(self, bot): 
self.bot = bot 
self.log_queue = asyncio.Queue() 
self.bg_task = None 
logger.info("Log Manager initialized") 

async def start(self): 
self.bg_task = asyncio.create_task(self.process_log_queue()) 
logger.info("Log queue processor started") 

async def process_log_queue(self): 
while True: 
try: 
embed = await self.log_queue.get() 
channel = self.bot.get_channel(Config.LOG_CHANNEL) 
if channel: 
await channel.send(embed=embed) 
logger.debug(f"Log sent to channel {Config.LOG_CHANNEL}") 
await asyncio.sleep(1) 
except Exception as e: 
logger.error(f"Log error: {e}") 
traceback.print_exc() 

async def log(self, embed: discord.Embed): 
await self.log_queue.put(embed) 

async def login_log(self, member: discord.Member, admin_type: str): 
embed = discord.Embed( 
title="📝 تسجيل دخول", 
description=f"**العضو:** {member.mention}\n**الإدارة:** {admin_type}\n**الوقت:** {datetime.now().strftime('%Y-%m-%d %I:%M %p')}", 
color=0x2B2D31 
) 
embed.set_thumbnail(url=member.display_avatar.url) 
await self.log(embed) 
logger.info(f"Login logged for {member.name} - {admin_type}") 

async def logout_log(self, member: discord.Member, duration: str, total: str): 
embed = discord.Embed( 
title="👋 تسجيل خروج", 
description=f"**العضو:** {member.mention}\n**المدة:** {duration}\n**الإجمالي:** {total}\n**الوقت:** {datetime.now().strftime('%Y-%m-%d %I:%M %p')}", 
color=0x2B2D31 
) 
embed.set_thumbnail(url=member.display_avatar.url) 
await self.log(embed) 
logger.info(f"Logout logged for {member.name} - Duration: {duration}") 

async def command_log(self, ctx, command: str, details: str = None): 
embed = discord.Embed( 
title=f"🔧 أمر {command}", 
description=f"**المستخدم:** {ctx.author.mention}\n**القناة:** {ctx.channel.mention}\n**الأمر:** {ctx.message.content}", 
color=0x2B2D31 
) 
if details: 
embed.add_field(name="التفاصيل", value=details, inline=False) 
embed.set_footer(text=datetime.now().strftime('%Y-%m-%d %I:%M %p')) 
await self.log(embed) 
logger.info(f"Command logged: {command} by {ctx.author.name}") 

async def admin_action_log(self, admin: discord.Member, action: str, target: discord.Member = None, value: str = None): 
embed = discord.Embed( 
title=f"⚡ إجراء إداري", 
description=f"**المشرف:** {admin.mention}\n**الإجراء:** {action}", 
color=0x2B2D31 
) 
if target: 
embed.add_field(name="المستهدف", value=target.mention, inline=True) 
if value: 
embed.add_field(name="القيمة", value=value, inline=True) 
embed.set_footer(text=datetime.now().strftime('%Y-%m-%d %I:%M %p')) 
await self.log(embed) 
logger.info(f"Admin action: {action} by {admin.name}") 

async def voice_log(self, member: discord.Member, action: str, channel_name: str, admin_type: str): 
embed = discord.Embed( 
title=f"🎤 {action} روم صوتي", 
description=f"**العضو:** {member.mention}\n**الروم:** {channel_name}\n**الإدارة:** {admin_type}\n**الوقت:** {datetime.now().strftime('%I:%M %p')}", 
color=0x2B2D31 
) 
await self.log(embed) 
logger.info(f"Voice {action} for {member.name} in {channel_name}") 

log_manager = LogManager(bot) 

# ==================== PERMISSION CHECKS ==================== 

def has_jrd_role(): 
async def predicate(ctx): 
if not ctx.guild: 
logger.warning(f"Command used outside guild by {ctx.author.name}") 
return False 

role = ctx.guild.get_role(Config.ADMIN_ROLE) 
if role and role in ctx.author.roles: 
logger.debug(f"Permission granted to {ctx.author.name} for admin command") 
return True 

logger.info(f"Permission denied to {ctx.author.name} for admin command - missing role {Config.ADMIN_ROLE}") 
return False 
return commands.check(predicate) 

# ==================== BOT EVENTS ==================== 

@bot.event 
async def on_ready(): 
logger.info(f"Bot connected: {bot.user} (ID: {bot.user.id})") 
logger.info(f"Guilds: {len(bot.guilds)}") 

await log_manager.start() 

status_embed = discord.Embed( 
title="🟢 البوت شغال", 
description=f"تم تشغيل البوت بنجاح\n**الوقت:** {datetime.now().strftime('%Y-%m-%d %I:%M %p')}", 
color=0x2B2D31 
) 
await log_manager.log(status_embed) 

if not auto_reset_loop.is_running(): 
auto_reset_loop.start() 
logger.info("Auto reset loop started") 

@bot.event 
async def on_command_error(ctx, error): 
logger.error(f"Command error for {ctx.author.name}: {error}") 
logger.error(f"Command: {ctx.message.content}") 
traceback.print_exc() 

if isinstance(error, commands.MissingRequiredArgument): 
if ctx.command and ctx.command.name == "جرد": 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"استخدام صحيح: `-جرد @user`\nمثال: `-جرد @{ctx.author.name}`" 
) 
await ctx.send(embed=embed) 
elif ctx.command and ctx.command.name == "اضافة": 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"استخدام صحيح: `-اضافة @user عدد الساعات`\nمثال: `-اضافة @{ctx.author.name} 5`" 
) 
await ctx.send(embed=embed) 
elif ctx.command and ctx.command.name == "حذف": 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"استخدام صحيح: `-حذف @user عدد الساعات`\nمثال: `-حذف @{ctx.author.name} 5`" 
) 
await ctx.send(embed=embed) 
else: 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"الأمر ناقص مدخلات. استخدم `-مساعدة` للتعرف على طريقة الاستخدام" 
) 
await ctx.send(embed=embed) 

elif isinstance(error, commands.CheckFailure): 
if ctx.command and ctx.command.name in ["جرد", "اضافة", "حذف", "تصفير"]: 
embed = EmbedFactory.error( 
"صلاحية", 
f"{ctx.author.mention} ما عندك صلاحية استخدام هذا الأمر.\nالرتبة المطلوبة: <@&{Config.ADMIN_ROLE}>" 
) 
await ctx.send(embed=embed) 
await log_manager.admin_action_log(ctx.author, "محاولة استخدام أمر إداري ممنوع") 

elif isinstance(error, commands.BadArgument): 
embed = EmbedFactory.error( 
"خطأ في المدخلات", 
"تأكد من كتابة العضو بشكل صحيح (منشن)" 
) 
await ctx.send(embed=embed) 

elif isinstance(error, commands.CommandNotFound): 
pass 

elif isinstance(error, KeyError): 
logger.error(f"KeyError: {error}") 

else: 
embed = EmbedFactory.error( 
"خطأ غير متوقع", 
"حدث خطأ أثناء تنفيذ الأمر. تم تسجيل الخطأ وإبلاغ الإدارة." 
) 
await ctx.send(embed=embed) 

# ==================== LOGIN/LOGOUT COMMANDS ==================== 

@bot.command(name="دخول") 
async def login(ctx): 
"""تسجيل دخول في النظام""" 
logger.info(f"Login attempt by {ctx.author.name} in channel {ctx.channel.id}") 

if ctx.channel.id == Config.LOGIN_BLACK: 
if not ctx.author.get_role(Config.BLACK_ROLE): 
embed = EmbedFactory.error( 
"صلاحية", 
f"{ctx.author.mention} ما عندك رتبة الإدارة السوداء." 
) 
await ctx.send(embed=embed) 
logger.info(f"Login denied for {ctx.author.name} - missing black role") 
return 
admin_type = "السوداء" 
admin_key = "black" 
elif ctx.channel.id == Config.LOGIN_SUPERME: 
if not ctx.author.get_role(Config.SUPERME_ROLE): 
embed = EmbedFactory.error( 
"صلاحية", 
f"{ctx.author.mention} ما عندك رتبة الإدارة السوبر." 
) 
await ctx.send(embed=embed) 
logger.info(f"Login denied for {ctx.author.name} - missing superme role") 
return 
admin_type = "السوبر" 
admin_key = "superme" 
else: 
logger.debug(f"Login attempt in wrong channel by {ctx.author.name}") 
return 

user_id = str(ctx.author.id) 

if user_id in dm.active_sessions: 
embed = EmbedFactory.error( 
"مكرر", 
f"{ctx.author.mention} انت مسجل دخول بالفعل." 
) 
await ctx.send(embed=embed) 
logger.info(f"Login denied for {ctx.author.name} - already logged in") 
return 

for sid, session in dm.active_sessions.items(): 
if session["type"] != admin_key: 
other_type = "السوداء" if session["type"] == "black" else "السوبر" 
embed = EmbedFactory.error( 
"تعارض", 
f"{ctx.author.mention} لا يمكنك تسجيل الدخول في الإدارة {admin_type} وأنت مسجل في {other_type}." 
) 
await ctx.send(embed=embed) 
logger.info(f"Login denied for {ctx.author.name} - conflict with another session") 
return 

dm.active_sessions[user_id] = { 
"time": datetime.now(), 
"type": admin_key, 
"name": ctx.author.name, 
"channel": ctx.channel.id, 
"voice_time": 0, 
"in_voice": False, 
"voice_start": None 
} 

dm.data["total_logins"] = dm.data.get("total_logins", 0) + 1 
dm.save() 

embed = EmbedFactory.success( 
"تم تسجيل الدخول", 
f"أهلاً {ctx.author.mention}\n" 
f"تم تسجيل دخولك في **الإدارة {admin_type}**.\n" 
f"الوقت: {datetime.now().strftime('%I:%M %p')}\n\n" 
f"بالتوفيق ياغالي." 
) 
await ctx.send(embed=embed) 

await log_manager.login_log(ctx.author, admin_type) 
logger.info(f"Login successful for {ctx.author.name} as {admin_type}") 

@bot.command(name="خروج") 
async def logout(ctx): 
"""تسجيل خروج من النظام""" 
logger.info(f"Logout attempt by {ctx.author.name}") 

if ctx.channel.id not in [Config.LOGIN_BLACK, Config.LOGIN_SUPERME]: 
return 

user_id = str(ctx.author.id) 

if user_id not in dm.active_sessions: 
embed = EmbedFactory.error( 
"غير مسجل", 
f"{ctx.author.mention} أنت غير مسجل دخول." 
) 
await ctx.send(embed=embed) 
logger.info(f"Logout denied for {ctx.author.name} - not logged in") 
return 

session = dm.active_sessions.pop(user_id) 

# حساب وقت الجلسة الأساسي (الوقت من لحظة تسجيل الدخول) 
session_duration = datetime.now() - session["time"] 
total_seconds = int(session_duration.total_seconds()) 

# إذا كان في روم صوتي، نضيف وقت الصوت 
if session.get("in_voice", False) and session.get("voice_start"): 
voice_duration = datetime.now() - session["voice_start"] 
voice_seconds = int(voice_duration.total_seconds()) 
total_seconds += voice_seconds 
logger.info(f"Added {voice_seconds}s voice time for {ctx.author.name}") 

# إضافة الوقت إلى قاعدة البيانات 
dm.add_time(user_id, total_seconds, session["type"]) 

# حساب مدة الجلسة 
hours, remainder = divmod(total_seconds, 3600) 
minutes, secs = divmod(remainder, 60) 
time_text = f"{hours} ساعة {minutes} دقيقة {secs} ثانية" 

# حساب الإجمالي 
total = dm.get_user_time(user_id) 
t_hours, t_remainder = divmod(total, 3600) 
t_minutes, t_secs = divmod(t_remainder, 60) 
total_text = f"{t_hours} ساعة {t_minutes} دقيقة {t_secs} ثانية" 

embed = EmbedFactory.success( 
"تم تسجيل الخروج", 
f"مع السلامة {ctx.author.mention}\n" 
f"**مدة جلستك:** {time_text}\n" 
f"**إجمالي جردك:** {total_text}\n\n" 
f"تم إضافة الوقت إلى جردك." 
) 
await ctx.send(embed=embed) 

dm.data["total_logouts"] = dm.data.get("total_logouts", 0) + 1 
dm.save() 

await log_manager.logout_log(ctx.author, time_text, total_text) 
logger.info(f"Logout successful for {ctx.author.name} - Duration: {time_text}") 

# ==================== USER COMMANDS ==================== 

@bot.command(name="وقتي") 
async def my_time(ctx): 
"""عرض وقتك الشخصي""" 
logger.info(f"Time check by {ctx.author.name}") 

user_id = str(ctx.author.id) 
total_seconds = dm.get_user_time(user_id) 

hours, remainder = divmod(total_seconds, 3600) 
minutes, seconds = divmod(remainder, 60) 

current_info = "" 
voice_info = "" 

if user_id in dm.active_sessions: 
session = dm.active_sessions[user_id] 

# وقت الجلسة الأساسي 
elapsed = datetime.now() - session["time"] 
e_hours, e_remainder = divmod(int(elapsed.total_seconds()), 3600) 
e_minutes, e_secs = divmod(e_remainder, 60) 

admin_type = "السوداء" if session["type"] == "black" else "السوبر" 
current_info = f"\n**الجلسة الحالية:**\n" 
current_info += f"الإدارة: {admin_type}\n" 
current_info += f"وقت الدخول: {e_hours} ساعة {e_minutes} دقيقة\n" 
current_info += f"منذ: {session['time'].strftime('%I:%M %p')}" 

# إذا كان في روم صوتي 
if session.get("in_voice", False) and session.get("voice_start"): 
v_elapsed = datetime.now() - session["voice_start"] 
v_hours, v_remainder = divmod(int(v_elapsed.total_seconds()), 3600) 
v_minutes, v_secs = divmod(v_remainder, 60) 
voice_info = f"\n**🎤 في روم صوتي:**\n" 
voice_info += f"المدة: {v_hours} ساعة {v_minutes} دقيقة" 

fields = [] 
if current_info: 
fields.append(("📌 الدخول", current_info, False)) 
if voice_info: 
fields.append(("🎤 الصوت", voice_info, False)) 

embed = EmbedFactory.stats( 
"الجرد الشخصي", 
f"{ctx.author.mention}\n" 
f"**إجمالي الوقت المسجل:** {hours} ساعة {minutes} دقيقة {seconds} ثانية", 
fields 
) 
embed.set_thumbnail(url=ctx.author.display_avatar.url) 
await ctx.send(embed=embed) 

await log_manager.command_log(ctx, "وقتي", f"الجرد: {hours} ساعة {minutes} دقيقة") 

@bot.command(name="ترتيب") 
async def leaderboard(ctx): 
"""عرض ترتيب الأعضاء حسب الساعات""" 
logger.info(f"Leaderboard viewed by {ctx.author.name}") 

if not dm.data.get("users"): 
embed = EmbedFactory.info( 
"لا توجد بيانات", 
"مافي جرد حالياً لعرض الترتيب." 
) 
await ctx.send(embed=embed) 
return 

sorted_users = sorted(dm.data["users"].items(), key=lambda x: x[1], reverse=True) 

total_hours_all = sum(dm.data["users"].values()) / 3600 
avg_hours = total_hours_all / len(dm.data["users"]) if dm.data["users"] else 0 

embed = discord.Embed( 
title="🏆 ترتيب الأعضاء", 
description=f"**إجمالي الساعات:** {total_hours_all:.1f} ساعة\n" 
f"**المتوسط:** {avg_hours:.1f} ساعة\n" 
f"**الأعضاء:** {len(dm.data['users'])}\n", 
color=0x2B2D31 
) 

rank_text = "" 
medals = ["🥇", "🥈", "🥉"] 

for index, (user_id, total_seconds) in enumerate(sorted_users[:15], 1): 
member = ctx.guild.get_member(int(user_id)) 
if member: 
hours, remainder = divmod(total_seconds, 3600) 
minutes, _ = divmod(remainder, 60) 

medal = medals[index-1] if index <= 3 else f"**{index}.**" 

status = "" 
if user_id in dm.active_sessions: 
session = dm.active_sessions[user_id] 
if session.get("in_voice", False): 
status = "🎤" 
else: 
status = "🟢" 

rank_text += f"{medal} {member.mention} {status}\n" 
rank_text += f"⏱️ {hours} ساعة {minutes} دقيقة\n\n" 

embed.description += f"\n{rank_text}" 

if len(sorted_users) > 15: 
embed.set_footer(text=f"و {len(sorted_users) - 15} عضو آخر") 

await ctx.send(embed=embed) 
await log_manager.command_log(ctx, "ترتيب") 

@bot.command(name="المسجلين") 
async def active_users(ctx): 
"""عرض الأعضاء المسجلين حالياً""" 
logger.info(f"Active users viewed by {ctx.author.name}") 

if not dm.active_sessions: 
embed = EmbedFactory.info( 
"لا يوجد مسجلين", 
"مافي أحد مسجل دخول حالياً." 
) 
await ctx.send(embed=embed) 
return 

embed = discord.Embed( 
title="👥 الأعضاء المسجلين حالياً", 
description=f"**العدد:** {len(dm.active_sessions)} عضو\n" 
f"**الوقت:** {datetime.now().strftime('%I:%M %p')}", 
color=0x2B2D31 
) 

black_count = 0 
superme_count = 0 

for user_id, session in dm.active_sessions.items(): 
member = ctx.guild.get_member(int(user_id)) 
if member: 
elapsed = datetime.now() - session["time"] 
hours = int(elapsed.total_seconds() // 3600) 
minutes = int((elapsed.total_seconds() % 3600) // 60) 

admin_type = "⚫ السوداء" if session["type"] == "black" else "🔵 السوبر" 
if session["type"] == "black": 
black_count += 1 
else: 
superme_count += 1 

voice_status = "" 
if session.get("in_voice", False): 
voice_status = "\n🎤 في روم صوتي" 

embed.add_field( 
name=member.display_name, 
value=f"{admin_type}{voice_status}\n⏱️ {hours} ساعة {minutes} دقيقة\nمنذ {session['time'].strftime('%I:%M %p')}", 
inline=True 
) 

embed.description += f"\n**السوداء:** {black_count} | **السوبر:** {superme_count}" 
await ctx.send(embed=embed) 
await log_manager.command_log(ctx, "المسجلين", f"العدد: {len(dm.active_sessions)}") 

# ==================== ADMIN COMMANDS ==================== 

@bot.command(name="جرد") 
@has_jrd_role() 
async def user_time(ctx, member: discord.Member = None): 
"""عرض جرد عضو معين""" 
logger.info(f"User time check by admin {ctx.author.name}") 

if member is None: 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"استخدام صحيح: `-جرد @user`\nمثال: `-جرد @{ctx.author.name}`" 
) 
await ctx.send(embed=embed) 
return 

user_id = str(member.id) 
total_seconds = dm.get_user_time(user_id) 

if total_seconds == 0: 
embed = EmbedFactory.info( 
"لا يوجد جرد", 
f"{member.mention} ما عنده جرد مسجل." 
) 
await ctx.send(embed=embed) 
return 

hours, remainder = divmod(total_seconds, 3600) 
minutes, seconds = divmod(remainder, 60) 

status = "⚫ غير مسجل" 
if user_id in dm.active_sessions: 
session = dm.active_sessions[user_id] 
if session.get("in_voice", False): 
status = "🎤 في روم صوتي" 
else: 
status = "🟢 مسجل حالياً" 

embed = EmbedFactory.stats( 
"جرد العضو", 
f"{member.mention}\n" 
f"**الحالة:** {status}\n" 
f"**إجمالي الوقت:** {hours} ساعة {minutes} دقيقة {seconds} ثانية" 
) 
embed.set_thumbnail(url=member.display_avatar.url) 
await ctx.send(embed=embed) 

await log_manager.admin_action_log( 
ctx.author, 
"عرض جرد", 
member, 
f"{hours} ساعة {minutes} دقيقة" 
) 
logger.info(f"Admin {ctx.author.name} viewed {member.name}'s time: {hours}h {minutes}m") 

@bot.command(name="اضافة") 
@has_jrd_role() 
async def add_time(ctx, member: discord.Member = None, hours: int = None): 
"""إضافة ساعات لعضو""" 
logger.info(f"Add time attempt by admin {ctx.author.name}") 

if member is None or hours is None: 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"استخدام صحيح: `-اضافة @user عدد الساعات`\nمثال: `-اضافة @{ctx.author.name} 5`" 
) 
await ctx.send(embed=embed) 
return 

if hours <= 0 or hours > 1000: 
embed = EmbedFactory.error( 
"قيمة غير صحيحة", 
"يجب أن تكون الساعات بين 1 و 1000" 
) 
await ctx.send(embed=embed) 
logger.warning(f"Admin {ctx.author.name} tried to add invalid hours: {hours}") 
return 

user_id = str(member.id) 
current = dm.get_user_time(user_id) 
dm.data["users"][user_id] = current + (hours * 3600) 
dm.save() 

new_total = dm.get_user_time(user_id) 
new_hours, new_remainder = divmod(new_total, 3600) 
new_minutes, _ = divmod(new_remainder, 60) 

embed = EmbedFactory.success( 
"تمت الإضافة", 
f"تم إضافة **{hours} ساعة** إلى جرد {member.mention}\n" 
f"**الجرد الجديد:** {new_hours} ساعة {new_minutes} دقيقة" 
) 
await ctx.send(embed=embed) 

await log_manager.admin_action_log( 
ctx.author, 
"إضافة ساعات", 
member, 
f"{hours} ساعة" 
) 
logger.info(f"Admin {ctx.author.name} added {hours} hours to {member.name}") 

@bot.command(name="حذف") 
@has_jrd_role() 
async def remove_time(ctx, member: discord.Member = None, hours: int = None): 
"""حذف ساعات من عضو""" 
logger.info(f"Remove time attempt by admin {ctx.author.name}") 

if member is None or hours is None: 
embed = EmbedFactory.error( 
"خطأ في الأمر", 
f"استخدام صحيح: `-حذف @user عدد الساعات`\nمثال: `-حذف @{ctx.author.name} 5`" 
) 
await ctx.send(embed=embed) 
return 

if hours <= 0 or hours > 1000: 
embed = EmbedFactory.error( 
"قيمة غير صحيحة", 
"يجب أن تكون الساعات بين 1 و 1000" 
) 
await ctx.send(embed=embed) 
logger.warning(f"Admin {ctx.author.name} tried to remove invalid hours: {hours}") 
return 

user_id = str(member.id) 
current = dm.get_user_time(user_id) 
new_total = max(0, current - (hours * 3600)) 
dm.data["users"][user_id] = new_total 
dm.save() 

new_hours, new_remainder = divmod(new_total, 3600) 
new_minutes, _ = divmod(new_remainder, 60) 

embed = EmbedFactory.success( 
"تم الحذف", 
f"تم حذف **{hours} ساعة** من جرد {member.mention}\n" 
f"**الجرد الجديد:** {new_hours} ساعة {new_minutes} دقيقة" 
) 
await ctx.send(embed=embed) 

await log_manager.admin_action_log( 
ctx.author, 
"حذف ساعات", 
member, 
f"{hours} ساعة" 
) 
logger.info(f"Admin {ctx.author.name} removed {hours} hours from {member.name}") 

@bot.command(name="تصفير") 
@has_jrd_role() 
async def reset_all(ctx): 
"""تصفير جميع الجرد""" 
logger.info(f"Reset all attempt by admin {ctx.author.name}") 

embed = EmbedFactory.info( 
"تأكيد التصفير", 
f"{ctx.author.mention} هل أنت متأكد من تصفير جميع الجرد؟\n" 
f"العدد: {len(dm.data.get('users', {}))} عضو\n" 
f"الإجمالي: {sum(dm.data.get('users', {}).values()) / 3600:.1f} ساعة\n\n" 
f"اكتب `-تأكيد` خلال 10 ثواني" 
) 
await ctx.send(embed=embed) 

def check(m): 
return m.author == ctx.author and m.channel == ctx.channel and m.content == "-تأكيد" 

try: 
await bot.wait_for("message", timeout=10.0, check=check) 
except asyncio.TimeoutError: 
embed = EmbedFactory.error( 
"إلغاء", 
"تم إلغاء عملية التصفير." 
) 
await ctx.send(embed=embed) 
logger.info(f"Reset cancelled by {ctx.author.name} - timeout") 
return 

before_count, before_total = dm.reset_all() 

embed = EmbedFactory.success( 
"تم التصفير", 
f"تم تصفير جميع الجرد بنجاح\n" 
f"**قبل:** {before_count} عضو | {before_total:.1f} ساعة" 
) 
await ctx.send(embed=embed) 

await log_manager.admin_action_log( 
ctx.author, 
"تصفير الجرد", 
value=f"{before_count} عضو | {before_total:.1f} ساعة" 
) 
logger.info(f"Admin {ctx.author.name} reset all data - {before_count} users, {before_total:.1f} hours") 

@bot.command(name="مساعدة") 
async def help_command(ctx): 
"""عرض قائمة الأوامر""" 
logger.info(f"Help viewed by {ctx.author.name}") 

embed = discord.Embed( 
title="📋 قائمة الأوامر", 
description="نظام تسجيل الدوام للإدارات", 
color=0x2B2D31 
) 

general = ( 
"`-دخول` - تسجيل دخول\n" 
"`-خروج` - تسجيل خروج\n" 
"`-وقتي` - عرض جردك\n" 
"`-ترتيب` - عرض الترتيب\n" 
"`-المسجلين` - عرض المسجلين حالياً\n" 
"`-مساعدة` - عرض هذه القائمة" 
) 
embed.add_field(name="👤 عامة", value=general, inline=False) 

if ctx.author.get_role(Config.ADMIN_ROLE): 
admin = ( 
"`-جرد @user` - عرض جرد عضو\n" 
"`-اضافة @user عدد` - إضافة ساعات\n" 
"`-حذف @user عدد` - حذف ساعات\n" 
"`-تصفير` - تصفير الكل" 
) 
embed.add_field(name="⚡ إدارية", value=admin, inline=False) 

embed.set_footer(text="نظام تسجيل الدوام v4.0") 
await ctx.send(embed=embed) 
await log_manager.command_log(ctx, "مساعدة") 

# ==================== VOICE EVENTS ==================== 

@bot.event 
async def on_voice_state_update(member, before, after): 
user_id = str(member.id) 

if user_id not in dm.active_sessions: 
return 

session = dm.active_sessions[user_id] 
session_type = session["type"] 
allowed_channels = Config.BLACK_VOICES if session_type == "black" else Config.SUPERME_VOICES 

# User joined a voice channel 
if before.channel is None and after.channel is not None: 
if after.channel.id in allowed_channels: 
session["in_voice"] = True 
session["voice_start"] = datetime.now() 

await log_manager.voice_log( 
member, 
"دخول", 
after.channel.name, 
"السوداء" if session_type == "black" else "السوبر" 
) 
logger.info(f"{member.name} joined voice channel {after.channel.name}") 

# User left a voice channel 
elif before.channel is not None and after.channel is None: 
if before.channel.id in allowed_channels and session.get("in_voice", False): 
voice_duration = datetime.now() - session["voice_start"] 
voice_seconds = int(voice_duration.total_seconds()) 

# Add voice time to session 
if "voice_time" not in session: 
session["voice_time"] = 0 
session["voice_time"] += voice_seconds 

session["in_voice"] = False 
session["voice_start"] = None 

await log_manager.voice_log( 
member, 
"خروج", 
before.channel.name, 
"السوداء" if session_type == "black" else "السوبر" 
) 
logger.info(f"{member.name} left voice channel {before.channel.name} - duration: {voice_seconds}s") 

# User switched voice channels 
elif before.channel is not None and after.channel is not None and before.channel != after.channel: 
# Leaving old channel 
if before.channel.id in allowed_channels and session.get("in_voice", False): 
voice_duration = datetime.now() - session["voice_start"] 
voice_seconds = int(voice_duration.total_seconds()) 

if "voice_time" not in session: 
session["voice_time"] = 0 
session["voice_time"] += voice_seconds 

logger.info(f"{member.name} switched from {before.channel.name} - duration: {voice_seconds}s") 

# Joining new channel 
if after.channel.id in allowed_channels: 
session["in_voice"] = True 
session["voice_start"] = datetime.now() 

await log_manager.voice_log( 
member, 
"دخول", 
after.channel.name, 
"السوداء" if session_type == "black" else "السوبر" 
) 
logger.info(f"{member.name} joined voice channel {after.channel.name}") 
else: 
session["in_voice"] = False 
session["voice_start"] = None 

# ==================== AUTO RESET ==================== 

@tasks.loop(hours=24) 
async def auto_reset_loop(): 
logger.info("Auto reset check running") 
last_reset = datetime.fromisoformat(dm.data["last_reset"]) 
if datetime.now() - last_reset >= timedelta(days=14): 
before_count, before_total = dm.reset_all() 

embed = discord.Embed( 
title="📅 تصفير تلقائي", 
description=f"تم تصفير الجرد التلقائي (بداية فترة جديدة)\n" 
f"**قبل:** {before_count} عضو | {before_total:.1f} ساعة", 
color=0x2B2D31 
) 
await log_manager.log(embed) 
logger.info(f"Auto reset completed - {before_count} users, {before_total:.1f} hours") 

@auto_reset_loop.before_loop 
async def before_reset(): 
await bot.wait_until_ready() 
logger.info("Auto reset loop ready") 

# ==================== RUN BOT ==================== 

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
if __name__ == "__main__":
    token = os.getenv("TOKEN")
    keep_alive()
    logger.info("Starting bot...")
    bot.run(token)

