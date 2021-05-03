import discord
from discord.ext import commands,tasks 
from itertools import cycle
import time

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("Woof\serviceKey.json")
firebase_admin.initialize_app(cred)

server_id=""


db = firestore.client()  # this connects to our Firestore database
# collection = db.collection('tasks')  # opens 'tasks' collection


bot = commands.Bot(command_prefix = '$', description="Simple reminder Bot for sending reminders.")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('Baraf Pani'))
    print('Bot is ready')
    

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('```Invalid Command!```')

@bot.command()
async def reminder(ctx, description, date, time): #function to add data to database
    server_id=str(ctx.guild.id)
    res = db.collection(server_id).add(   #add to collection, if does not exist create one
        {
            'description': description,
            'time': time,
            'date': date,
        }
    )
    #print(res)
    await ctx.send('```New reminder added```')

@reminder.error
async def reminder_syntax_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Please pass all argumnets in format "Description" "date" "time" ```')

@tasks.loop(seconds=1)
async def send_reminder(self):
    print(self.index)
    self.index += 1
   

@bot.command()
async def ping(ctx):
    await ctx.send('```Pong!```')
    server_id=str(ctx.guild.id)
    docs = db.collection(server_id).stream()

    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')
        print(docs)

bot.run('ODM3NzYyNzkxMTEyODM1MDgy.YIxRZg.OEHmsuaKoPkriCwy-f8OJb6zciw')
