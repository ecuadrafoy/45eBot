import os
import discord
import asyncio
from discord.ext.commands.bot import AutoShardedBot
import wikipedia
import pandas as pd
from discord import member
from dotenv import load_dotenv
from sqlalchemy.sql.expression import column
from tabulate import tabulate
from discord.ext import commands
from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from datetime import datetime
from random import randint

from models import Base, DeathList, Event, Member, Attendance, MoonDeath

engine = create_engine('sqlite:///official-db.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# Create table if it doesn't exist
#if not engine.dialect.has_table(engine, 'event'):
Base.metadata.create_all(engine)

load_dotenv('.env')
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.members = True 

description = 'A Based Bot'
bot = commands.Bot(command_prefix='?', description=description ,intents=intents)
token = TOKEN


bot.remove_command('help')
@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title = 'Help', description = 'Use ?help <command> for extended information on a command')
    em.add_field(name = 'Event Management', value = '`create`,`list`,`attend`, `view`, `delete`,`vc`')
    em.add_field(name = 'Wikipedia Search', value = '`wikisearch`,`wikiview`,`wikirandom`')
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
async def vc(ctx):
    em = discord.Embed(title = 'Voice Chat Attendance', description = "Take attendance during a linebattle from A Company directly")
    em.add_field(name ='**Syntax**', value = '?vc "Name of Event" ')
    await ctx.send(embed=em)

@help.command()
async def cum(ctx):
    em = discord.Embed(title = 'Cum', description = "Make bot cum")
    await ctx.send(embed=em)

@help.command()
async def wikisearch(ctx):
    em = discord.Embed(title = 'Wikipedia search', description = "Provide a list of search results from a query on wikipedia")
    em.add_field(name ='**Syntax**', value = '?wikisearch "Search query" ')
    await ctx.send(embed=em)

@help.command()
async def wikiview(ctx):
    em = discord.Embed(title = 'Wikipedia article', description = "Show summary of a wikipedia article from a query")
    em.add_field(name ='**Syntax**', value = '?wikiview "Search query" ')
    await ctx.send(embed=em)

@help.command()
async def wikirandom(ctx):
    em = discord.Embed(title = 'Random Wikipedia article', description = "Show summary of a random wikipedia article")
    em.add_field(name ='**Syntax**', value = '?wikirandom ')
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
async def create(ctx, name:str, date:str, time: str='0:00am', event_type='Holdfast'):
    ''' Creates an event with a specified name and date use the following format ?create "1st of Jan Event" 1/1/2021 8:00pm'''
    server = ctx.guild.name
    name = name.strip()
    date_time = '{} {}'.format(date, time)
    try:
        event_date = datetime.strptime(date_time, '%m/%d/%Y %I:%M%p')
        event = Event(name=name, server=server, date=event_date, event_type=event_type)
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
    name = name.strip()
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
    id = ctx.author.id
    name = name.strip()

    try:
        #Counts the number of existing id for a user
        count = session.query(Member).filter(Member.id == id).count()
        event = session.query(Event).filter(Event.name == name).first()
        #attendance_q = session.query(Attendance).all()
        # Verify this event exists
        if not event:
            await ctx.send('This event does not exist')
            return
        # Create member if they do not exist in the database
        if count < 1:
            member = Member(id=id, name=author)
            session.add(member)
        attending = Attendance(member_id=id, event_id=event.id, member_name=author)
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
        headers = ['Name', 'Date', 'Type']
        rows = [[e.name, e.date, e.event_type] for e in events]
        table = tabulate(rows, headers)
        await ctx.send('```\n' + table + '```\n' + '```All times shown are EST```')
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e)

@bot.command()
async def view(ctx, name: str):
    '''Displays information about a specific event
    '''
    name = name.strip()
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


# https://github.com/Omastto1/VoiceChatPresenceBot/tree/main/src

