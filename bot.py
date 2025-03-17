from bs4 import BeautifulSoup
from datetime import datetime
from discord.ext import commands
import requests
import re
import discord
import random
import os
import sys

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="TIH.", intents=intents)
intents.message_content = True
TIH_role = "TIH ping"

@bot.event
async def on_ready():
    try:
        print(f"logged in as {bot.user}")
        await bot.change_presence(activity=discord.Game(name="Browsing History"))
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await get_events(channel)
            await get_events(bot.get_channel(1350208090707853535))
        sys.exit()
        else:
            print(f"Channel with ID {CHANNEL_ID} not found.")

    except Exception as e:
        print(f"command sync error: {e}")

async def get_events(channel):
    role_name = TIH_role

    try:
        guild = channel.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            await channel.send(f"Role '{role_name}' not found.")
            return

        class Context:
            def __init__(self, channel, guild, author, roles):
                self.channel = channel
                self.guild = guild
                self.author = author
            async def send(self, message):
                await self.channel.send(message)

        author = guild.me
        ctx = Context(channel, guild, author, author.roles)

        today = datetime.today()
        formatted_today = today.strftime("%B/%d")
        formatted_today = formatted_today.replace(f"/0{today.day}", f"/{today.day}")

        scrapable = requests.get("https://www.onthisday.com/events/" + formatted_today)
        soup = BeautifulSoup(scrapable.text, "html.parser")

        event_lists = soup.find_all("ul", class_="event-list")

        output_list = []
        formatted_today_2 = today.strftime("%B %d")
        formatted_today_2 = formatted_today_2.replace(f"/0{today.day}", f"/{today.day}")
        output_string = "# Today in History: " + formatted_today_2 + "\n"

        for event_list in event_lists:
            events = event_list.find_all("li", class_="event")

            for event in events:
                date_tag = event.find("a", class_="date")

                if date_tag:
                    year = date_tag.text.strip()
                    description = event.text.strip().replace(year, "").strip()
                    if ('BC' in year):
                        year = year.replace(' BC', "")
                        description = 'BC ' + description
                    output_list.append(f"{year} - {description}")
                else:
                    event_text = event.text.strip()
                    match = re.match(r"(\S+)", event_text)

                    if match:
                        year = match.group(1)
                        description = event_text.replace(year, "").strip()
                        output_list.append(f"{year} - {description}")
                    else:
                        output_list.append(f"Missing date for event: {event_text}")
        
        output_list.sort(key=lambda x: int(x.split(' - ')[0]))
        random_events = random.sample(output_list, min(10, len(output_list)))
        random_events.sort(key=lambda x: int(x.split(' - ')[0]))

        for event in random_events:
            output_string += event + "\n\n"
            if (' - BC ' in event):
                event.replace('BC', "", 1)
                event.replace(' - ', ' BC - ', 1)
        await ctx.send(output_string)
        await channel.send(discord.utils.get(guild.roles, name = role_name).mention)
    except Exception as e:
        tb = sys.exc_info()[2]
        traceback_info = traceback.extract_tb(tb)
        filename, line_number, function_name, text = traceback_info[-1]
        await channel.send(f"Error occurred in file: {filename}, line: {line_number}, function: {function_name}\nError: {e}")

bot.run(TOKEN)
