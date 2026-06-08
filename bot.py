from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatCommand
from twitchAPI.chat.middleware import BaseCommandMiddleware, StreamerOnly
from typing import Callable, Optional, Awaitable
from configparser import ConfigParser
from datetime import datetime
from time import time
import random
import asyncio
import json

# Setup
config = ConfigParser()
config.read('config.ini')
APP_ID = config['auth']['clientID']
APP_SECRET = config['auth']['clientSecret']
TARGET_CHANNEL = config['setup']['targetChannel']
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

"""
Custom middleware class that allows a command to be executed if the calling 
user is a moderator or the streamer.
"""
class ModeratorOnlyMiddleware(BaseCommandMiddleware):

    def __init__(self, execute_blocked_handler: Optional[Callable[[ChatCommand], Awaitable[None]]] = None):
        self.execute_blocked_handler = execute_blocked_handler

    async def can_execute(self, cmd: ChatCommand) -> bool:
        return cmd.user.mod or (cmd.user.display_name.lower() == TARGET_CHANNEL.lower())
    
    async def was_executed(self, cmd: ChatCommand):
        pass

"""
Main class for Twitch chat bot functionality.
"""
class TwitchBot:

    def __init__(self):
        self.data = {}
        self.activeUsers = []
        self.redeemLastUsage = {}
        self.reservedCommands = []

    """
    Returns False if any data is in the customCommands/quotes/points sections 
    of the data json in memory, and True otherwise. Used to prevent accidentally 
    writing an empty data object to the data.json file.
    """
    async def data_is_empty(self):
        if('customCommands' in self.data and self.data['customCommands']):
            return False
        if('quotes' in self.data and self.data['quotes']):
            return False
        if('points' in self.data and self.data['points']):
            return False
        return True

    """
    Loads the contents of data.json into memory; used at startup. 
    If the file does not exist or cannot be read; initializes a data 
    object with no data in it.
    """
    async def load_data(self):
        try:
            with open('data.json', 'r') as file:
                self.data = json.loads(file.read())
                if('customCommands' not in self.data):
                    self.data['customCommands'] = {}
                if('quotes' not in self.data):
                    self.data['quotes'] = []
                if('points' not in self.data):
                    self.data['points'] = {}
        except:
            self.data = {
                'customCommands': {},
                'quotes': [],
                'points': {}
            }
            with open('data.json', 'x') as file:
                file.write(json.dumps(self.data, indent=4))

    """
    Saves the contents of the data object to data.json; used whenever 
    the contents of the data object in memory changes.
    """
    async def save_data(self):
        # Sanity check - If data is empty, then don't write it out, in case something went 
        # horribly wrong during initialization, to prevent data loss
        if(await self.data_is_empty()):
            return
        # Sort the point list (Python dicts are ordered)
        self.data['points'] = dict(sorted(self.data['points'].items(), key=lambda item: item[1], reverse=True))
        try:
            with open('data.json', 'w') as file:
                file.write(json.dumps(self.data, indent=4))
        except Exception as e:
            print('ERROR: Could not save data.json!', e)

    """
    Joins the target channel and sends a test message.
    """
    async def on_ready(self, ready_event: EventData):
        print('Connecting to Twitch channel...')
        await ready_event.chat.join_room(TARGET_CHANNEL)
        await ready_event.chat.send_message(TARGET_CHANNEL, 'Bot is connected!')
        print('Successfully connected to Twitch channel: ' + TARGET_CHANNEL)

    """
    Prints the message and adds the sending user to the list of users 
    who were active in the activity window for point rewards. Also 
    checks to see if the message is calling a custom command.
    """
    async def on_message(self, msg: ChatMessage):
        print(f'Message from {msg.user.name}: {msg.text}')
        if(msg.user.display_name.lower() not in self.activeUsers):
            self.activeUsers.append(msg.user.display_name.lower())
        await self.handle_custom_commands(msg)

    """
    Usage: `!addcom <commandName> <responseText>`
    Example: `!addcom mycommandname Response text!`
    Adds a custom command so that any user can type `!mycommandname`, and 
    the bot will reply with "Response text!".
    """
    async def add_custom_command(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'customCommands')):
            return
        if len(cmd.parameter) == 0:
            await cmd.reply('Missing command name')
            return
        if(len(cmd.parameter.split(' ')) < 2):
            await cmd.reply('Missing reply text')
            return
        commandName = cmd.parameter.split(' ')[0].lower()
        if(commandName[0] != '!'):
            commandName = '!' + commandName
        commandReplyText = " ".join(cmd.parameter.split(' ')[1:])
        if(commandName in self.reservedCommands):
            await cmd.reply('Command name is a reserved name; use a different command name')
            return
        if(commandName in self.data['customCommands']):
            await cmd.reply('Command already exists; use !editcom to edit it or !removecom to remove it')
            return
        self.data['customCommands'][commandName] = commandReplyText
        await self.save_data()
        await cmd.reply(f'Successfully added command: {commandName}')

    """
    Usage: `!editcom <commandName> <newResponseText>`
    Example: `!editcom mycommandname New response text!`
    Changes the response text on a custom command.
    """
    async def edit_custom_command(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'customCommands')):
            return
        if len(cmd.parameter) == 0:
            await cmd.reply('Missing command name')
            return
        if(len(cmd.parameter.split(' ')) < 2):
            await cmd.reply('Missing reply text')
            return
        commandName = cmd.parameter.split(' ')[0].lower()
        if(commandName[0] != '!'):
            commandName = '!' + commandName
        commandReplyText = " ".join(cmd.parameter.split(' ')[1:])
        if(commandName not in self.data['customCommands']):
            await cmd.reply('Command does not exist; use !addcom to create it')
            return
        self.data['customCommands'][commandName] = commandReplyText
        await self.save_data()
        await cmd.reply(f'Successfully edited command: {commandName}')
    
    """
    Usage: `!removecom <commandName>`
    Example: `!removecom mycommandname`
    Removes a custom command.
    """
    async def remove_custom_command(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'customCommands')):
            return
        if len(cmd.parameter) == 0:
            await cmd.reply('Missing command name')
            return
        commandName = cmd.parameter.lower()
        if(commandName[0] != '!'):
            commandName = '!' + commandName
        if(commandName not in self.data['customCommands']):
            await cmd.reply('Command does not exist; use !addcom to create it')
            return
        del self.data['customCommands'][commandName]
        await self.save_data()
        await cmd.reply(f'Successfully removed command: {commandName}')
    
    """
    Helper function to see if the message is calling a custom command, 
    and if so, replies with the result text.
    """
    async def handle_custom_commands(self, msg: ChatMessage):
        if(not config.getboolean('featuresEnabled', 'customCommands')):
            return
        commandName = msg.text.split(' ')[0].lower()
        if(commandName in self.data['customCommands']):
            await msg.reply(self.data['customCommands'][commandName])
    
    """
    Usage: `!addquote <quoteText>`
    Example: `!addquote This is the quote text!`
    Adds a quote to the list, appending the date and current game on the stream 
    to the end.
    """
    async def add_quote(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'quotes')):
            return
        date = datetime.today().strftime('%Y-%m-%d')
        gameName = (await self.chat.twitch.get_channel_information(cmd.room.room_id))[0].game_name
        quoteText = f'{cmd.parameter} | {date} | {gameName}'
        self.data['quotes'].append(quoteText)
        await self.save_data()
        await cmd.reply(f'Added quote #{len(self.data['quotes'])}: {quoteText}')

    """
    Usage: `!addquote <index>`
    Example: `!removequote 4`
    Sets the quote with the given index (1-indexed) to "<removed>", which causes it to not be 
    selected as a quote with the !quote command. We do this instead of actually removing it 
    so that future indices are preserved (e.g. if someone removes quote 5, then quote 10 is still 
    quote 10).
    """
    async def remove_quote(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'quotes')):
            return
        try:
            index = int(cmd.parameter)
            if(index < 1 or index > len(self.data['quotes']) or self.data['quotes'][index - 1] == '<removed>'):
                await cmd.reply('A quote does not exist with that index')
                return
            self.data['quotes'][index - 1] = '<removed>'
            await self.save_data()
            await cmd.reply(f'Removed quote #{index}')
        except ValueError:
            await cmd.reply('Quote index must be a number')

    """
    Multiple forms of usage.

    Usage: `!quote`
    Example: `!quote`
    Replies with a random non-removed quote.

    Usage: `!quote <index>`
    Example: `!quote 4`
    Replies with the quote at the given index (1-indexed), provided 
    the quote exists and is not removed.

    Usage: `!quote <keyword>`
    Example: `!quote mykeyword`
    Replies with a random non-removed quote that has the given keyword 
    as a substring.
    """
    async def get_quote(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'quotes')):
            return
        # Check to make sure there is at least one non-removed quote
        noQuotes = True
        for quote in self.data['quotes']:
            if(quote != '<removed>'):
                noQuotes = False
                break
        if(noQuotes):
            await cmd.reply('There are no quotes yet!')
            return
        if(len(cmd.parameter) == 0):
            # !quote - Get a random quote
            index = -1
            quote = None
            while(quote == None):
                index = random.randint(0, len(self.data['quotes']) - 1)
                if(self.data['quotes'][index] != '<removed>'):
                    quote = self.data['quotes'][index]
            await cmd.reply(f'Quote #{index + 1}: {self.data['quotes'][index]}')
            return
        try:
            index = int(cmd.parameter)
            # !quote <index> - Get the quote at the given index
            if(index < 1 or index > len(self.data['quotes']) or self.data['quotes'][index - 1] == '<removed>'):
                await cmd.reply('A quote does not exist with that index')
                return
            await cmd.reply(f'Quote #{len(self.data['quotes'])}: {self.data['quotes'][index - 1]}')
        except ValueError:
            # !quote <keyword> - Get a random quote containing the keyword as a substring
            keyword = cmd.parameter
            matchingQuotes = []
            for quote in self.data['quotes']:
                if(quote != '<removed>' and keyword.lower() in quote.lower()):
                    matchingQuotes.append(quote)
            if(len(matchingQuotes) == 0):
                await cmd.reply('No quotes match that keyword!')
                return
            indexInMatchingQuotes = random.randint(0, len(matchingQuotes) - 1)
            quote = matchingQuotes[indexInMatchingQuotes]
            index = 0
            for q in self.data['quotes']:
                if (q == quote):
                    break
                index += 1
            await cmd.reply(f'Quote #{index + 1}: {quote}')

    """
    Usage: `!points`
    Example: `!points`
    Replies with the number of points that the calling user has.
    """
    async def get_points(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'points')):
            return
        points = 0
        if(cmd.user.display_name.lower() in self.data['points']):
            points = self.data['points'][cmd.user.display_name.lower()]
        message = f'{cmd.user.display_name} has {points} points'
        if(points == 1):
            message = message[0:len(message - 1)] # "1 points" -> "1 point"
        await cmd.reply(message)

    """
    Usage: `!leaderboard`
    Example: `!leaderboard`
    Replies with a list of the top 10 users by points.
    """
    async def get_points_leaderboard(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'points')):
            return
        print('got here')
        topTenNames = list(self.data['points'].keys())[0:10]
        message = ""
        for name in topTenNames:
            message += f'{name} ({self.data['points'][name]}) | '
        message = message[0:len(message) - 3] # Remove trailing space-pipe-space
        await cmd.reply(message)

    """
    Usage: `!addpoints <username> <amount>`
    Example: `!addpoints theemkay 100`
    Adds the given number of points to the given user. Only 
    usable by the streamer.
    """
    async def add_points(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'points')):
            return
        try:
            if(' ' not in cmd.parameter):
                await cmd.reply('Missing number of points')
                return
            user = cmd.parameter.split(' ')[0].lower()
            if(user[0]) == '@':
                user = user[1:] # Remove leading @ symbol
            pointsToAdd = int(cmd.parameter.split(' ')[1])
            if(user not in self.data['points']):
                await cmd.reply(f'{user} is not in the points list')
                return
            self.data['points'][user] += pointsToAdd
            await self.save_data()
            await cmd.reply(f'{user} has gained {pointsToAdd} points and now has a total of {self.data['points'][user]}')
        except ValueError:
            await cmd.reply('Number of points must be a number')
    
    """
    Usage: `!redeem <redeemName>`
    Example: `!redeem stretch`
    Checks that the user has enough points and that the redeem 
    is not on cooldown, and then deducts the cost from the user's 
    points, and replies with a confirmation message.
    """
    async def redeem_points(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'points')):
            return
        if(len(cmd.parameter) == 0):
            await cmd.reply('Missing redeem name')
            return
        redeem = cmd.parameter.lower()
        if(redeem not in config['redeemCosts']):
            await cmd.reply('There is no redeem with that name')
            return
        if(cmd.user.display_name.lower() != TARGET_CHANNEL.lower()): # Skip cooldown and point stuff if it's the streamer
            if(redeem in config['redeemCooldowns'] and redeem in self.redeemLastUsage):
                secondsSinceLastUsage = int(time()) - self.redeemLastUsage[redeem]
                cooldown = config.getint('redeemCooldowns', redeem)
                if(secondsSinceLastUsage < cooldown):
                    await cmd.reply(f'That redeem is still on cooldown for {cooldown - secondsSinceLastUsage} more seconds')
                    return
            self.redeemLastUsage[redeem] = int(time())
            cost = config.getint('redeemCosts', redeem)
            currentPoints = 0
            if(cmd.user.display_name.lower() in self.data['points']):
                currentPoints = self.data['points'][cmd.user.display_name.lower()]
            if(cost > currentPoints):
                await cmd.reply(f'That redeem costs {cost} points, and you only have {currentPoints}')
                return
            self.data['points'][cmd.user.display_name.lower()] -= cost
            await self.save_data()
        await cmd.reply(f'{cmd.user.display_name} has redeemed {redeem} and now has {self.data['points'][cmd.user.display_name.lower()]} points!')

    """
    Usage: `!redeems`
    Example: `!redeems`
    Replies with a list of redeems and costs.
    """
    async def get_redeems(self, cmd: ChatCommand):
        if(not config.getboolean('featuresEnabled', 'points')):
            return
        message = ''
        for redeem in config['redeemCosts']:
            message += f'{redeem} ({config['redeemCosts'][redeem]}) | '
        message = message[0:len(message) - 3] # Remove trailing space-pipe-space
        await cmd.reply(message)

    """
    Main loop that the bot's main thread enters after setup. Sleeps for the activity window, 
    adds point rewards to everyone in the active user list (populated by the on_message hook), 
    and clears the active user list.
    """
    async def point_loop(self):
        while(True): # Interrupted by program ending
            await asyncio.sleep(config.getint('points', 'activeMinutes') * 60)
            if(config.getboolean('featuresEnabled', 'points')):
                # Give points to all active chatters, and then clear the list of active chatters
                pointRewards = config.getint('points', 'pointRewards')
                print(f'Giving {pointRewards} points to users: {self.activeUsers}')
                for user in self.activeUsers:
                    if(user.lower() in self.data['points']):
                        self.data['points'][user.lower()] += pointRewards
                    else:
                        self.data['points'][user.lower()] = pointRewards
                await self.save_data()
                self.activeUsers = []

    async def run(self):

        # Load persistent data
        await self.load_data()

        # Set up authentication
        twitch = await Twitch(APP_ID, APP_SECRET)
        auth = UserAuthenticator(twitch, USER_SCOPE)
        token, refresh_token = await auth.authenticate()
        await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)
        self.chat = await Chat(twitch)

        # Regster event handlers
        self.chat.register_event(ChatEvent.READY, self.on_ready)
        self.chat.register_event(ChatEvent.MESSAGE, self.on_message)

        # Register command handlers
        self.chat.register_command('addcom', self.add_custom_command, [ModeratorOnlyMiddleware()])
        self.chat.register_command('removecom', self.remove_custom_command, [ModeratorOnlyMiddleware()])
        self.chat.register_command('editcom', self.edit_custom_command, [ModeratorOnlyMiddleware()])
        self.chat.register_command('addquote', self.add_quote, [ModeratorOnlyMiddleware()])
        self.chat.register_command('removequote', self.remove_quote, [ModeratorOnlyMiddleware()])
        self.chat.register_command('quote', self.get_quote)
        self.chat.register_command('points', self.get_points)
        self.chat.register_command('addpoints', self.add_points, [StreamerOnly()])
        self.chat.register_command('redeem', self.redeem_points)
        self.chat.register_command('redeems', self.get_redeems)
        self.chat.register_command('leaderboard', self.get_points_leaderboard)
        self.reservedCommands = [
            '!addcom',
            '!removecom',
            '!editcom',
            '!addquote',
            '!removequote',
            '!quote',
            '!points',
            '!addpoints',
            '!redeem',
            '!redeems',
            '!leaderboard'
        ]

        # Start the bot
        self.chat.start()

        # Keep the bot going indefinitely until the user stops the program
        try:
            await self.point_loop()
        finally:
            # Gracefully disconnect/close
            self.chat.stop()
            await twitch.close()

asyncio.run(TwitchBot().run())