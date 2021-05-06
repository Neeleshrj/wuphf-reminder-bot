# discord-reminder-bot
A basic Reminder Bot for Discord on discord.py and firebase


## Vitual Environment Setup 
- `cd /path/to/project` : change directory to project directory
- `python -m venv .` : make a vitual environment inside project directory
- enter virtual environment
  - for linux: `source bin/activate`
  - for windows: `Scripts\activate`
  
## Package Installation
- `python -m pip intall -r requirements.txt` : this will install all necessary packages

## Adding Environment Variables
- Firebase
  - enable firestore in firebase
  - generate service account credentials in firebase and the required json as shown in `serviceKey.template.json`
- Discord
  - add a bot in discord developer portal and check/enable administrator and indent permissionsbbot
  - generate a Bot Token and copy it in `.env` file as shown `.env.template`
  
## Run
- `python bot.py` : enjoy!
