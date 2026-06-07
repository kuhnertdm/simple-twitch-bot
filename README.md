# Simple Twitch Bot

Simple, no-nonsense, lightweight Twitch chat bot made using [pytwitchapi](https://pytwitchapi.dev/en/stable/)

## Features

* Supports Python 3.5+
* Works with the streamer's Twitch account or a dedicated bot account
* Custom runtime-manageable commands
* Quotes
* Points/Redeems

## Jumpstart

* Twitch setup
  * Go to [Twitch's app creation page](https://dev.twitch.tv/console/apps/create), logging in with your actual Twitch account (not the dedicated bot account)
  * Fill in the following info:
    * Name: `[Any appropriate name]`
    * OAuth Redirect URLs: `http://localhost:17563`
    * Category: `Chat Bot`
    * Client Type: `Confidential`
  * Save the Client ID value of the application (sometimes also called the Application ID), create a Client Secret for the application, and save that too
  * **OPTIONAL:** If you are using a dedicated bot account, create it like any other Twitch account
* Bot Setup
  * Install [Python 3](https://www.python.org/) if you have not - Requires a minimum version of Python 3.5
  * Install the pytwitchapi package: `pip install twitchAPI`
  * Clone/download the contents of this repo
  * Make a duplicate of `config.ini.example` named `config.ini`
* Configuration
  * Customize your config.ini file as needed:
    * Add your saved client ID/secret values in the appropriate fields under `[auth]`
    * Specify your channel name in the appropriate field under `[setup]`
    * If you want to disable any of the three main features (custom commands, quotes, and points), change "True" to "False" for the appropriate field under `[featuresEnabled]`
    * To configure the rate at which points are gained, change the appropriate values under `[points]`:
      * **activeMinutes**: How often the bot checks for activity
      * **pointRewards**: How many points are awarded to active users in the window
      * For example, if `activeMinutes` is 5, and `pointRewards` is 25, then every 5 minutes, the bot will award 25 points to every user who sent a chat message in the past 5 minutes.
    * To configure the available point redeems, add/modify/remove fields under `[redeemCosts]` and `[redeemCooldowns]` as needed:
      * Every redeem must have a value under `[redeemCosts]`; cooldowns are optional. If a redeem has a cooldown, the redeem name must match between the two sections.
      * Redeem cooldowns are global, and specified in seconds. For example, if a redeem is listed under `[redeemCooldowns]` with a value of `300`, then it can only be called once every 300 seconds (5 minutes) by anyone.
* Running the Bot
  * Run `bot.py`
    * Windows: `py -3 ./bot.py`
    * Linux: `python3 ./bot.py`
  * The script will open your default browser to log into Twitch to authenticate via OAuth2.
  * **OPTIONAL:** If you're using a dedicated bot account, copy the URL from the browser window and paste it into an incognito browser so you can log in with your not-already-logged-in Twitch account. If you have previously authenticated using your standard Twitch account and want to start using a dedicated bot account, you will need to go to your [Twitch connections](https://www.twitch.tv/settings/connections) page and click "Disconnect" on the entry under "Other Connections" that corresponds to your app name.
  * Authenticate in the browser. The bot will gain the ability to read/post messages in the chat that it is connected to, using the account that is authorized.
  * The bot will start up and post a test message in the chat.
  * To stop the bot, kill the script (Ctrl+C)

## Usage

### Custom Commands

* `!addcom <name> <responseText>` - Creates a new custom command.
  * Only usable by streamer/moderators.
  * If the command name is not prefixed with `!`, it will be added automatically.
  * Example: `!addcom yt This is my YouTube channel: <link>` - Creates a new command so that any user can type `!yt`, and the bot will reply with `This is my YouTube channel: <link>`
* `!editcom <name> <responseText>` - Changes the response text on a custom command.
  * Only usable by streamer/moderators.
  * If the command name is not prefixed with `!`, it will be added automatically.
  * Example: `!editcom yt This is my NEW YouTube channel: <newlink>` - Creates a new command so that any user can type `!yt`, and the bot will reply with `This is my NEW YouTube channel: <newlink>`
* `!removecom <name>` - Removes a custom command.
  * Only usable by streamer/moderators.
  * If the command name is not prefixed with `!`, it will be added automatically.
  * Example: `!removecom yt` - Removes the `!yt` command

### Quotes

* `!addquote <quotetext>` - Adds a new quote.
  * Only usable by streamer/moderators.
  * The date/current game are appended onto the end of the quote text.
  * Example: `!addquote Something silly! - @MyFavoriteModerator` - Creates a new quote in the following format: `Something silly! - @MyFavoriteModerator | 06/07/2026 | Super Mario 64`
* `!removequote <index>` - Removes the quote with the given index.
  * Only usable by streamer/moderators.
  * Preserves the indices of all other quotes. For example, if quote 5 is removed, then quote 6 is still quote 6.
  * Example: `!removequote 4` - Removes the quote with index 4.
* `!quote` - Replies with a random quote
  * Usable by anyone.
  * Example: `!quote` causes the bot to reply with `Quote #3: Something silly! - @MyFavoriteModerator | 06/07/2026 | Super Mario 64`
* `!quote <index>` - Replies with the quote with the given index
  * Usable by anyone.
  * Example: `!quote 3` causes the bot to reply with `Quote #3: Something silly! - @MyFavoriteModerator | 06/07/2026 | Super Mario 64`
* `!quote <keyword>` - Replies with a random quote containing the given keyword
  * Usable by anyone
  * Example: `!quote silly` causes the bot to reply with `Quote #3: Something silly! - @MyFavoriteModerator | 06/07/2026 | Super Mario 64`

### Points

* `!points` - Replies with the number of points the caller has
  * Usable by anyone.
  * Example: `!points` causes the bot to reply with `YourUsername has 5 points`
* `!addpoints <user> <amount>` - Adds the given number of points to the given user
  * Only usable by the streamer.
  * If the user is prefixed with `@`, it will be removed automatically.
  * Example: `!addpoints MyFavoriteChatter 1000` gives 1000 points to MyFavoriteChatter
* `!redeem <redeemName>` - Redeems the given redeem
  * Usable by anyone
  * Example: `!redeem stretch` causes the bot to deduct the configured cost of the "stretch" redeem and reply with `YourUsername has redeemed stretch and now has 5 points!`
* `!redeems` - Replies with the list of available redeems
  * Usable by anyone
  * Example: `!redeems` causes the bot to reply with `lurk (1) | stretch (10) | ama (100)`
* `!leaderboard` - Replies with the list of the top 10 users by points
  * Usable by anyone
  * Example: `!leaderboard` causes the bot to reply with `myfavoritestreamer (12345) | myfavoritemoderator (100) | myfavoritechatter (5)`