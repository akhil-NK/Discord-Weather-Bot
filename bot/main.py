import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import weatherData as wd
import asyncio
import time
import csv

global ZIPCODE

with open("bot/zipcode.txt", "r", encoding="utf-8") as file:
    ZIPCODE = file.read(5)




load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log',encoding='utf-8',mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!",intents = intents)

#getting all the data for the weather.


_cache = {"data": None, "fetched": 0}

async def getData():
    return await asyncio.to_thread(wd.getCachedData, ZIPCODE)

@bot.event
async def on_ready():
    print(f"WE are ready to go, {bot.user.name}")




@bot.event
async def on_member_join(member):
    await member.send(f"Welcome {member}")




@bot.command()
async def hello(ctx):
    await ctx.send(f"HELLO {ctx.author.mention}")

@bot.command()
async def summary(ctx):
    data = await getData()
    if data is None:
        await ctx.send("Couldn't get the weather right now.")
        return
    summary = wd.daySummary(data)
    await ctx.send(f"{ctx.author.mention} {summary}")

@bot.command()
async def rain(ctx):
    data = await getData()
    if data is None:
        await ctx.send("Couldn't get the weather right now.")
        return
    rain = wd.rainChance(data)
    await ctx.send(f"{ctx.author.mention} Chance of Rain is {rain}")

@bot.command()
async def snow(ctx):
    data = await getData()
    if data is None:
        await ctx.send("Couldn't get the weather right now.")
        return
    snow = wd.snowChance(data)
    await ctx.send(f"{ctx.author.mention} Chance of Snow is {snow}")

@bot.command()
async def extremes(ctx):
    data = await getData()
    if data is None:
        await ctx.send("Couldn't get the weather right now.")
        return
    extremes = wd.extremeTemps(data)
    await ctx.send(f"{ctx.author.mention} Low of {extremes["low"]} and High of {extremes["high"]}")

@bot.command()
async def now(ctx):
    data = await getData()
    nowdata = wd.weatherNow(data)
    if data is None:
        await ctx.send("Couldn't get the weather right now.")
        return
    await ctx.send(f"{ctx.author.mention} {nowdata}")

@bot.command()
async def getZipcode(ctx):
    await ctx.send(f"{ctx.author.mention} Zipcode : {ZIPCODE}")

@bot.command(name = "commands")
async def Commands(ctx):
    await ctx.send(f"{ctx.author.mention} LIST OF COMMANDS")
    #yet to complete

@bot.command()
async def setZipcode(ctx,new_zip):
    if(new_zip.isdigit() and len(new_zip)==5):
        ZIPCODE = new_zip
        with open("bot/zipcode.txt", "w", encoding="utf-8") as file:
            file.write(new_zip)
        await ctx.send(f"{ctx.author.mention} ZIPCODE {new_zip} ACCEPTED")

    else:
        await ctx.send(f"{ctx.author.mention} INVALID ZIPCODE")

@bot.command()
async def addJacket(ctx, jacket: str, temp_min: int, temp_max: int):
    if temp_min > temp_max or temp_max > 134 or temp_min < -27:
        await ctx.send(f"{ctx.author.mention} INVALID VALUES")
        return
    with open("jackets.csv", mode="a", newline="") as f:
        csv.writer(f).writerow([ctx.author.id, jacket, temp_min, temp_max])
    await ctx.send(f"{ctx.author.mention} [ {jacket} {temp_min} {temp_max} ] Added")

@addJacket.error
async def addJacket_error(ctx, error):
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send(f'{ctx.author.mention} Usage: `!addJacket "<name>" <min_temp> <max_temp>` (temps must be whole numbers)')
    else:
        raise error


@bot.command()
async def viewJackets(ctx):
    try:
        with open("jackets.csv", mode="r", newline="") as f:
            rows = [r for r in csv.reader(f) if r and r[0] == str(ctx.author.id)]
    except FileNotFoundError:
        rows = []

    if not rows:
        await ctx.send(f"{ctx.author.mention} You haven't added any jackets yet. Use `!addJacket`.")
        return

    lines = [f"**{name}**: {tmin}° to {tmax}°" for _, name, tmin, tmax in rows]
    await ctx.send(f"{ctx.author.mention} Your jackets:\n" + "\n".join(lines))


@bot.command()
async def removeJacket(ctx, jacket:str):
        try:
            with open("jackets.csv", mode="r", newline="") as f:
                rows = [r for r in csv.reader(f) if r]
        except FileNotFoundError:
            rows = []

        uid = str(ctx.author.id)
        if not any(r[0] == uid for r in rows):
            await ctx.send(f"{ctx.author.mention} You haven't added any jackets yet. Use `!addJacket`.")
            return

        correct = None
        
        for i in range(len(rows)):
            if rows[i][1].lower() == jacket.lower() and rows[i][0]==uid:
                correct = rows[i]
                break

        if correct == None:
            await ctx.send(f"{ctx.author.mention} {jacket.title()} is not present.")
            return

        rows.remove(correct)
        with open("jackets.csv", mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        await ctx.send(f"{ctx.author.mention} {jacket.title()} Removed.")
            

def loadJackets(user_id):
    try:
        with open("jackets.csv", mode="r", newline="") as f:
            return [
                (r[1], int(r[2]), int(r[3]))
                for r in csv.reader(f)
                if r and r[0] == str(user_id)
            ]
    except FileNotFoundError:
        return []


def pickJacket(jackets, temp):
    fits = [j for j in jackets if j[1] <= temp <= j[2]]
    if not fits:
        return None
    return min(fits, key=lambda j: abs((j[1] + j[2]) / 2 - temp))


@bot.command()
async def recommend(ctx):
    data = await getData()
    if data is None:
        await ctx.send("Couldn't get the weather right now.")
        return

    jackets = loadJackets(ctx.author.id)
    if not jackets:
        await ctx.send(f"{ctx.author.mention} You haven't added any jackets yet. Use `!addJacket`.")
        return

    ex = wd.extremeTemps(data)
    low, high = float(ex['low']), float(ex['high'])

    morning = pickJacket(jackets, low)
    afternoon = pickJacket(jackets, high)

    if morning is None and afternoon is None:
        msg = f"None of your jackets cover today's range ({low}° to {high}°). Try `!addJacket`."
    elif morning == afternoon:
        msg = f"Wear your **{morning[0]}** today (low {low}°, high {high}°)."
    else:
        parts = []
        if morning:
            parts.append(f"**{morning[0]}** for the morning ({low}°)")
        else:
            parts.append(f"no jacket covers the morning low ({low}°)")
        if afternoon:
            parts.append(f"**{afternoon[0]}** for the afternoon ({high}°)")
        else:
            parts.append(f"no jacket covers the afternoon high ({high}°)")
        msg = "Today: " + ", ".join(parts) + "."

    await ctx.send(f"{ctx.author.mention} {msg}")


        




bot.run(token, log_handler = handler,log_level=logging.DEBUG)