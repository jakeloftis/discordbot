#
```
sudo apt update && sudo apt upgrade -y
```
#
```
sudo apt install python3 python3-pip -y
```
#
```
sudo apt install sqlite3 -y
```
#
```
pip3 install discord.py python-dotenv
```
#
```
mkdir discord_bot
```
#
```
cd discord_bot
```
#
```
nano .env
```
#
```
DISCORD_BOT_TOKEN=your_discord_bot_token_here
```
#
```
sudo nano /etc/systemd/system/discord-bot.service
```
#
```
[Unit]
Description=Discord Bot Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/ubuntu/discord_bot/
ExecStart=/usr/bin/python3 /home/ubuntu/discord_bot/bot.py
Restart=on-failure
Environment=DISCORD_BOT_TOKEN=your-bot-token

[Install]
WantedBy=multi-user.target
```
#
```
sudo systemctl daemon-reload
```
#
```
sudo systemctl enable discord-bot.service
```
#
```
sudo systemctl start discord-bot.service
```
#
```
sudo systemctl restart discord-bot.service
```
#
```
sudo journalctl -u discord-bot.service
```






