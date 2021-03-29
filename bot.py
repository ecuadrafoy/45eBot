import os
import discord
from dotenv import load_dotenv
from tabulate import tabulate
from discord.ext import commands
from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sqlite3

from models import Base, Event, Member, Attendance

engine = create_engine('sqlite:///event-bot.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# Create table if it doesn't exist
#if not engine.dialect.has_table(engine, 'event'):
Base.metadata.create_all(engine)

load_dotenv('.env')

TOKEN = os.getenv('DISCORD_TOKEN')

description = 'A based bot'
bot = commands.Bot(command_prefix='?', description=description)
token = TOKEN

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
    ''' Creates an event with a specified name and date'''
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
        await ctx.send('```\n' + table + '```\n' + 'All times shown are EST')
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
        attending = session.query(Attendance).filter(Attendance.event_id == event.id).count()
        info = [['Name', event.name], ['Date', event.date], ['Number Attending', attending]]
        await ctx.send('```\n' + tabulate(info) + '```')
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)

@bot.command()
async def cum(ctx):
    '''Make the bot cum'''
    await ctx.send('Camed')



if __name__ == '__main__':
    try:
        bot.run(TOKEN)
    except Exception as e:
        print('Could not start bot')
        print(e)
    finally:
        print('Closing session')
        session.close()



