import discord
from discord.ext import commands, tasks
import random
import asyncio
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import re

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Intents and command prefix
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# SQLite setup
DB_FILE = "reminders.db"

def init_db():
    """Initialize the database and create the reminders table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_reminder_to_db(user_id, channel_id, message, timestamp):
    """Add a reminder to the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reminders (user_id, channel_id, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, channel_id, message, timestamp))
    conn.commit()
    conn.close()

def remove_reminder_from_db(reminder_id):
    """Remove a reminder from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def load_reminders_from_db():
    """Load all reminders from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, user_id, channel_id, message, timestamp FROM reminders')
    reminders = c.fetchall()
    conn.close()
    return reminders

# Scheduler function
async def schedule_reminder(reminder_id, user_id, channel_id, message, time_remaining):
    """Schedule a reminder to trigger after the given duration."""
    print(f"Scheduling reminder for user {user_id} in channel {channel_id} in {time_remaining} seconds: {message}")
    await asyncio.sleep(time_remaining)
    try:
        channel = bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title="⏰ Reminder",
                description=message,
                color=discord.Color.red(),
            )
            await channel.send(f"<@{user_id}>", embed=embed)
            print(f"Sent reminder to channel {channel.name}: {message}")
        else:
            print(f"Channel with ID {channel_id} could not be found.")
    except Exception as e:
        print(f"Error sending reminder to channel {channel_id}: {e}")
    finally:
        remove_reminder_from_db(reminder_id)

# Events
@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    init_db()

    # Restart pending reminders
    current_time = datetime.now(timezone.utc).timestamp()
    for reminder in load_reminders_from_db():
        reminder_id, user_id, channel_id, message, timestamp = reminder
        time_remaining = timestamp - current_time
        if time_remaining > 0:
            asyncio.create_task(schedule_reminder(reminder_id, user_id, channel_id, message, time_remaining))
        else:
            print(f"Removing expired reminder from database: {reminder}")
            remove_reminder_from_db(reminder_id)

# Slash commands
@bot.slash_command(name="remind", description="Set a reminder with combined durations (e.g., 1w2d3h4m).")
async def remind(ctx, duration: str, *, reminder_message: str):
    time_multiplier = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800}
    total_seconds = 0

    # Parse combined durations like "1w2d3h4m"
    matches = re.findall(r'(\d+)([wdhm])', duration)
    if not matches:
        await ctx.respond("Invalid format. Use a combination like 1w2d3h4m (weeks, days, hours, minutes).")
        return

    for amount, unit in matches:
        total_seconds += int(amount) * time_multiplier[unit]

    if total_seconds <= 0:
        await ctx.respond("The reminder duration must be greater than 0.", ephemeral=True)
        return

    # Calculate reminder timestamp
    timestamp = datetime.now(timezone.utc).timestamp() + total_seconds

    # Add reminder to the database
    add_reminder_to_db(ctx.author.id, ctx.channel.id, reminder_message, timestamp)

    embed = discord.Embed(
        title="⏰ Reminder Set",
        description=f"I'll remind you in {duration} ({total_seconds} seconds).",
        color=discord.Color.orange(),
    )
    await ctx.respond(embed=embed)

    # Schedule the reminder
    asyncio.create_task(schedule_reminder(None, ctx.author.id, ctx.channel.id, reminder_message, total_seconds))

@bot.slash_command(name="view_reminders", description="View all active reminders")
async def view_reminders(ctx):
    reminders = load_reminders_from_db()
    if not reminders:
        await ctx.respond("There are no active reminders right now.", ephemeral=True)
        return

    embed = discord.Embed(title="⏰ Active Reminders", color=discord.Color.blue())
    current_time = datetime.now(timezone.utc).timestamp()
    has_active_reminders = False

    for reminder_id, user_id, channel_id, message, timestamp in reminders:
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)  # Fetch the user object
        username = user.name if user else "Unknown User"  # Fallback if user is not found

        time_remaining = int(timestamp - current_time)
        if time_remaining <= 0:
            continue  # Skip expired reminders

        has_active_reminders = True
        embed.add_field(
            name=f"#{reminder_id} Reminder",
            value=(
                f"**Created by:** {username}\n"
                f"**Message:** {message}\n"
                f"**Time Remaining:** {time_remaining} seconds"
            ),
            inline=False,
        )

    if not has_active_reminders:
        await ctx.respond("You have no active reminders.", ephemeral=True)
    else:
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="delete_reminder", description="Delete a reminder by its ID")
async def delete_reminder(ctx, reminder_id: int):
    """Delete a specific reminder by its ID."""
    reminders = load_reminders_from_db()
    reminder_to_delete = None

    # Check if the reminder exists and belongs to the user
    for reminder in reminders:
        if reminder[0] == reminder_id and reminder[1] == ctx.author.id:  # Match ID and user_id
            reminder_to_delete = reminder
            break

    if reminder_to_delete is None:
        await ctx.respond("Reminder not found or you don't have permission to delete it.", ephemeral=True)
        return

    # Remove the reminder from the database
    remove_reminder_from_db(reminder_id)

    embed = discord.Embed(
        title="🗑 Reminder Deleted",
        description=f"Successfully deleted reminder ID #{reminder_id}.",
        color=discord.Color.green(),
    )
    await ctx.respond(embed=embed)

@bot.slash_command(name="roll", description="Roll a random number between a given range")
async def roll(ctx, min: int, max: int):
    if min >= max:
        await ctx.respond("Invalid range. Please make sure min is less than max.")
        return
    result = random.randint(min, max)
    await ctx.respond(f'🎲 You rolled: {result}')

@bot.slash_command(name="poll", description="Create a poll with options")
async def poll(ctx, title: str, options: str):
    option_list = options.split(",")
    if len(option_list) < 2:
        await ctx.respond("Please provide at least two options, separated by commas.")
        return
    elif len(option_list) > 20:
        await ctx.respond("Too many options. Please limit to 20 options or less.")
        return

    embed = discord.Embed(title=title, color=discord.Color.blue())
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
                 "🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯"]
    description = "\n".join([f'{reactions[i]} {option}' for i, option in enumerate(option_list)])
    embed.description = description
    
    message = await ctx.respond(embed=embed)
    message = await message.original_response()
    
    for i in range(len(option_list)):
        await message.add_reaction(reactions[i])

@bot.slash_command(name="choose", description="Enter choices separated by commas ,")
async def choose(ctx: discord.ApplicationContext, options: str):
    """
    Allows the user to enter options separated by a comma.
    Example usage: /choose "Game 1, Game 2, Game 3"
    """
    try:
        # Split options by commas, trimming any extra spaces
        options_list = [option.strip() for option in options.split(",") if option.strip()]
        print(f"Received options: {options_list}")  # Debug: Show list of options

        if len(options_list) < 2:
            await ctx.respond("Please provide at least two options separated by commas.", ephemeral=True)
            print("Error: Less than two options provided.")
            return

        # Shuffle the list before making a choice
        random.shuffle(options_list)
        choice = options_list[0]
        print(f"Selected choice: {choice}")  # Debug: Show the selected choice

        await ctx.respond(f'🤖 I choose: **{choice}**')
    except Exception as e:
        print(f"Error in /choose command: {e}")
        await ctx.respond("Something went wrong while processing your request.", ephemeral=True)

# Run the bot
bot.run(TOKEN)
