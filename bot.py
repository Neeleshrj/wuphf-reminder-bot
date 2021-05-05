from typing import AsyncContextManager
import discord
from discord.ext import commands,tasks 
from timing import diff_timestamp
import threading
import firebase_admin
from firebase_admin import credentials, firestore


cred = credentials.Certificate("./serviceKey.json")
firebase_admin.initialize_app(cred)

server_id=""
reminder_db={}

db = firestore.client()  # this connects to our Firestore database
# collection = db.collection('tasks')  # opens 'tasks' collection


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix = '>', description="Simple reminder Bot for sending regular reminders.",intents=intents)

server_list=[]
reminder_db={}


#events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Your Requests"))
    print('Bot is ready')
    for guild in bot.guilds:
        server_list.append(str(guild.id))
    change_detection()
    check_reminder.start()
   


#functions
def change_detection(): #listener function to check for data changes in firebase
    # Create an Event for notifying main thread.
    callback_done = threading.Event()

    # Create a callback on_snapshot function to capture changes
    def on_snapshot(doc_snapshot, changes, read_time,id):
        reminder_db[id]=[]
        for doc in doc_snapshot:     
            reminder_db[id].append(doc.to_dict())   
        #print(reminder_db)
        callback_done.set()
         
    for id in server_list:
        doc_ref = db.collection(id)
        # Watch the document
        doc_watch = doc_ref.on_snapshot(lambda *args,change_id=id: on_snapshot(*args,change_id))


def delete_database(serv_id):
    docs = db.collection(serv_id).stream()
    for doc in docs:
        if doc.id != 'reminder_channel' and diff_timestamp(doc.to_dict().get("date"),doc.to_dict().get("time")) <=0:
            db.collection(serv_id).document(doc.id).delete()


@tasks.loop(seconds=1) 
async def check_reminder(): #check if reminder is 1 day or 1 hour later and print
    for key,value in reminder_db.items():
        found=False
        delete_it=False  
        for data in value:
            try:                 
                if data['date']:
                    time_differnce = diff_timestamp(data['date'],data['time'])
                    if time_differnce == 86400 or time_differnce == 3600:            
                        found= True
                    elif time_differnce <= 0:
                        delete_it = True
            except Exception:
                pass
            if found:
                #print_reminder(key,data)
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
                #print("value passed to bot")
                found=False    
            elif delete_it:
                print("delete")
                delete_database(key)    

#async def print_reminder(ser_id, data):


#bot commands

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
    await ctx.send('```New reminder added```')


@bot.command()
async def attendance(ctx, channel_name): #function to get all users in a specific voice channel
    for channel in ctx.guild.channels:
        if channel.name == channel_name:
            wanted_channel_id = channel.id

    wanted_channel = bot.get_channel(wanted_channel_id)    
    
    members  = wanted_channel.members
   
    for member in members:
        await ctx.send(member.name)
        #await ctx.send(member)
    

@bot.command()
async def setch(ctx, channel_name): #function to set which channel to send reminders to
    for channel in ctx.guild.channels:
        if channel.name == channel_name:
            wanted_channel_id = channel.id
    server_id=str(ctx.guild.id)
    res = db.collection(server_id).document('reminder_channel').set(
        {
            'channel_id': str(wanted_channel_id)
        }  
    )
    await ctx.send(f'```Reminders are being sent to #{channel_name}```')


@bot.command()
async def creators(ctx):
    embed = discord.Embed(title="Neelesh Ranjan Jha", description="", color=discord.Color.green())
    embed.add_field(name="Github:",value="https://github.com/Neeleshrj")
    embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/57111920?v=4")
    
    await ctx.send(embed=embed)

    embed = discord.Embed(title="Naman Aggarwal", description="", color=discord.Color.blue())
    embed.add_field(name="Github:",value="https://github.com/divinenaman")
    embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/63128054?v=4")
    await ctx.send(embed=embed)     


@bot.command()
async def helpme(ctx):
    embed = discord.Embed(title="All Commands", description="All commands need to be prefixed with >", color=discord.Color.red(),inline=True)
    embed.add_field(name="To set reminder", value=">reminder \"description\" \"dd-mm-yy\" \"hh:mm\"",inline=False)
    embed.add_field(name="To set which channel the reminders should be received",value=">setch channel-name",inline=False)
    embed.add_field(name="To find all users in a voice channel",value=">attendance channel-name",inline=True)
    embed.add_field(name="To know my overlords", value=">creators")
    await ctx.send(embed=embed) 
    

#exception handling
@reminder.error
async def reminder_syntax_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Please pass all argumnets in format "Description" "dd-mm-yy" "HH:MM" ```')

@attendance.error
async def attendance_syntax_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Please enter name of channel you want member list of after command```')

@setch.error
async def set_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Enter name of channel you want to send reminders to after command```')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('```Invalid Command!```')


bot.run('YOUR TOKEN HERE')




#USELESS NOW
# @tasks.loop(seconds=1)
# async def check_reminder(server_list):
#     # for id in server_list:
#     #     docs = db.collection(id).stream()
#     #     reminder_doc = db.collection(id).document('reminder_channel')
#     #     rem_doc = reminder_doc.get()
#     #     if rem_doc.exists:
#     #         chan_id = rem_doc.to_dict().get('channel_id')
#     #         for doc in docs:
#     #             channel=bot.get_channel(int(chan_id))
#     #             if doc.id != 'reminder_channel' and (diff_timestamp(doc.to_dict().get("date"),doc.to_dict().get("time")) == 86400 or diff_timestamp(doc.to_dict().get("date"),doc.to_dict().get("time")) == 3600):
#     #                 embed = discord.Embed(title="R E M I N D E R S !", description="", color=discord.Color.red())
#     #                 embed.add_field(name="Description:",value=f'{doc.to_dict().get("description")}',inline=False)
#     #                 embed.add_field(name="Date:",value=f'{doc.to_dict().get("date")}',inline=True)
#     #                 embed.add_field(name="Time:",value=f'{doc.to_dict().get("time")}',inline=True)    
#     #                 await channel.send(embed=embed)
#     #             elif doc.id != 'reminder_channel' and diff_timestamp(doc.to_dict().get("date"),doc.to_dict().get("time")) <= 0:
#     #                 db.collection(id).document(doc.id).delete()
#     print("")