@bot.command()
@commands.has_any_role('Colonel','Admin Dunkin','Officer','NCO')
async def vc(ctx, name:str):
    get_channel = ctx.author.voice.channel.id
    channel = bot.get_channel(get_channel)
    name = name.strip()
    # Adding new members to the DB if they don't exist
    db_members = pd.read_sql('member', con=engine)
    curMembersID = []
    for member in channel.members:
        curMembersID.append(member.id)
    curMembersName = []
    for member in channel.members:
        curMembersName.append(member.name)
    curMembersNick = []
    for member in channel.members:
        curMembersNick.append(member.nick)
    df = pd.DataFrame(zip(curMembersID, curMembersName),
                      columns = ['id', 'name'], dtype='object')
    mask = ~df.id.isin(db_members.id) #produces a True tag for IDs that are not in the database
    attendance_df = pd.DataFrame({'Gamers Attending':curMembersNick})
    attendance_print = attendance_df.to_string(index=False)
    #Printing the nicknames
    await ctx.send('```\n' + attendance_print +'```')
    df.loc[mask].to_sql('member', con=engine, index=False, if_exists='append')

    #Adding to the Attendance table
    try:
         event = session.query(Event).filter(Event.name == name).first()
         id = event.id
         df = df.assign(event_id=id)
         df.rename(columns={'id':'member_id', 'name':'member_name'}, inplace=True)
         df.to_sql('attendance', con=engine, index=False, if_exists='append')
         message_confirm = '{} members are attending the event {}'.format(len(df), event.name)
         await ctx.send('```' + message_confirm + '```')
         if not event:
             await ctx.send('This event does not exist')
             return
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e) 
         
@bot.command(brief="returns a list of the people in the voice channels in the server",)
async def vcmembers(ctx):
    #First getting the voice channels
    voice_channel_list = ctx.guild.voice_channels
    #getting the members in the voice channel
    for voice_channels in voice_channel_list:
        #list the members if there are any in the voice channel
        if len(voice_channels.members) != 0:
            if len(voice_channels.members) == 1:
                print("{} member in {}".format(len(voice_channels.members), voice_channels.name))
                await ctx.send("{} member in {}".format(len(voice_channels.members), voice_channels.name))
            else:
                await ctx.send("{} members in {}".format(len(voice_channels.members), voice_channels.name))
            for members in voice_channels.members:
                #if user does not have a nickname in the guild, send thier discord name. Otherwise, send thier guild nickname
                if members.nick == None:
                    await ctx.send(members.name)
                else:
                    await ctx.send(members.nick)

@bot.command()
async def killmoon(ctx):
    user = ctx.author
    kill = MoonDeath(member_id=user.id, name=user.nick)
    session.add(kill)
    session.commit()
    death_count = session.query(MoonDeath).count()
    message = '{} has killed Moon. He has died {} times'.format(user.nick, death_count) 
    await ctx.send('```'+ message + '```')

@bot.command()
async def kill(ctx, objective:str):
    user = ctx.author
    try:
        target = session.query(Member).filter(Member.name.contains(objective)).first()
        if not target:
            await ctx.send('Target was not found')
        else:
            kill = DeathList(assassin_id=user.id, assasin_name=user.nick, target_id=target.id, target_name=target.name)
            session.add(kill)
            session.commit()
            death_count = session.query(DeathList).filter(DeathList.target_id == target.id).count()
            message = '{} has killed {}. He has died {} times.' .format(user.nick, target.name, death_count)
            await ctx.send('```'+ message + '```')
    except Exception as e:
        await ctx.send('Could not complete your command')
        print(e) 


# Setting up a Wikipedia search
current_language = 'en'

