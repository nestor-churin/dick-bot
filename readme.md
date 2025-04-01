# Dick Bot 🍆

A fun Telegram bot that lets users in group chats play a game measuring their virtual "sizes".

## Features

- Daily size measurements with random changes
- Group and global leaderboards
- Admin controls for resetting group data
- Captcha verification for sensitive operations
- Cooldown system (24 hours between attempts)
- Support for multiple groups

## Commands

- `/start` - Show bot introduction
- `/help` - Display available commands
- `/dick` - Get your daily measurement
- `/my_dick` - Check your current stats
- `/top_dick` - View top 10 players in current group
- `/global_top` - View global top 10 players
- `/reset` - Reset group data (admin only)
- `/tos` - Show Terms of Service

## Setup

1. Create a new bot via [@BotFather](https://t.me/BotFather) and get your bot token
2. Clone this repository
3. Install requirements:
```sh
pip install -r requirements.txt
```
4. Configure the bot by editing `config.yaml`:
```yaml
BOT_TOKEN: "your_bot_token_here"
API_ID: your_api_id_here
API_HASH: "your_api_hash_here"

#SETTINGS
random_min: 10
random_max: 20
```
5. Run the bot:
```sh
python bot.py
```

## Requirements

- Python 3.7+
- pyrogram
- aiosqlite
- pyyaml
- aiofiles

## Privacy & Terms

- Bot stores only essential data (user ID, username, chat ID)
- Data can be reset by group admins
- Intended for users 16+
- For entertainment purposes only

## Author

Developed by [nestor_churin](t.me/nestor_churin)
Version: 1.0.0 R

## License

[MIT License](https://github.com/nestor-churin/dick-bot/blob/main/LICENSE)
