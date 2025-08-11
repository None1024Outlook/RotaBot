import rotaeno

import os
import json
import time
import asyncio
import discord
import validators
import discord.app_commands
import discord.ext.commands

DISCORD_BOT_TOKEN = "Your Discord Bot Token"
DISCORD_USER_DATAS_FILE = "data/users.json"
USER_DATAS = {}
with open(DISCORD_USER_DATAS_FILE, "r", encoding="utf-8") as f:
    USER_DATAS = json.load(f)
LOCALES_DIR = "data/i18n"
LOCALES = {}
for locale_file in os.listdir(LOCALES_DIR):
    with open(os.path.join(LOCALES_DIR, locale_file), "r", encoding="utf-8") as f:
        LOCALES[locale_file.split(".")[0]] = json.load(f)

def t(key, locale="zh-CN", **kwargs):
    text: str = LOCALES.get(str(locale), LOCALES.get("zh-CN", {})).get(key, key)
    return text.format(**kwargs)

def verify_user_data(user_id, required_keys: list = ["serverCode", "objectID", "sessionToken"]):
    user_id = str(user_id)
    
    for key in required_keys:
        try:
            USER_DATAS[user_id]
        except KeyError:
            return False, f"missing-required-parameter-{key}"
        
        if "serverCode" in USER_DATAS[user_id]:
            if USER_DATAS[user_id]["serverCode"] == "private":
                if "privateServerURL" not in USER_DATAS[user_id]:
                    return False, f"missing-required-parameter-privateServerURL"
        if key not in USER_DATAS[user_id]:
            save_user_datas()
            return False, f"missing-required-parameter-{key}"
    
    save_user_datas()
    return True, "binding-successful"

def save_user_datas():
    global USER_DATAS
    with open(DISCORD_USER_DATAS_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_DATAS, f, ensure_ascii=False, indent=4)
    with open(DISCORD_USER_DATAS_FILE, "r", encoding="utf-8") as f:
        USER_DATAS = json.load(f)

async def songAliasAutocomplete(interaction: discord.Interaction, current: str):
    fit = 80
    while fit > 0:
        results = rotaeno.database.song_alias.song_alias.get_song_id(song_alias=current, fit=fit)
        if len(results) != 0: break
        fit -= 5
    return [
        discord.app_commands.Choice(name=alias, value=alias)
        for alias in list(results.keys())[:10]
    ]

async def update_user_datas(interaction: discord.Interaction, key: str, value: str, send_message: bool = True):
    user_id = str(interaction.user.id)
    user_locale = interaction.locale
    USER_DATAS[user_id] = USER_DATAS.get(user_id, {})
    USER_DATAS[user_id][key] = value
    
    _, key = verify_user_data(user_id)
    if send_message:
        await interaction.followup.send(t(key, user_locale))

class choiceValue:
    def __init__(self, value):
        self.value = value

async def time_calculator_async(func, *args, **kwargs):
    start_time = time.time()
    result = await func(*args, **kwargs)
    end_time = time.time()
    return result, round(end_time - start_time, 2)

async def time_calculator_sync(func, *args, **kwargs):
    start_time = time.time()
    result = await asyncio.to_thread(func, *args, **kwargs)
    end_time = time.time()
    return result, round(end_time - start_time, 2)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.messages = True
bot = discord.ext.commands.Bot(command_prefix="/", intents=intents)

class LoginGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="login", description="登录Rotaeno账户")
    
    @discord.app_commands.command(name="server", description="设置登录服务器")
    @discord.app_commands.describe(server_code="服务器代码", private_server_url="私有服务器地址")
    @discord.app_commands.choices(server_code=[
        discord.app_commands.Choice(name="国服", value="cn"),
        discord.app_commands.Choice(name="国际服", value="global"),
        discord.app_commands.Choice(name="私有服务器", value="private")
    ])
    async def login_server(self, interaction: discord.Interaction, server_code: discord.app_commands.Choice[str], private_server_url: str = ""):
        await interaction.response.defer()
        
        locale = interaction.locale
        
        if server_code.value not in ["cn", "global", "private"]:
            await interaction.followup.send(t("unavailable-server-code", locale, server_code=server_code.value), ephemeral=True)
            return
        if server_code.value == "private" and not validators.url(private_server_url):
            await interaction.followup.send(t("unavailable-private-server-url", locale, private_server_url=private_server_url), ephemeral=True)
            return
        
        await handle_login(interaction, mode="server", server_code=server_code.value, private_server_url=private_server_url)
    
    @discord.app_commands.command(name="objectid", description="设置objectID")
    @discord.app_commands.describe(object_id="objectID")
    async def login_objectid(self, interaction: discord.Interaction, object_id: str):
        await interaction.response.defer()
        
        await handle_login(interaction, mode="objectid", object_id=object_id)
    
    @discord.app_commands.command(name="session", description="设置sessionToken")
    @discord.app_commands.describe(session_token="sessionToken")
    async def login_session(self, interaction: discord.Interaction, session_token: str):
        await interaction.response.defer()
        
        await handle_login(interaction, mode="session", session_token=session_token)
    
    @discord.app_commands.command(name="qrcode", description="通过TapTap扫描二维码获取登录数据")
    @discord.app_commands.describe(server_code="服务器代码")
    @discord.app_commands.choices(server_code=[
        discord.app_commands.Choice(name="国服", value="cn"),
        discord.app_commands.Choice(name="国际服", value="global"),
    ])
    async def login_qrcode(self, interaction: discord.Interaction, server_code: discord.app_commands.Choice[str]):
        await interaction.response.defer()
        
        locale = interaction.locale
        
        if server_code.value not in ["cn", "global"]:
            await interaction.followup.send(t("unavailable-server-code", locale, server_code=server_code.value), ephemeral=True)
            return
        
        await handle_login(interaction, mode="qrcode", server_code=server_code.value)

