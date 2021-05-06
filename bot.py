import os
import threading
import discord
from discord.ext import commands,tasks
from typing import AsyncContextManager

import firebase_admin
from firebase_admin import credentials, firestore

from utilities.timing import diff_timestamp
from utilities.parser import parse
from dotenv import load_dotenv

# load env vaiables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

cred = credentials.Certificate("./serviceKey.json")
firebase_admin.initialize_app(cred)

server_id=""
server_list=set()
reminder_db={}

# this connects to our Firebase Firestore database
db = firestore.client()  

# input arguments parser
parser = parse()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix = '>', description="Simple reminder Bot for sending regular reminders.",intents=intents)


# event to executed when bot is online
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Your Requests"))
    print('Bot is ready','\n')
    for guild in bot.guilds:
        server_list.add(str(guild.id))
    change_detection()
    check_reminder.start()
   


#listener function to check for data changes in firebase
def change_detection(): 

    # Create an Event for notifying main thread
    callback_done = threading.Event()                                                                                                                                                                                                                                                                                                                                                       

    # Create a callback on_snapshot function to capture changes
    def on_snapshot(doc_snapshot, changes, read_time,id):
        reminder_db[id]=[]
        for doc in doc_snapshot:
            doc_dict = doc.to_dict()
            doc_dict['id'] = doc.id     
            reminder_db[id].append(doc_dict)   
        #print(reminder_db)
        callback_done.set()
         
    for id in server_list:
        doc_ref = db.collection(id)
        # Watch the document
        doc_watch = doc_ref.on_snapshot(lambda *args,change_id=id: on_snapshot(*args,change_id))


def delete_reminder_docs(serv_id,doc_ids):
    for doc_id in doc_ids:
        db.collection(serv_id).document(doc_id).delete()


# check if reminder is due by 1 day or 1 hour
@tasks.loop(seconds=1) 
async def check_reminder(): 
    for key,value in reminder_db.items():
        found=False
        delete_it=[]  
        for data in value:
            try:                 
                if data['date']:
                    time_differnce = diff_timestamp(data['date'],data['time'])
                    if time_differnce == 86400 or time_differnce == 3600 or time_differnce == 1:            
                        found= True
                    
                    elif time_differnce <= 0:
                        delete_it.append(data['id'])     
            
            except Exception:
                pass
            
            if found:
                reminder_doc = db.collection(key).document('reminder_channel')
                rem_doc = reminder_doc.get()
                if rem_doc.exists:
                        chan_id = rem_doc.to_dict().get('channel_id')
                        channel=bot.get_channel(int(chan_id))
                        embed = discord.Embed(title="R E M I N D E R S !", description="", color=discord.Color.red())
                        embed.add_field(name="Description:",value=data['description'],inline=False)
                        embed.add_field(name="Date:",value=data['date'],inline=True)
                        embed.add_field(name="Time:",value=data['time'],inline=True)    
                        await channel.send(embed=embed)             
                found=False

        if len(delete_it) > 0:
            delete_reminder_docs(key,delete_it)    

'''
    bot commands
'''

@bot.command()
async def ping(ctx):
    await ctx.send('```Who has summoned the ancient one?```')


# command to add reminder to database
@bot.command()
async def reminder(ctx, description, date, time): 
    parser.parse_reminder(description,date,time)
    
    server_id=str(ctx.guild.id)

    reminder_doc = db.collection(server_id).document('reminder_channel')
    rem_doc = reminder_doc.get()

     # add a default channel to post reminders
    if not rem_doc.exists:
        found = False
        res = db.collection(server_id).document('reminder_channel').set(
            {
                'channel_id': str(ctx.channel.id)
            }
        )

    # add to collection, if does not exist create one
    res = db.collection(server_id).add(   
        {
            'description': description,
            'time': time,
            'date': date,
        }
    )
    await ctx.send('```New reminder added```')


# command to get all users in a specific voice or text channel
@bot.command()
async def attendance(ctx, channel_name, type_channel="vc"): 
    
    if type_channel == "text":
        channels = ctx.guild.text_channels
    
    elif type_channel == "vc":
        channels = ctx.guild.voice_channels

    found = False
    for channel in channels:
        if channel.name == channel_name:
            wanted_channel_id = channel.id
            found = True

    if not found:
        raise commands.BadArgument(f'{type_channel} Channel:"{channel_name}" not found.Enter a valid channel') 

    wanted_channel = bot.get_channel(wanted_channel_id)    
    
    members  = wanted_channel.members
    if len(members) == 0:
        await ctx.send('```No members found```')
    else:    
        msg = ""
        i = 1
        for member in members:
            msg += f'{i}) {member}' + "\n"
            i+=1
        
        await ctx.send(f'```{msg}```')   


# command to set channel to post reminders
@bot.command()
async def setch(ctx, channel_name): 
    found = False
    for channel in ctx.guild.text_channels:
        if channel.name == channel_name:
            wanted_channel_id = channel.id
            found = True
    
    if not found:
        raise commands.BadArgument(f'Text Channel:"{channel_name}" not found.Enter a valid text channel') 

    server_id=str(ctx.guild.id)
    res = db.collection(server_id).document('reminder_channel').set(
        {
            'channel_id': str(wanted_channel_id)
        }  
    )
    await ctx.send(f'```Reminders are being sent to #{channel_name}```')


# command to know the creators
@bot.command()
async def creators(ctx):
    embed = discord.Embed(title="Neelesh Ranjan Jha", description="", color=discord.Color.green())
    embed.add_field(name="Github:",value="https://github.com/Neeleshrj")
    embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/57111920?v=4")
    
    await ctx.send(embed=embed)

    embed = discord.Embed(title="Naman Agarwal", description="", color=discord.Color.blue())
    embed.add_field(name="Github:",value="https://github.com/divinenaman")
    embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/63128054?v=4")
    await ctx.send(embed=embed)     


# command to fetch a commands help guide
@bot.command()
async def helpme(ctx):
    embed = discord.Embed(title="All Commands", description="All commands need to be prefixed with >", color=discord.Color.red(),inline=True)
    embed.add_field(name="To set reminder", value=">reminder \"description\" \"dd-mm-yy\" \"hh:mm\"",inline=False)
    embed.add_field(name="To set a default channel to post all reminders",value=">setch channel-name",inline=False)
    embed.add_field(name="To find all users in a voice channel",value=">attendance channel-name",inline=False)
    embed.add_field(name="To find all users in a text channel",value=">attendance channel-name \"text\"",inline=False)
    embed.add_field(name="To know my overlords", value=">creators",inline=False)
    await ctx.send(embed=embed) 
    

#exception handling
@reminder.error
async def reminder_syntax_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Please pass all argumnets in format "Description" "dd-mm-yy" "HH:MM" ```')

    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'```{error}```')

@attendance.error
async def attendance_syntax_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Please enter name of channel you want member list of after command```')

    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'```{error}```')
    
@setch.error
async def set_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Enter name of channel you want to send reminders to after command```')

    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'```{error}```')
        
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('```Invalid Command!```')


# the magic starts here
bot.run(BOT_TOKEN)