@bot.command()
async def wikisearch(ctx, query:str):
    global current_language
    e = None
    try:
        wikicontent = wikipedia.search(query, results=20, suggestion=False)
        print(wikicontent)
        #if not results
        if not wikicontent:
            wikicontent = 'Could not find search results for  {}.'.format(query)
            embed = discord.Embed(title = "Wikipedia search results:", color=0xe74c3c, description = wikicontent)
            embed.set_thumbnail(url = 'https://www.wikipedia.org/static/images/project-logos/{}wiki.png'.format(current_language))
            await ctx.send(embed=embed)
        #if there are do
        else:
            embed = discord.Embed(title='Wikipedia search results:', color=0, description="\n".join(wikicontent))
            embed.set_thumbnail(url='https://www.wikipedia.org/static/images/project-logos/{}wiki.png'.format(current_language))
            await ctx.send(embed=embed)
    except Exception as e:
        e = str(e)
        await ctx.send('Sorry a random error occurred. Please try again')
        print(e)

@bot.command()
async def wikiview(ctx, query:str):
    global current_language
    e = None
    try:
        pagecontent = wikipedia.page(query)
        pagetext = wikipedia.summary(query, sentences=5)
        
        try:
            thumbnail = pagecontent.images[randint(0, len(pagecontent.images))]
        except:
            thumbnail = "https://www.wikipedia.org/static/images/project-logos/{}wiki.png".format(current_language)
        embed = discord.Embed(title = query, color = 0, description = pagetext + "\n\n[Read further]({})".format(pagecontent.url))
        embed.set_thumbnail(url=thumbnail)
        await ctx.send(embed=embed)
        
    except wikipedia.DisambiguationError:
        NotSpecificRequestErrorMessage = """Sorry, your search request wasn't specific enough. Please try '/w search (your request)'. This will display all wikipedia articles with your search request. You can than copy the correct result and put that in /a display."""
        embed = discord.Embed(title="Bad request: ", color=0xe74c3c, description=NotSpecificRequestErrorMessage)
        embed.set_thumbnail(url="https://www.wikipedia.org/static/images/project-logos/{}wiki.png".format(current_language))
        await ctx.send(embed=embed)

    except wikipedia.PageError:

        NoResultErrorMessage = "Sorry, there are no Wikipedia articles with this title. Please try '/w search (your request)' to look up Wikipedia article name's"
        embed = discord.Embed(title="Not found: ", color=0xe74c3c, description=NoResultErrorMessage)
        embed.set_thumbnail(url="https://www.wikipedia.org/static/images/project-logos/{}wiki.png".format(current_language))
        await ctx.send(embed=embed)

    except:
        RandomErrorMessage = "Sorry, a random error occured"
        embed = discord.Embed(title="Error", color=0xe74c3c, description=RandomErrorMessage)
        embed.set_thumbnail(url="https://www.wikipedia.org/static/images/project-logos/{}wiki.png".format(current_language))
        await ctx.send(embed=embed)

@bot.command()
async def wikirandom(ctx):

    global current_language

    #Makes sure you will get an article.
    try:
        random_article = wikipedia.random(pages=1)

    except wikipedia.DisambiguationError:
        try:
            random_article = wikipedia.random(pages=1)
        except wikipedia.DisambiguationError:
            try:
                random_article = wikipedia.random(pages=1)
            except wikipedia.DisambiguationError:
                random_article = wikipedia.random(pages=1)
    pagecontent = wikipedia.page(random_article)
    pagetext = wikipedia.summary(random_article, sentences=5)
    #Try to set an random image in the article as the thumbnail
    try:
        thumbnail = pagecontent.images[randint(0, len(pagecontent.images))]
    except Exception as error:
        thumbnail = "https://www.wikipedia.org/static/images/project-logos/{}wiki.png".format(current_language)
        print("Couldn't load {}".format(thumbnail))
    embed = discord.Embed(title=random_article, color=0, description=pagetext + "\n\n[Read further]({})".format(pagecontent.url))
    embed.set_thumbnail(url=thumbnail)
    await ctx.send(embed=embed)
   


if __name__ == '__main__':
    try:
        bot.run(TOKEN)
    except Exception as e:
        print('Could not start bot')
        print(e)
    finally:
        print('Closing session')
        session.close()



