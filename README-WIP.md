```
sudo apt update
```
#
```
sudo apt upgrade -y
```
#
```
sudo apt install python3 python3-pip -y
```
#
```
pip3 install -U py-cord
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
nano bot.py
```
#
```
nano .env
```
#
```
DISCORD_BOT_TOKEN=your-bot-token
```
#
```
chmod 600 .env
```
#
```
python3 bot.py
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
WorkingDirectory=/path/to/your/discord_bot
ExecStart=/usr/bin/python3 /path/to/your/discord_bot/bot.py
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
sudo systemctl status discord-bot.service
```
#
```
sudo systemctl restart discord-bot.service
```
#
```
https://discord.com/oauth2/authorize?client_id=APPLICATION_ID&permissions=563261338561600&integration_type=0&scope=bot+applications.commands
```

