# Welcome to DCSServerBot!
You've found a comprehensive solution that helps you administrate your DCS World servers. It has a Discord integration 
(now optional!) with slash-commands, built in per-server and per-user statistics, optional cloud-based statistics, 
[Coalitions](./COALITIONS.md)-support and much more! 
With its plugin system and reporting framework, DCSServerBot can be enhanced very easily to support whatever might come 
into your mind. DCSServerBot is a solution for DCS server admins built by a DCS server admin.

This documentation shows you the main features, how to install and configure the bot and some more sophisticated 
stuff at the bottom, if you for instance run multiple servers maybe even over multiple locations. 

Now let's see, what DCSServerBot can do for you (installation instructions [below](#installation))!

---
## Architecture
DCSServerBot has a modular architecture with services, plugins and extensions that provide specific functionalities 
like monitoring the availability of your servers, a lot of Discord slash-commands and supports common add-ons like SRS, 
LotAtc, DCS Olympus and others.

The solution itself is made for anything from single-server environments up to large scale, worldwide installations with
high availability requirements. There are nearly no limits. If you are interested into some deeper insights to the
bots architecture, read [here](./ARCHITECTURE.md)

### Node
A node is an installation of DCSServerBot on one PC. The usual user will have one installation, meaning one node.
You can run multiple instances of DCS ("DCS servers") with each node (see below). If you run multiple PCs or (virtual) 
servers, you need to install multiple DCSServerBot nodes. This results in a DCSServerBot cluster.<br>
One node is always a master node, which handles all the Discord commands and controls the rest of the cluster.

