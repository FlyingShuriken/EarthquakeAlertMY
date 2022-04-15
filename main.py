import discord
from discord.ext import tasks, commands
import requests
from dotenv import dotenv_values
from loguru import logger

from datetime import datetime
import time

bot = commands.Bot(command_prefix='>')
BOT_TOKEN = dotenv_values(".env")['BOT_TOKEN']
MET_TOKEN = dotenv_values(".env")['MET_TOKEN']
DEFAULT_LANGUAGE = dotenv_values(".env")['DEFAULT_LANGUAGE'] or "en"
if(DEFAULT_LANGUAGE not in ["en","ms"]): DEFAULT_LANGUAGE = "en "
BASE_URL = "https://api.met.gov.my/v2.1/"
ALERT_CHANNEL = bot.get_channel(int(dotenv_values(".env")['ALERT_CHANNEL_ID']))

logger.add("./logs/file_{time}.log", colorize=True, format="<green>{time}</green> <level>{message}</level>")

def Logging(context,type=None,):
    if not type:
        logger.info(f"{context}")
    elif type == "warning":
        logger.warning(f"{context}")


class METRequest:
    def __init__(self, url=BASE_URL, headers={}, cat="WARNING", types="QUAKETSUNAMI" ,date_period=(datetime.now().strftime("%Y-%m-%d"),datetime.now().strftime("%Y-%m-%d"))):
        if headers:
            if "Authorization" in headers.keys():
                pass
            else:
                headers["Authorization"] = f"METToken {MET_TOKEN}"
                pass
        else:
            headers = {"Authorization": f"METToken {MET_TOKEN}"}
        if url.endswith("/v2.1/"):
            url += "data"
            pass
        params = {
            "datasetid": cat,
            "datacategoryid": types,
            "start_date": date_period[0],
            "end_date": date_period[1],
        }
        self.request = requests.get(url, headers=headers, params=params)

    def getJson(self):
        return self.request.json()

    def getMessage(self):
        data = self.getJson()
        obj = MessageEmbed(data["metadata"]["resultset"]["datasetid"],data["metadata"]["resultset"]["datacategoryid"],data)
        self.embedObj = obj
        return obj.getEmbed()

class MessageEmbed:
    def __init__(self,cat,type,data):
        pages = []
        for y in range(len(data["results"])):
            for i in data["results"][y]:
                v = data["results"][y]["date"]
                part = str(v.split("T")[0]).split("-")
                date = datetime(int(part[0]),int(part[1]),int(part[2]))
                today = datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday)
                diff = today - date
                if diff.days < 2:
                    if i == "value":
                        d = data["results"][y][i]
                        if type.upper() == "QUAKETSUNAMI":
                            ttl = d["heading"][DEFAULT_LANGUAGE]
                            ear = d["text"][DEFAULT_LANGUAGE]["earthquake"]
                            tsu = d["text"][DEFAULT_LANGUAGE]["tsunami"]
                            val = f"Earthquake:\n```{ear}```\nTsunami:\n```{tsu}```"
                        else:
                            ttl = d["heading"][DEFAULT_LANGUAGE]
                            war = d["text"][DEFAULT_LANGUAGE]["warning"]
                            val = f"```{war}```"
                        pages.append(discord.Embed(title=f"\u2757\u2757\u2757WARNING\u2757\u2757\u2757\n{ttl}",description=val,color=0xff3300))
        i = 0
        if(pages==[]):
            embed = discord.Embed(title=f"NO WARNING",description="No data under this category",color=0xff3300)
            embed.set_author(name="API/SRC:MetMalaysia",url="https://www.met.gov.my/")
            embed.add_field(name="THIS IS A FORECAST",value="IT MIGHT BE NOT ACCURATE")
            embed.set_footer(text="author:peepoo#4822")
        else:embed = pages[i]
        for abc in pages:
            embed = abc
            embed.set_author(name="API/SRC:MetMalaysia",url="https://www.met.gov.my/")
            embed.add_field(name="THIS IS A FORECAST",value="IT MIGHT BE NOT ACCURATE")
            embed.set_footer(text="author:peepoo#4822")

        self.pages = pages
        self.message = embed
        self.index = 0

    def getEmbed(self):
        return self.message

    def setIndex(self,index):
        if self.index >= len(self.pages):
            self.index = 0
        else:
            self.index = index
        return self.pages[self.index]

@tasks.loop(seconds=10.0)
async def QuakeSensor():
    Logging(f"Task - QuakeSensor")
    req = METRequest()
    message = req.getMessage()
    if req.embedObj.pages == []:
        return
    await ALERT_CHANNEL.send(embed = req.getMessage())

@bot.command()
async def ping(ctx):
    Logging(f"{ctx.author} used command in {ctx.channel.name} - ping")
    await ctx.send('pong')

@bot.command()
async def test(ctx,type="QUAKETSUNAMI"):
    Logging(f"{ctx.author} used command in {ctx.channel.name} - test")
    req = METRequest(type=type)
    message = await ctx.send(embed = req.getMessage())
    # pages = req.embedObj.pages
    # i = req.embedObj.index


@bot.event
async def on_ready():
    Logging(f"Running as {bot.user.name or bot.user.id}")
    QuakeSensor.start()

bot.run(BOT_TOKEN)