class B40Group(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="b40", description="Best40相关功能")
    
    @discord.app_commands.command(name="default", description="生成Best40数据")
    async def b40_default(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        await handle_b40(interaction, mode="default")

class SongGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="song", description="歌曲相关功能")
    
    @discord.app_commands.command(name="info", description="获取单曲信息")
    @discord.app_commands.describe(song_alias="歌曲别名")
    @discord.app_commands.autocomplete(song_alias=songAliasAutocomplete)
    async def song_info(self, interaction: discord.Interaction, song_alias: str):
        await interaction.response.defer()
        
        locale = interaction.locale
        
        if not rotaeno.database.song_alias.song_alias.get_song_id(song_alias):
            await interaction.followup.send(t("song-alias-not-found", locale, song_alias=song_alias), ephemeral=True)
            return
        
        await handle_song(interaction, mode="info", song_alias=song_alias)
    
    @discord.app_commands.command(name="status", description="获取歌曲状态数据")
    @discord.app_commands.describe(song_status="歌曲状态")
    @discord.app_commands.choices(song_status=[
        discord.app_commands.Choice(name="None", value="NONE"),
        discord.app_commands.Choice(name="Full Combo", value="FC"),
        discord.app_commands.Choice(name="All Perfect", value="AP"),
        discord.app_commands.Choice(name="All Perfect Plus", value="APP"),
        discord.app_commands.Choice(name="Clear", value="CLEAR"),
        discord.app_commands.Choice(name="Not Clear", value="NOTCLEAR"),
        discord.app_commands.Choice(name="Favorite", value="FAVORITE"),
        discord.app_commands.Choice(name="Not Favorite", value="NOTFAVORITE")
    ])
    async def song_status(self, interaction: discord.Interaction, song_status: discord.app_commands.Choice[str]):
        await interaction.response.defer()
        
        locale = interaction.locale
        
        if song_status.value not in ["NONE", "FC", "AP", "APP", "CLEAR", "NOTCLEAR", "FAVORITE", "NOTFAVORITE"]:
            await interaction.followup.send(t("unavailable-song-status", locale, song_status=song_status.value), ephemeral=True)
            return
        
        await handle_song(interaction, mode="status", song_status=song_status.value)
    
    @discord.app_commands.command(name="rtr", description="获取指定等级范围歌曲信息")
    @discord.app_commands.describe(song_level_num_min="歌曲等级下限 (数字)", song_level_num_max="歌曲等级上限 (数字)", song_sort_type="歌曲排序类型")
    @discord.app_commands.choices(song_sort_type=[
        discord.app_commands.Choice(name="Rating值", value="rating"),
        discord.app_commands.Choice(name="分数", value="score"),
        discord.app_commands.Choice(name="等级", value="level")
    ])
    async def song_rtr(self, interaction: discord.Interaction, song_level_num_min: str = "12.5", song_level_num_max: str = "1145", song_sort_type: discord.app_commands.Choice[str] = "rating"):
        await interaction.response.defer()
        
        locale = interaction.locale
        
        song_sort_type = choiceValue(getattr(song_sort_type, "value", song_sort_type))
        if song_sort_type.value not in ["rating", "score", "level"]:
            await interaction.followup.send(t("unavailable-song-sort-type", locale, song_sort_type=song_sort_type.value), ephemeral=True)
            return
        
        if not song_level_num_min.replace(".", "", 1).isdigit() or not song_level_num_max.replace(".", "", 1).isdigit():
            await interaction.followup.send(t("invalid-song-level-num-range", locale, song_level_num_range=f"({song_level_num_min}, {song_level_num_max})"), ephemeral=True)
            return
        song_level_num_min = float(song_level_num_min)
        song_level_num_max = float(song_level_num_max)
        await handle_song(interaction, mode="rtr", song_level_num_range=(song_level_num_min, song_level_num_max) if song_level_num_min <= song_level_num_max else (song_level_num_max, song_level_num_min), song_sort_type=song_sort_type.value)