### Instance
Each node can control multiple instances of DCS, meaning `DCS.exe` or `DCS_Server.exe` processes. You can use the
normal client installation of DCS World to run a server, but the [Dedicated Server](https://www.digitalcombatsimulator.com/en/downloads/world/server/) installation would be preferable.

### Services
A service is a component that runs on each node. Services can be combined with plugins, if they provide additional
Discord commands, like the Music service. Some services only run on the master node, like the Bot service for instance.

| Service    | Scope                                                                                                     | Plugin      | Documentation                             |
|------------|-----------------------------------------------------------------------------------------------------------|-------------|-------------------------------------------|
| Backup     | Backup your bot- and DCS-configuration, your missions, database, etc.                                     | Backup      | [README](./services/backup/README.md)     |
| Bot        | The Discord bot handling all discord commands. There is a Discord-free variant available also (see blow)! |             | [README](./services/bot/README.md)        |
| Cleanup    | Cleanup logfiles, trackfiles, etc. from your disk.                                                        |             | [README](./services/cleanup/README.md)    |
| Dashboard  | Nice console graphics display to show the status of your bot / servers.                                   |             | [README](./services/dashboard/README.md)  |
| Monitoring | Availability- and performance-monitoring of your DCS servers.                                             | ServerStats | [README](./services/monitoring/README.md) |
| Music      | Play music over different SRS-radios on your servers.                                                     | Music       | [README](./services/music/README.md)      |
| OvGME      | Manage mods that needs to be installed / updated in your DCS servers.                                     | OvGME       | [README](./services/ovgme/README.md)      |
| Scheduler  | Schedule tasks based on a cron-like configuration.                                                        | Scheduler   | [README](./services/scheduler/README.md)  |
| ServiceBus | Communication hub between every node of the bot cluster and all DCS-servers.                              |             | [README](./services/servicebus/README.md) |

### Plugins
A plugin is an expansion of the bot that can be controlled via Discord commands and sometimes in-game chat commands. 
DCSServerBot comes with a rich set of default plugins, but it can be enhanced with optional plugins. I enhance the bot
from time to time, but you as a community member can also create your own plugins (and maybe share them with others). 

| Plugin       | Scope                                                                           | Optional | Depending on            | Documentation                              |
|--------------|---------------------------------------------------------------------------------|----------|-------------------------|--------------------------------------------|
| GameMaster   | Interaction with the running mission (inform users, set flags, etc)             | no       |                         | [README](./plugins/gamemaster/README.md)   |
| Mission      | Handling of missions, comparable to the WebGUI.                                 | no       | GameMaster              | [README](./plugins/mission/README.md)      |
| Admin        | Admin commands to manage your DCS server.                                       | yes*     |                         | [README](./plugins/admin/README.md)        |
| Help         | Interactive help commands for Discord and in-game chat                          | yes*     |                         | [README](./plugins/help/README.md)         |
| UserStats    | Users statistics system.                                                        | yes*     | Mission                 | [README](./plugins/userstats/README.md)    |
| CreditSystem | User credits, based on achievements.                                            | yes*     | Mission                 | [README](./plugins/creditsystem/README.md) |
| Scheduler    | Autostart / -stop of servers or missions, modify missions, etc.                 | yes*     | Mission                 | [README](./plugins/scheduler/README.md)    |
| Cloud        | Cloud-based statistics and connection to the DGSA global ban system.            | yes*     | Userstats               | [README](./plugins/cloud/README.md)        |
| MissionStats | Detailed users statistics / mission statistics.                                 | yes*     | Userstats               | [README](./plugins/missionstats/README.md) |
| Backup       | Create a backup of your database, server or bot configurations.                 | yes      |                         | [README](./plugins/backup/README.md)       |
| Battleground | Support for [DCS Battleground](https://github.com/Frigondin/DCSBattleground)    | yes      |                         | [README](./plugins/battleground/README.md) |
| Commands     | Create custom discord commands.                                                 | yes      |                         | [README](./plugins/commands/README.md)     |
| Competitive  | Support for PvP communities, especially with TrueSkill™️ ranking system.        | yes      | Mission                 | [README](./plugins/competitive/README.md)  |
| DBExporter   | Export the DCSServerBot database or singular tables as json.                    | yes      |                         | [README](./plugins/dbexporter/README.md)   |
| FunkMan      | Support for [FunkMan](https://github.com/funkyfranky/FunkMan)                   | yes      |                         | [README](./plugins/funkman/README.md)      |
| GreenieBoard | Greenieboard and LSO quality mark analysis (SC and Moose.AIRBOSS / FunkMan)     | yes      | Missionstats            | [README](./plugins/greenieboard/README.md) |
| LotAtc       | Upload LotAtc Transponder files to your servers.                                | yes      |                         | [README](./plugins/lotatc/README.md)       |
| MOTD         | Message for players on join or when they jump in a module.                      | yes      | Mission, MissionStats   | [README](./plugins/motd/README.md)         |
| Music        | Upload and play music over SRS.                                                 | yes      |                         | [README](./plugins/music/README.md)        |
| OvGME        | Install or update mods into your DCS server.                                    | yes      |                         | [README](./plugins/ovgme/README.md)        |
| Pretense     | Commands for Pretense missions.                                                 | yes      |                         | [README](./plugins/pretense/README.md)     |
| Punishment   | Punish users for team-hits or team-kills.                                       | yes      | Mission                 | [README](./plugins/punishment/README.md)   |
| RealWeather  | Apply real weather to your missions (also available as an extension).           | yes      |                         | [README](./plugins/realweather/README.md)  |
| RestAPI      | Simple REST-API to query users and statistics (WIP).                            | yes      | Userstats, MissionStats | [README](./plugins/restapi/README.md)      |
| ServerStats  | Server statistics for your DCS servers.                                         | yes      | Userstats               | [README](./plugins/serverstats/README.md)  |
| SlotBlocking | Slot blocking either based on discord roles or credits.                         | yes      | Mission, CreditSystem   | [README](./plugins/slotblocking/README.md) |
| SRS          | Display players activity on SRS, show active channels and enable slot blocking. | yes      | MissionStats            | [README](./plugins/srs/README.md)          |
| Tacview      | Install or uninstall Tacview from your server(s) and do a basic configuration.  | yes      |                         | [README](./plugins/tacview/README.md)      |
| Voting       | Simple voting system for players to be able to change missions, weather, etc.   | yes      |                         | [README](./plugins/voting/README.md)       |


*) These plugins are loaded by the bot by default, but they are not mandatory to operate the bot.<br> 
&nbsp;&nbsp;&nbsp;&nbsp;If you do not want to load any of them, define a list of `plugins` in your main.yaml and only<br>
&nbsp;&nbsp;&nbsp;&nbsp;list the plugins you want to load.

#### How to install 3rd-Party Plugins
If a community member provides a plugin for DCSServerBot, chances are that it is packed into a zip file. You can 
download this zipfile and place it directly into the /plugins directory. DCSServerBot will automatically unpack the 
plugin for you, when DCSServerBot restarts. Keep in mind that some of these plugins might need configurations. Please 
refer to the respective plugin-documentation for more.

#### In case you want to write your own Plugin ...
You can find a sample in the plugins/sample subdirectory and a guide [here](./plugins/README.md). These will guide you 
through the steps needed to build your own plugin. Do you want your plugin to be added as an optional plugin to the 
DCSServerBot? Contact me via the contact details listed below.

### Extensions
Many DCS admins use extensions or add-ons like DCS-SRS, Tacview, LotAtc, etc.</br>
DCSServerBot supports some of them already and can add a bit of quality of life.

| Extension        | Scope                                                                                                             | 
|------------------|-------------------------------------------------------------------------------------------------------------------|
| MizEdit          | My own invention, can be used to modify your missions. Very powerful, read it up [here](./extensions/MizEdit.md)! |
| DCS Voice Chat   | DCS VOIP system to communicate with other pilots.                                                                 |
| DCS-SRS          | Market leader in DCS VOIP integration.                                                                            |
| Tacview          | Well known flight data capture and analysis tool.                                                                 |
| LotAtc           | GCI- and ATC-extension for DCS World. Simple display only extension.                                              |
| DSMC             | DSMC mission handling, should be activated when dealing with DSMC missions.                                       |
| DCS Olympus      | Real-time control of your DCS missions through a map interface.                                                   |
| Lardoon          | Webgui for Tacview with search options.                                                                           |
| Sneaker          | Moving map interface (see [Battleground](https://github.com/Frigondin/DCSBattleground) for another option!        |
| DCS Real Weather | Real weather for your missions.                                                                                   |
| OvGME            | Use mods within your DCS World servers.                                                                           |
| gRPC             | Support gRPC, a communication framework with DCS World.                                                           |
| Pretense         | Dynamic campaign framework by Dzsek.                                                                              |

Check out [Extensions](./extensions/README.md) for more info on how to use them.

---
## Installation

### Prerequisites
You need to have [Python](https://www.python.org/downloads/) 3.9 or higher and [PostgreSQL](https://www.postgresql.org/download/) installed. Please make sure that you tick 
"Add python.exe to PATH" during your Python installation.<br>

If you want to use instant autoupdate from the master branch, you have to install [GIT](https://git-scm.com/download/win) and make sure the ```git```-command is in your PATH.

### Discord Setup
The bot needs a unique Token per installation. This one can be obtained at http://discord.com/developers <br/>
- Create a "New Application".
- Select Bot from the left menu and give it a nice name, icon and maybe a banner.
- Press "Reset Token" and then "Copy" to obtain your token. 
- Now your Token is in your clipboard. Paste it in some editor for later use. 
- All "Privileged Gateway Intents" have to be enabled on that page.<br/>
- To add the bot to your Discord guild, select "OAuth2" from the left menu
- Select the "bot" checkbox in "OAuth2 URL Generator"
- Select the following "Bot Permissions":
  - Left side:
    - Manage Channels
  - Center:
    - Send Messages
    - Manage Messages
    - Embed Links
    - Attach Files
    - Read Message History
    - Add Reactions
    - Use Slash Commands
- Press "Copy" on the generated URL and paste it into the browser of your choice
- Select the guild the bot has to be added to - and you're done!

> ⚠️ **Attention!**<br>
> For easier access to user and channel IDs, enable "Developer Mode" in "Advanced Settings" in your Discord client.

### 🆕 Setup without using Discord
If you do not want to use Discord, or if you maybe are not allowed to do so due to limitations of your Country, etc.
you can now install DCSServerBot without the need to use Discord. Just select the respective option during the 
installation, and you will install a variant that works without.
> ⚠️ **Attention!**<br>
> Please keep in mind that DCSServerBot was originally made for Discord and that there are some functionalities that
> can only work, if you use it, like static graphs, greenieboards, and others.<br>
> But you can still use a lot and there are in-game chat-commands also that you can use, without any need of Discord.

### Download
Best is to use ```git clone https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot.git``` as you then always have 
the newest fixes, independent of and release version. Otherwise, download the latest release version as ZIP and extract 
it somewhere on your PC that is running the DCS server(s) and give it write permissions, if needed. 

> ⚠️ **Attention!**<br>
> Make sure that the bots installation directory can only be seen by yourself and is not exposed to anybody 
> outside via www etc. as it contains sensitive data.

### Database
DCSServerBot uses PostgreSQL to store all information that needs to be persistent. This consists of, but is not limited
to: players, mission information, statistics. DCSServerBot needs a fast database to do this. Install the latest 
available PostgreSQL version from the above-mentioned website.<br>

> ⚠️ **Attention!**<br>
> If using PostgreSQL remotely over unsecured networks, it is recommended to have SSL enabled.

### DCSServerBot Installation (Discord)
Run the provided `install.cmd` script or just `run.cmd`.<br>
It will ask you for your Guild ID (right-click on your Discord server icon and select "Copy Server ID") and the bots 
user ID (right-click on the bot user and select "Copy User ID"). Then it will search for existing DCS installations, 
create the database user, password and database and asks whether you want to add existing DCS servers to the 
configuration.<br>
When finished, the bot should launch successfully and maybe even start your servers already, if configured.

### DCSServerBot Installation (non-Discord)
Run the provided `install.cmd` script or just `run.cmd`.<br>
It will ask you for your DCS group name and a role mapping, where you can give specific DCS users roles that are needed
to make the in-game commands work. You need the UCIDs of the users here. Then it will search for existing DCS 
installations, create the database user, password and database and asks whether you want to add existing DCS servers 
to the configuration.<br>
When finished, the bot should launch successfully and maybe even start your servers already, if configured.

> ⚠️ **Attention!**<br> 
> You should shut down your DCS servers during the bots installation, as it places its own LUA hooks inside
> the servers Scripts directory.<br>
> Please keep also in mind, that a lot of configuration parameters which you find below are not needed for a 
> non-Discord setup. If you have no idea what to put in a specific parameter, that is usually a good sign to just
> skip it.

You can start the installer with these parameters:
```
Usage: install.cmd [-h] [-n NODE] [-c CONFIG] [-u USER] [-d DATABASE]

Welcome to DCSServerBot!

options:
  -h, --help                        Show this help message and exit
  -n NODE, --node NODE              Node name (default = hostname)
  -c CONFIG, --config CONFIG        Path to configuration
  -u USER, --user USER              Database username (default = dcsserverbot)
  -d DATABASE, --database DATABASE  Database name (default = dcsserverbot)
```
You might want to provide different node names, if you install multiple nodes on one PC and different database user
and database names, if you want to install multiple bots for multiple Discord groups.

### Desanitization
DCSServerBot desanitizes your MissionScripting environment. That means, it changes entries in Scripts\MissionScripting.lua
of your DCS installation. If you use any other method of desanitization, DCSServerBot checks, if additional 
desanitizations are required and conducts them.

> ⚠️ **Attention!**<br>
> DCSServerBot needs write-permissions on the DCS-installation directory.<br>
> You can usually achieve that by giving the "User group" write permissions on it. Right-click on your DCS installation
> folder,<br>select Properties -> Security -> Edit, select "Users (...)" and tick Modify below. Then press the OK button.
> There might be a question about changing the permission on all subdirectories - say yes in that case. 

Your MissionScripting.lua should look like this after a successful bot start:
```lua
do
	sanitizeModule('os')
	--sanitizeModule('io')
	--sanitizeModule('lfs')
	--_G['require'] = nil
	_G['loadlib'] = nil
	--_G['package'] = nil
end
```

### Custom MissionScripting.lua
If you want to use a **custom MissionScripting.lua** that has more sanitization (for instance for LotAtc, Moose, 
OverlordBot or the like) or additional lines to be loaded (for instance for LotAtc, or DCS-gRPC), just place the 
MissionScripting.lua of your choice in the config directory of the bot. It will then be replaced on every bot startup.

---
## Configuration
The bot configuration is held in several files in the **config** subdirectory.
If you run the `install.cmd` script for the first time, it will generate basic files for you that you can amend to your 
needs afterwards. Your bot should be ready to run already, and you can skip this section for now, if you don't want to
bother with the bots configuration in first place.

> ⚠️ **Attention!**<br>
> If you run more than one bot node, best is to share the configuration between all nodes. This can be done via a cloud
> drive for instance or with some file sync tool.

The following samples will show you what you can configure in DCSServerBot. For most of the configuration, default 
values will apply, so you don't need to define all these values explicitly. I printed them here for completeness and 
for the sake of documentation.

### config/main.yaml
This file holds the main information about DCSServerBot. You can configure which plugins are loaded here for instance.

```yaml
guild_id: 112233445566    # Your Discord server ID. Right-click on your server and select "Copy Server ID". On non-discord installations this number is filled for you.
guild_name: My Group      # Non-Discord only: your DCS group name
autoupdate: true          # use the bots autoupdate functionality, default is false
use_dashboard: true       # Use the dashboard display for your node. Default is true.
chat_command_prefix: '-'  # The command prefix to be used for in-game chat commands. Default is "-"
chat_filter: true         # Use the profanity filter for the in-game chat.
mission_rewrite: false    # Disable the re-write of missions by MizEdit or RealWeather. The server will be stopped for any mission change then. (default: true)
language: de              # Change the bots language to German. This is WIP, several languages are in the making, including DE, ES, RU and more
database:
  url: postgres://USER:PASSWORD@DB-IP:DB-PORT/DB-NAME   # The bot will auto-move the database password from here to a secret place and replace it with SECRET.
  pool_min: 5           # min size of the DB pool, default is 5
  pool_max: 10          # max size of the DB pool, default is 10
  max_reties: 10        # maximum number of retries to initially connect to the database on startups
logging:
  loglevel: DEBUG           # loglevel, default is DEBUG
  logrotate_count: 5        # Number of logfiles to keep after rotation. Default is 5.    
  logrotate_size: 10485760  # max size of a logfile, default is 10 MB
  utc: true                 # log in UTC (default: true), use local time otherwise
messages:
  player_username: Your player name contains invalid characters. Please change your # Default message for players with invalid usernames
    name to join our server.
  player_default_username: Please change your default player name at the top right  # Default message for players with default usernames
    of the multiplayer selection list to an individual one!
  player_banned: 'You are banned from this server. Reason: {}'                      # Default message for banned players.
filter:
  server_name: ^Special K -           # Filter to shorten your server names on many bot displays. Default is none. 
  mission_name: ^Operation|_|\(.*\)   # Filter to shorten your mission names on many bot displays. Default is none.
  tag: "'^[JDS]'"                     # If your community uses specific tags, this helps with the bots automatch functionality.
opt_plugins:                          # Optional: list of optional plugins to be loaded and used by the bot
- serverstats                         # see above
- dbexporter
- motd
- greenieboard
- punishment
- slotblocking
- music
- funkman
- ovgme
- commands
- restapi
```

### config/nodes.yaml
This file holds the main configuration for all your nodes.<br>
For a cluster installation, you want to describe all your nodes and instances on all your nodes, as the bot can 
(auto-)migrate stuff in-between the cluster!

```yaml
NODENAME:                       # this will usually be your hostname
  listen_port: 10042            # On which port should the bot listen? Default is 10042
  listen_address: 0.0.0.0       # Optional: On which interface should the bot listen? Default is 127.0.0.1.
  slow_system: false            # Optional: if you are using a slower PC to run your servers, you should set this to true (default: false)
  preferred_master: true        # cluster only: this node should be the preferred master node (default: false)
  heartbeat: 30                 # cluster only: time for the heartbeat between the master and agent nodes to run (default: 30)
  cloud_drive: false            # cluster only: set this to false, if you do not have the bot installed on a cloud drive (default and recommended: true) 
  nodestats: true               # Enable/disable node statistics (database pool and event queue sizes), default: true
  DCS:
    installation: '%ProgramFiles%\\Eagle Dynamics\\DCS World Server'  # This is your DCS installation. Usually autodetected by the bot.
    autoupdate: true            # enable auto-update for your DCS servers. Default is false.
    cloud: true                 # If you have installed DCS on a NAS or cloud drive, autoupdate and desanitization will only take place once on all your nodes.
    desanitize: true            # Desanitize your MissionScripting.lua after each update. Default is true.
    minimized: true             # Start DCS minimized (default: true)
    user: xxxx                  # Your DCS username (only needed for specific use-cases)
    password: xxxx              # Your DCS password (will be auto-moved by the bot to a secret place)
  instances:
    DCS.release_server:        # The name of your instance. You can have multiple instances that have to have unique names.
      home: '%USERPROFILE%\\Saved Games\\DCS.release_server' # The path to your saved games directory.
      missions_dir: '%USERPROFILE%\Documents\Missions'        # You can overwrite the default missions dir like so. Default is the Missions dir below the instance home folder.
      bot_port: 6666            # The port DCSServerBot uses to communicate with your DCS server. Each instance has to have a unique port. This is NOT your DCS port (10308)!!!
      max_hung_minutes: 3       # Let DCSServerBot kill your server if it is unresponsive for more than x minutes. Default is 3. Disable it with 0.
      affinity: 2,3             # Optional: set the CPU-affinity for the DCS_Server.exe.
      priority: normal          # Optional: set the process priority (low, normal, high, realtime) for the DCS_Server.exe
      extensions:               # See the extension documentation for more detailed information on what to set here.
        SRS:
          config: '%USERPROFILE%\Saved Games\DCS.release_server\Config\SRS.cfg'  # it is recommended to copy your SRS "server.cfg" below your instances home directory.
          host: 127.0.0.1       # SRS servers local IP (default is 127.0.0.1)
          port: 5002            # SRS servers local port (default is 5002). The bot will change this in your SRS configuration, if set here!
          autostart: true       # this will autostart your DCS server with the DCS server start (default: true)
          autoupdate: true      # This will auto-update your SRS servers. Default is false, you need to run the bot as Administrator to make it work!
        Tacview:
          show_passwords: false # If you don't want to show the Tacview passwords (default: true)
    instance2:                  # you can have an unlimited amount of instance configurations, but each instance has to have a physical representation on your disk.
      ...
```

### config/servers.yaml
This is your server configuration.<br>
You might wonder why the configuration is split between nodes.yaml and servers.yaml? Even if you have a basic setup! 
This is to decouple the server configuration from the physical node (aka the "DCS.exe" / "DCS_Server.exe" process). You 
will learn to love it, especially when you decide to move a server from one instance to another or even from one node to 
another. This is much easier with a non-coupled approach like that.
```yaml
DEFAULT:
  message_ban: 'You are banned from this server. Reason: {}' # default message, if a player is banned on the DCS server
  message_afk: '{player.name}, you have been kicked for being AFK for more than {time}.'  # default message for AFK users
  message_server_full: The server is full, please try again later!  # default message, if the server is considered full (see SlotBlocking plugin)
  message_reserved: 'This server is locked for specific users.\nPlease contact a server admin.' # Message if server requires discord role (optional)
  message_no_voice: You need to be in voice channel "{}" to use this server!  # default message, if you are not in Discord voice, but force_voice is on.
  message_slot_spamming: You have been kicked for slot spamming! # default message for slot spamming (changing more than 5 slots in-between 5 seconds)
  message_timeout: 10           # default timeout for DCS popup messages in seconds 
  display_ai_chat: false        # do not display AI chat messages in the chat channel (default: false)
  rules: |                      # Optional: Rules to be displayed for new users (needs MissionStats enabled!)
    These are the rules to play on this server:
    1) Do not team-kill
    2) Do not harass people
    3) Be a decent human being
    4) ...
  accept_rules_on_join: true    # True, if rules have to be acknowledged (players will be moved to spectators otherwise, default: false)
My Fancy Server:                # Your server name, as displayed in the server list and listed in serverSettings.lua
  server_user: Admin            # Name of the server user #1 (technical user), default is "Admin".
  afk_time: 300                 # Time in seconds after which a player that is on spectators is considered being AFK. Default: -1, which is disabled
  ping_admin_on_crash: true     # Ping DCS Admin role in discord, when the server crashed. Default: true
  autoscan: false               # Enable autoscan for new missions (and auto-add them to the mission list). Default: false
  autorole: Fancy Players       # Optional: give people this role, if they are online on this server (overwrites autorole[online] in bot.yaml!).
  force_voice: false            # Optional: enforce the usage of a voice channel (users needs to be linked!) - default: false
  discord:                      # Optional: specify discord roles that are allowed to use this server
    - '@everyone'               # Attention: people can not self-link on these servers and have to be liked properly already!
  channels:
    status: 1122334455667788    # The Discord channel to display the server status embed and players embed into. Right-click on your channel and select "Copy Channel ID". You can disable it with -1
    chat: 8877665544332211      # The Discord channel for the in-game chat replication. You can disable it with setting it to -1.
    admin: 1188227733664455     # The channel where you can fire admin commands to this server. You can decide if you want to have a central admin channel or server specific ones. See bot.yaml for more.
    voice: 1827364518273645     # The voice channel, where people need to connect to (if force_voice is true). 
  chat_log:
    count: 10                   # A log file that holds the in-game chat to check for abuse. Tells how many files will be kept, default is 10.
    size: 1048576               # Max logfile size, default is 1 MB. 
  no_coalition_chat: true       # Do not replicate red and blue chats to the Discord chat replication (default: false)
  serverSettings:               # Overwrite the serverSettings.lua with these values
    port: 10308
    advanced:
      resume_mode: 0
My 2nd Fancy Server:            # You can have an unlimited amount of server configurations.
  ...
```

### config/presets.yaml
This file holds your different presets that you can apply to missions as modifications.<br>
See [MizEdit](./extensions/MizEdit.md) for further details.

### services/bot.yaml
This is your Discord-bot configuration.

```yaml
token: SECRET_DISCORD_TOKEN                     # Your TOKEN, as received from the discord developer portal. This will be auto-moved to a secret place by the bot.
owner: 1122334455667788                         # The ID of your bot user. Right click, select "Copy User ID".
automatch: true                                 # Use the bots auto-matching functionality (see below), default is true.
autoban: false                                  # Use the bots auto-ban functionality (see below), default is false.
autorole:                                       # Automatically give roles to people, depending on conditions (see below). The roles need to be set up in your Discord server.
  on_join: Member                               # Give anyone the "Member" role, if they join your Discord.
  linked: DCS                                   # Give people that get linked the DCS role.
  online: Online                                # Give people that are online on any of your servers the "Online" role.
no_dcs_autoban: false                           # If true, people banned on your Discord will not be banned on your servers (default: false)
message_ban: User has been banned on Discord.   # Default reason to show people that try to join your DCS servers when they are banned on Discord.
message_autodelete: 300                         # Most of the Discord messages are private messages. If not, this is the timeout after that they vanish. Default is 300 (5 mins). 
admin_channel: 1122334455667788                 # Optional: Central admin channel (see below).
reports:
  num_workers: 4                                # Number of worker threads to be used for any reports generated by the bot. Default is 4.
discord_status: Managing DCS servers ...        # Message to be displayed as the bots Discord status. Default is none.
audit_channel: 88776655443322                   # Central audit channel to send audit events to (default: none)
roles:                                          # Roles mapping. The bot uses internal roles to decouple from Discord own role system.
  Admin:                                        # Map your Discord role "Admin" to the bots role "Admin" (default: Admin)
  - Admin                                       
  Alert:                                        # Optional Alert role. Default is DCS Admin. Would be pinged on server crashes and low performance
  - DCS Admin
  DCS Admin:                                    # Map your Discord role "Moderator" and "Staff" to the bots "DCS Admin" role (default: DCS Admin)
  - Moderator
  - Staff
  GameMaster:                                   # Map the GameMaster role to anybody with the Staff role in your Discord.
  - Staff
  DCS:                                          # Map the bots DCS role to everyone in your discord. Only everyone needs the leading @!
  - @everyone
```
> ⚠️ **Attention!**<br>
> The bots role needs to be above any other role in your Discord server that it has to be able to manage.<br>
> If you want the bot to give the "Online" role for people for example, it has to be below the bot's role.

### CJK-Fonts Support
DCSServerBot supports external fonts, especially CJK-fonts to render the graphs and show your player names using the 
real characters of your language. Unfortunately, I can not auto-download the respective fonts from Google Fonts
anymore, where I have to ask you guys to do that on your own.<br>
To download the supported fonts, go to https://fonts.google.com/ and search for 
- [Noto Sans Traditional Chinese](https://fonts.google.com/noto/specimen/Noto+Sans+TC)
- [Noto Sans Japanese](https://fonts.google.com/noto/specimen/Noto+Sans+JP)
- [Noto Sans Korean](https://fonts.google.com/noto/specimen/Noto+Sans+KR)

Then press "Get font" and "Download all". Copy the ZIP file into a folder "fonts" that you create below the DCSServerBot
installation directory. The bot will take this ZIP on its next startup, unpack it and delete the ZIP file. From then
on, the bot will use the respective font(s) without further configurations.

#### Auto Matching (default: enabled)
To use in-game commands, your DCS players need to be matched to Discord users. Matched players are able to see statistics 
and you can see a variety of statistics yourself as well. The bot offers a linking system between Discord and DCS accounts 
to enable this.
Players can do this with the `/linkme` command. This creates a permanent and secured link that can then be used for in-game 
commands. The bot can also auto-match a DCS player to Discord user. This way, players can see their own stats via Discord 
commands. The bot will try to match the Discord username to DCS player name. This works best when DCS and Discord names 
match! It can generate false links though, which is why I prefer (or recommend) the /linkme command. People still seem 
to like the auto-matching, that is why it is in and you can use it (enabled per default).

#### Auto-Banning (default: disabled)
DCSServerBot supports automatically bans / unbans of players from the configured DCS servers, as soon as they leave / join 
your Discord guild. If you like that feature, set `autoban: true` in services/bot.yaml (default: false).

However, players that are being banned from your Discord or that are being detected as hackers are auto-banned from 
all your configured DCS servers independent of that setting. You can prevent this by setting `no_dcs_autoban: true`.

#### Roles (Discord and non-Discord)
The bot uses the following **internal** roles to apply specific permissions to commands.<br>
You can map your Discord roles to these internal roles like described in the example above or for the non-Discord
variant, you just add your UCIDs as a list below each group.<br>
Non-Discord installations usually only need the Admin and DCS Admin roles.

| Role           | Description                                                                                                                                         |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| Admin          | People with this role are allowed to manage the server, start it up, shut it down, update it, change the password and gather the server statistics. |
| DCS Admin      | People with this role are allowed to restart missions, managing the mission list, ban and unban people.                                             |
| DCS            | People with this role are allowed to chat, check their statistics and gather information about running missions and players.                        |
| GameMaster     | People with this role can see both [Coalitions](./COALITIONS.md) and run specific commands that are helpful in missions.                            |

See [Coalitions](./COALITIONS.md) for coalition roles.

### Handling of Passwords and other Secrets
DCSServerBot stores the secret Discord TOKEN and your database and (optional) DCS password in separate files. If ever 
you have added these to your config files like mentioned above, the bot will take them and move them away. This is a 
security feature. If you somehow forgot the values, you can always reveal them by starting the bot with the -s option
like so: `run.cmd -s`.

### DCS/Hook Configuration
The DCS World integration is done via Hooks. They are being installed automatically into your configured DCS servers by 
the bot.

### Sample Configuration
To view some sample configurations for the bot or for each configurable plugin, look [here](samples/README.md).

### Additional Security Features
Players that have no pilot ID (empty or whitespace) or that share an account with others, will not be able to join your 
DCS server. This is not configurable, it's a general rule (and a good one in my eyes).<br>
Besides that, people that try to join from the very same IP that a banned user has used before will be rejected also
(ban-avoidance). You get a message in the discord admin-channel about it.

### Setup Multiple Servers on a Single Host
To run multiple DCS servers under control of DCSServerBot you just have to make sure that you configure different 
communication ports. This can be done with the parameter `bot_port` in nodes.yaml. The default is 6666, you can just 
increase that for every server (6667, 6668, ...).<br>
Don't forget to configure different Discord channels (`chat` and `status`, optional `admin`) for every server, too. 
This will be done in the servers.yaml file.<br>
To add subsequent servers, just follow the steps above, and you're good, unless they are on a different Windows server 
(see [Multi-Node-Setup](./MULTINODE.md) in that case).

DCSServerBot will autodetect all configured DCS servers on installation and generate simple configuration files 
for you already. To add a new instance, you can either do that manually or use `/node add_instance` in your Discord.
---
## Starting the Bot
To start the bot, use the packaged ```run.cmd``` command. This creates the necessary Python virtual environment and 
launches the bot afterward.<br/>
If you want to run the bot from autostart, press Win+R, enter `shell:startup` and press ENTER, create a shortcut to your
`run.cmd` in there.
---
## Repairing the Bot
If you have issues starting DCSServerBot, especially after an update, it might be that some 3rd party library got 
corrupted. In rare cases, it can also happen, that an auto-update is not possible at all, because some file got changed 
that was not supposed to be changed, or some other corruption has occurred.<br>
In these cases, you can run the `repair.cmd` script in the DCSServerBot installation folder.
---
## How to do the more complex stuff?
DCSServerBot can be used to run a whole worldwide distributed set of DCS servers and therefore supports the largest 
communities. The installation and maintenance of such a use-case is just a bit more complex than a single server 
installation. Please refer to [Multi-Node-Setup](./MULTINODE.md) for further information.

### How to talk to the Bot from inside Missions
If you plan to create Bot-events from inside a DCS mission, that is possible! Just make sure, you include this line in a trigger:
```lua
  dofile(lfs.writedir() .. 'Scripts/net/DCSServerBot/DCSServerBot.lua')
```
> Don't use a Mission Start trigger, as this might clash with other plugins loading stuff into the mission._<br/>
 
After that, you can for instance send chat messages to the bot using
```lua
  dcsbot.sendBotMessage('Hello World', '12345678') -- 12345678 is the ID of the channel, the message should appear, default is the configured chat channel
```
inside a trigger or anywhere else where scripting is allowed.

> ⚠️ **Attention!**<br>
> Channel always has to be a string, encapsulated with '', **not** a number because of Integer limitations in LUA.

Embeds can be sent using code similar to this snippet:
```lua
  title = 'Special K successfully landed at Kutaisi!'
  description = 'The unbelievable and unimaginable event happend. Special K succeeded at his 110th try to successfully land at Kutaisi, belly down.'
  img = 'https://i.chzbgr.com/full/8459987200/hB315ED4E/damn-instruction-manual'
  fields = {
    ['Pilot'] = 'sexy as hell',
    ['Speed'] = '130 kn',
    ['Wind'] = 'calm'
  }
  footer = 'Just kidding, they forgot to put their gear down!'
  dcsbot.sendEmbed(title, description, img, fields, footer)
```
They will be posted in the chat channel by default, if not specified otherwise (adding the channel id as a last parameter of the sendEmbed() call, see sendBotMessage() above).

If you like to use a single embed, maybe in the status channel, and update it instead of creating new messages, you 
can do that, by giving is a name like "myEmbed" in this example. The name has to be unique per server.
```lua
  title = 'RED Coalition captured Kutaisi!'
  description = 'After a successful last bombing run, RED succeeded in capturing the strategic base of Kutaisi.\nBLUE has to fight back **NOW** there is just one base left!'
  dcsbot.updateEmbed('myEmbed', title, description)
  --[....]
  title = 'Mission Over!'
  description = 'RED has won after capturing the last BLUE base Batumi, congratulations!'
  img = 'http://3.bp.blogspot.com/-2u16gMPPgMQ/T1wfXR-bn9I/AAAAAAAAFrQ/yBKrNa9Q88U/s1600/chuck-norris-in-war-middle-east-funny-pinoy-jokes-2012.jpg'
  dcsbot.updateEmbed('myEmbed', title, description, img)
```
If no embed named "myEmbed" is already there, the updateEmbed() call will generate it for you. Otherwise, it will be 
replaced with this one.

### How to overwrite DCSServerBot's default permissions?
You can change any command either in discord or the in-game chat. You can select a different name, different roles, etc.,
or even disable the command at all.
For Discord, you need to keep the command structure in mind, meaning, if you have a group command (like /server startup)
or a single one (like /help). If you want to change any of the commands, go to your respective plugin configuration and
add a top-level section like so:
```yaml
commands:
  dcs:
    bans:
      roles:
      - Admin
      name: prohibiciones
      brief: lista de prohibiciones
      description: mostrar una lista de todas las prohibiciones en sus servidores
```
If you add this to your admin.yaml, it will rename the command `/dcs bans` to `/dcs prohibiciones`, change the 
documentation of it and make it only available for people that own the Admin role.

If you want to change in-game chat commands, you can do it like so:
```yaml
chat_commands:
  911:
    enabled: false
```
If you add these lines to your mission.yaml, you disable the -911 command on your servers.

---
## Contact / Support
If you need support, if you want to chat with me or other users or if you like to contribute, jump into my [Support Discord](https://discord.gg/h2zGDH9szZ).<br>
If you like what I do, and you want to support me, you can do that via my [Patreon Page](https://www.patreon.com/DCS_SpecialK).

---
## Credits
Thanks to the developers of the awesome solutions [HypeMan](https://github.com/robscallsign/HypeMan) and [perun](https://github.com/szporwolik/perun), that gave me the main ideas to this 
solution. I gave my best to mark the few parts in the code to show where I copied some ideas or even code from you guys, 
which honestly is just a very small piece. Hope that is ok. Also thanks to Moose for aligning the API for [FunkMan](https://github.com/funkyfranky/FunkMan) 
with me and make it compatible with DCSServerBot in first place.
