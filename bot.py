from typing import AsyncContextManager
import discord
from discord.ext import commands,tasks 
import datetime

#date-time functions
import datetime

def diff_timestamp(date,time):
    timestamp1 = datetime.datetime.now().timestamp()
    timestamp2 = datetime.datetime.strptime(date+" "+time,"%d-%m-%y %H:%M")
    timestamp2 = datetime.datetime.timestamp(timestamp2)
    diff = timestamp2 - timestamp1
    return int(diff)

# d1 = "05-05-21"
# t1 = "21:28"
# ts1 = diff_timestamp(d1,t1)
# print(int(ts1))



import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("./serviceKey.json")
firebase_admin.initialize_app(cred)

server_id=""


db = firestore.client()  # this connects to our Firestore database
# collection = db.collection('tasks')  # opens 'tasks' collection


bot = commands.Bot(command_prefix = '>', description="Simple reminder Bot for sending reminders.")

server_list=[]

   
@bot.command()
async def ping(ctx):
    await ctx.send('```Pong!```')


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


@tasks.loop(seconds=1)
async def check_reminder(server_list):
    for id in server_list:
        docs = db.collection(id).stream()
        reminder_doc = db.collection(id).document('reminder_channel')
        rem_doc = reminder_doc.get()
        if rem_doc.exists:
            chan_id = rem_doc.to_dict().get('channel_id')
            for doc in docs:
                channel=bot.get_channel(int(chan_id))
                if doc.id != 'reminder_channel' and (diff_timestamp(doc.to_dict().get("date"),doc.to_dict().get("time")) == 86400 or diff_timestamp(doc.to_dict().get("date"),doc.to_dict().get("time")) == 3600):
                    embed = discord.Embed(title="R E M I N D E R S !", description="", color=discord.Color.red())
                    embed.add_field(name="Description:",value=f'{doc.to_dict().get("description")}',inline=False)
                    embed.add_field(name="Date:",value=f'{doc.to_dict().get("date")}',inline=True)
                    embed.add_field(name="Time:",value=f'{doc.to_dict().get("time")}',inline=True)    
                    await channel.send(embed=embed)
                
    #print("bruh")


@bot.command()
async def setch(ctx, channel_name):
    for channel in ctx.guild.channels:
        if channel.name == channel_name:
            wanted_channel_id = channel.id
    server_id=str(ctx.guild.id)
    res = db.collection(server_id).document('reminder_channel').set(
        {
            'channel_id': str(wanted_channel_id)
        }  
    )

#events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('Baraf Pani'))
    print('Bot is ready')
    for guild in bot.guilds:
        server_list.append(str(guild.id))
    check_reminder.start(server_list)
 

 #exception handling
@reminder.error
async def reminder_syntax_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Please pass all argumnets in format "Description" "date" "time" ```')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('```Invalid Command!```')


bot.run('ODM3NzYyNzkxMTEyODM1MDgy.YIxRZg.OEHmsuaKoPkriCwy-f8OJb6zciw')