async def handle_login(interaction: discord.Interaction, mode: str, **kwargs):
    user_id = str(interaction.user.id)
    user_name = interaction.user.name
    user_locale = interaction.locale
    
    server_code = kwargs.get("server_code", None)
    object_id = kwargs.get("object_id", None)
    session_token = kwargs.get("session_token", None)
    private_server_url = kwargs.get("private_server_url", None)
    
    if mode == "server":
        if server_code is None:
            await interaction.followup.send(t("please-enter-server-code", user_locale))
            return
        if server_code == "private" and private_server_url is None:
            await interaction.followup.send(t("please-enter-private-server-url", user_locale))
            return
        await update_user_datas(interaction, "serverCode", server_code)
        if server_code == "private" and private_server_url is not None:
            await update_user_datas(interaction, "privateServerURL", private_server_url)
    elif mode == "objectid":
        if object_id is None:
            await interaction.followup.send(t("please-enter-object-id", user_locale))
            return
        await update_user_datas(interaction, "objectID", object_id)
    elif mode == "session":
        if session_token is None:
            await interaction.followup.send(t("please-enter-session-token", user_locale))
            return
        await update_user_datas(interaction, "sessionToken", session_token)
    elif mode == "qrcode":
        if server_code is None:
            await interaction.followup.send(t("please-enter-server-code", user_locale))
            return
        taptap_login = rotaeno.api.taptap_auth.TapTapLogin(server=server_code, device_id=user_id)
        qrcode_data, exec_time_get_qrcode_dataata = await time_calculator_sync(taptap_login.get_qrcode, needImage=True)
        await interaction.followup.send(t("taptap-login-qrcode-has-been-generated-lease-scan-it-within-1-minute-to-log-in", user_locale), file=discord.File(qrcode_data["image"]))
        try:
            login_data, exec_time_get_login_data = await time_calculator_sync(taptap_login.get_objectid_and_sessiontoken, qrcode_data=qrcode_data, show_qrcode=False)
        except TimeoutError:
            await interaction.followup.send(t("login-timed-out-please-retrieve-taptap-login-qrcode-again", user_locale))
            raise TimeoutError("二维码已过期")
        session_token = login_data["sessionToken"]
        object_id = login_data["objectID"]
        await update_user_datas(interaction, "serverCode", server_code, send_message=False)
        await update_user_datas(interaction, "objectID", object_id, send_message=False)
        await update_user_datas(interaction, "sessionToken", session_token, send_message=False)
        await interaction.followup.send(t("binding-successful-function-execution-time", user_locale, exec_time=exec_time_get_qrcode_dataata+exec_time_get_login_data))

async def handle_b40(interaction: discord.Interaction, mode: str, **kwargs):
    user_id = str(interaction.user.id)
    user_name = interaction.user.name
    user_locale = interaction.locale
    
    verified, key = verify_user_data(user_id)
    if not verified:
        await interaction.followup.send(t("rotaeno-account-binding-not-yet-completed", user_locale, message=t(key, user_locale,)))
        return
    
    user_profile = USER_DATAS[user_id]
    user_profile.update({"locale": user_locale})
    
    if mode == "default":
        image_path, exec_time = await time_calculator_sync(rotaeno.processor.get_best40, user_profile)
    
    await interaction.followup.send(t("your-best40-data-has-been-generatedfunction-execution-time", user_locale, exec_time=exec_time), file=discord.File(image_path, filename="image.png"))

async def handle_song(interaction: discord.Interaction, mode: str, **kwargs):
    user_id = str(interaction.user.id)
    user_name = interaction.user.name
    user_locale = interaction.locale
    
    verified, key = verify_user_data(user_id)
    if not verified:
        await interaction.followup.send(t("rotaeno-account-binding-not-yet-completed", user_locale, message=t(key, user_locale)))
        return
    
    user_profile = USER_DATAS[user_id]
    user_profile.update({"locale": user_locale})
    
    song_alias = kwargs.get("song_alias", None)
    if song_alias is not None:
        song_id = rotaeno.database.song_alias.song_alias.get_song_id(song_alias=song_alias)[list(rotaeno.database.song_alias.song_alias.get_song_id(song_alias=song_alias))[0]]
    song_status = kwargs.get("song_status", None)
    song_level_num_range = kwargs.get("song_level_num_range", (12.5, 1145))
    song_sort_type = kwargs.get("song_sort_type", "rating")
    
    if mode == "info":
        image_path, exec_time = await time_calculator_sync(rotaeno.processor.get_song, user_profile, song_id=song_id)
    elif mode == "status":
        image_path, exec_time = await time_calculator_sync(rotaeno.processor.get_song_status, user_profile, song_status=song_status)
    elif mode == "rtr":
        image_path, exec_time = await time_calculator_sync(rotaeno.processor.get_song_rtr, user_profile, song_level_num_range=song_level_num_range, song_sort_type=song_sort_type)
    
    await interaction.followup.send(t("your-song-data-has-been-generatedfunction-execution-time", user_locale, exec_time=exec_time), file=discord.File(image_path, filename="image.png"))

async def handle_on_ready():
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands globally")
    for command in synced:
        print(f"Synced command: {command.name}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await handle_on_ready()

bot.tree.add_command(LoginGroup())
bot.tree.add_command(B40Group())
bot.tree.add_command(SongGroup())

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
