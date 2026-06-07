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
    * OAuth Redirect URLs: `[http](http://localhost:17563)`
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