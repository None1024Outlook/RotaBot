import time
import json
import utils
import config
import asyncio
import rotaeno
import discord
from typing import List
import discord.ext.commands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = discord.ext.commands.Bot(commands_prefix="/", intents=intents)
SERVER_CODE = [
    discord.app_commands.Choice(name="国服", value="gf"),
    discord.app_commands.Choice(name="国际服", value="wf"),
    discord.app_commands.Choice(name="本地存档", value="local")
]
SERVER_CODE_TEXT = ["gf", "wf", "local"]

async def timeCalculatorAsync(func, *args, **kwargs):
    start_time = time.time()
    result = await asyncio.to_thread(func, *args, **kwargs)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return result, round(elapsed_time, 2)

def getUserData(userID: str = None, all: bool = False) -> dict:
    userDatas = json.load(open(config.USER_DATA_FILE, "r", encoding="utf-8"))
    if all: return userDatas
    return userDatas.get(userID, {})

def getSongInfo(songID: str) -> dict:
    return utils.songData.getSong(songID)

async def songAliasAutocomplete(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
    fit = 80
    while fit > 0:
        results = utils.songAlias.getSongID(songAlias=current, fit=fit)
        if len(results) != 0: break
        fit -= 5
    return [
        discord.app_commands.Choice(name=alias, value=alias)
        for alias in list(results.keys())[:10]
    ]

class choiceValue:
    def __init__(self, value):
        self.value = value

def saveUserData(data) -> None:
    json.dump(data, open(config.USER_DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

def verifyUserData(userID: str, requiredKeys: list = config.VERIFY_USER_DATA_DEFAULT_REQURIED_KEYS) -> dict:
    userData = getUserData(userID)
    if userData != {}:
        result = {"verify": True}
        for key in requiredKeys:
            if userData.get(key, None) is None:
                return {"verify": False, "key": key}
            result[key] = userData.get(key)
        return result
    return {"verify": False, "key": None}

def updateUserData(userID: str, key: str, value) -> None:
    userData = getUserData(userID)
    userData[key] = value
    data = getUserData(all=True)
    data[userID] = userData
    saveUserData(data)

class LoginGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="login", description="登录Rotaeno账户")
    
    @discord.app_commands.command(name="server", description="设置登录服务器代码")
    @discord.app_commands.describe(server_code="服务器代码")
    @discord.app_commands.choices(server_code=SERVER_CODE)
    async def login_server(self, interaction: discord.Interaction, server_code: discord.app_commands.Choice[str]):
        await interaction.response.defer(thinking=True)
        server_code = choiceValue(getattr(server_code, "value", server_code))
        
        if server_code.value not in SERVER_CODE_TEXT:
            await interaction.followup.send(f"不可用服务器代码 `{server_code.value}`", ephemeral=True)
            return

        await self.handle_login(interaction, mode="server", serverCode=server_code.value)

    @discord.app_commands.command(name="objectid", description="设置objectID")
    @discord.app_commands.describe(object_id="objectID")
    async def login_objectid(self, interaction: discord.Interaction, object_id: str):
        await interaction.response.defer(thinking=True)
        
        await self.handle_login(interaction, mode="objectid", objectID=object_id)

    @discord.app_commands.command(name="session", description="设置sessionToken")
    @discord.app_commands.describe(session_token="sessionToken")
    async def login_session(self, interaction: discord.Interaction, session_token: str):
        await interaction.response.defer(thinking=True)

        await self.handle_login(interaction, mode="session", sessionToken=session_token)
        
    async def handle_login(interaction: discord.Interaction, mode: str, **kwargs):
        userID = str(interaction.user.id)
        
        serverCode = kwargs.get(serverCode, None)
        objectID = kwargs.get(objectID, None)
        sessionToken = kwargs.get(sessionToken, None)
        
        if mode == "server":
            updateUserData(userID, "server", serverCode)
            verifyInfo = verifyUserData(userID)
            if not verifyInfo["verify"]:
                await interaction.followup.send(f"还缺少 `{verifyInfo['key']}`")
                return
        elif mode == "objectid":
            updateUserData(userID, "objectID", objectID)
            verifyInfo = verifyUserData(userID)
            if not verifyInfo["verify"]:
                await interaction.followup.send(f"还缺少 `{verifyInfo['key']}`")
                return
        elif mode == "session":
            updateUserData(userID, "sessionToken", sessionToken)
            verifyInfo = verifyUserData(userID)
            if not verifyInfo["verify"]:
                await interaction.followup.send(f"还缺少 `{verifyInfo['key']}`")
                return
        await interaction.followup.send(f"登录成功")    

class B40Group(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="b40", description="Best40相关")

    @discord.app_commands.command(name="default", description="生成Best40数据(普通)")
    async def b40_default(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        await self.handle_b40(interaction, mode="default")
    
    async def handle_b40(interaction: discord.Interaction, mode: str, **kwargs):
        userID = str(interaction.user.id)
        verifyInfo = verifyUserData(userID)
        if not verifyInfo["verify"]:
            await interaction.followup.send(f"请先绑定Rotaeno账户")
            return
        
        if mode == "default":
            imagePath, execTime = await timeCalculatorAsync(rotaeno.getBest40, getUserData(userID), needCharacter=False)
        await interaction.followup.send(f"你的 Best 40 数据已生成 | 函数用时: {execTime}秒", file=discord.File(imagePath))

bot.tree.add_command(LoginGroup())
bot.tree.add_command(B40Group())
bot.run("Your Discord Bot Token")
