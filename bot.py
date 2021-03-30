import os
import discord
from discord import member
from dotenv import load_dotenv
from tabulate import tabulate
from discord.ext import commands
from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from datetime import datetime
import logging
import sqlite3

from models import Base, Event, Member, Attendance
#logging.basicConfig(level=logging.INFO)


#logger = logging.getLogger('discord')
#logger.setLevel(logging.DEBUG)
#handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
#handler.setFormatter(logging.Formatter('(%asctime)s:%(levelname)s: %(message)s'))
#logger.addHandler(handler)

engine = create_engine('sqlite:///event-bot.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# Create table if it doesn't exist
#if not engine.dialect.has_table(engine, 'event'):
Base.metadata.create_all(engine)

load_dotenv('.env')

TOKEN = os.getenv('DISCORD_TOKEN')

description = 'A Based Bot'
bot = commands.Bot(command_prefix='?', description=description)
token = TOKEN


bot.remove_command('help')
@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title = 'Help', description = 'Use ?help <command> for extended information on a command')
    em.add_field(name = 'Event Management', value = '`create`,`list`,`attend`, `view`, `delete`')
    em.add_field(name = 'Fun', value = '`cum`')
    await ctx.send(embed=em)

@help.command()
async def create(ctx):
    em = discord.Embed(title = 'Create an Event', description = "Create a scheduled event")
    em.add_field(name ='**Syntax**', value = '?create "Name of Event" [dd/mm/yyy] 0:00pm or am')
    await ctx.send(embed=em)

@help.command()
async def list(ctx):
    em = discord.Embed(title = 'List events', description = "Shows a list with all the events")
    await ctx.send(embed=em)

@help.command()
async def attend(ctx):
    em = discord.Embed(title = 'Attend an event', description = "Confirm attendance for a scheduled event")
    em.add_field(name ='**Syntax**', value = '?attend "Name of Event" ')
    await ctx.send(embed=em)

@help.command()
async def view(ctx):
    em = discord.Embed(title = 'Show event details', description = "Shows information for an event, players attending, total count")
    em.add_field(name ='**Syntax**', value = '?view "Name of Event" ')
    await ctx.send(embed=em)

@help.command()
async def delete(ctx):
    em = discord.Embed(title = 'Delete an event', description = "Delete an event and all the players linked to it")
    em.add_field(name ='**Syntax**', value = '?delete "Name of Event" ')
    await ctx.send(embed=em)

@help.command()
async def cum(ctx):
    em = discord.Embed(title = 'Cum', description = "Make bot cum")
    await ctx.send(embed=em)


@bot.event
async def on_ready():
    print(bot.user.id)
    print(bot.user.name)
    print('---------------')
    print('This bot is ready boyyyyyy')

@bot.command()
@commands.has_permissions(administrator=True)

async def ping(ctx, member: discord.Member=None):
    '''Returns pong when called'''
    if member == None:
        member = ctx.author
    #author = ctx.author
    #server = ctx.guild
    await ctx.send('Pong for {}!'.format(member))
    #await ctx.send('{} arguments: {}'.format(len(args),', '.join(args)))

@bot.command()
@commands.has_any_role('Colonel','Admin Dunkin','Officer','NCO')
async def create(ctx, name:str, date:str, time: str='0:00am'):
    ''' Creates an event with a specified name and date use the following format ?create "1st of Jan Event" 1/1/2021 8:00pm'''
    server = ctx.guild.name
    date_time = '{} {}'.format(date, time)
    try:
        event_date = datetime.strptime(date_time, '%m/%d/%Y %I:%M%p')
        event = Event(name=name, server=server, date=event_date)
        session.add(event)
        session.commit()
        message = 'Event {} created successfully for {}'.format(name,event.date)
        await ctx.send(message)
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)

@bot.command()
@commands.has_any_role('Colonel','Admin Dunkin','Officer','NCO')
async def delete(ctx, name:str):
    ''' Delete an event and the attendance of people related to the event'''
    try:
        event = session.query(Event).filter(Event.name == name).first()
        session.query(Attendance).filter(Attendance.event_id == event.id).delete()      
        #event = Event(name=name)
        session.delete(event)
        session.commit()
        message = 'Event {} deleted successfully'.format(name)
        await ctx.send(message)
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckAnyFailure):
        await ctx.send('You do not have the correct role for this command.')


@bot.command()
async def attend(ctx, name: str):
    '''
    Allows a user to attend an upcoming event
    '''
    author = ctx.author.name
    avatar = ctx.author.avatar_url
    id = ctx.author.id
    try:
        #Counts the number of existing id for a user
        count = session.query(Member).filter(Member.id == id).count()
        event = session.query(Event).filter(Event.name == name).first()
        # Verify this event exists
        if not event:
            await ctx.send('This event does not exist')
            return
        # Create member if they do not exist in the database
        if count < 1:
            member = Member(id=id, name=author)
            session.add(member)
        attending = Attendance(member_id=id, event_id=event.id)
        session.add(attending)
        session.commit()
        message = 'Member {} is now attending event {}'.format(author, name)
        await ctx.send(message)
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)

@bot.command()
async def list(ctx):
    ''' Displays the list of current events
    '''
    try:
        events = session.query(Event).order_by(Event.date).all()
        headers = ['Name', 'Date']
        rows = [[e.name, e.date] for e in events]
        table = tabulate(rows, headers)
        await ctx.send('```\n' + table + '```\n' + '```All times shown are EST```')
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)

@bot.command()
async def view(ctx, name: str):
    '''Displays information about a specific event
    '''
    try:
        event = session.query(Event).filter(Event.name == name).first()
        if not event:
            await ctx.send('This event does not exist')
            return
        join = session.query(Member.name).join(Attendance, Attendance.member_id == Member.id).filter(Attendance.event_id == event.id).all()

        attending_count = session.query(Attendance).filter(Attendance.event_id == event.id).count()

        info = [['Name', event.name], ['Date', event.date], ['Number Attending', attending_count]]
        players_headers= ['Gamers Attending']
        rows = [[a.name] for a in join]
        table = tabulate(rows, players_headers)
        await ctx.send('```\n' + tabulate(info) + '```')
        await ctx.send('```\n' + table + '```')

    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)

@bot.command()
async def cum(ctx):
    '''Make the bot cum'''
    await ctx.send('Camed')


@bot.command()
async def vc_list(ctx):
    channel = ctx.get_channel(394722615337418786)
    curMembers = []
    for member in channel.members:
        curMembers.append(member.name)
    await ctx.send(curMembers)



if __name__ == '__main__':
    try:
        bot.run(TOKEN)
    except Exception as e:
        print('Could not start bot')
        print(e)
    finally:
        print('Closing session')
        session.close()



