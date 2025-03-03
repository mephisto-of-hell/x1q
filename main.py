# main.py
from telethon import TelegramClient, events
from config import BOT_TOKEN, SUPPORTED_LANGUAGES
from database import init_db, set_group_language
from quiz import post_quiz_poll, handle_poll_answer
import asyncio
import datetime

# Initialize the Telegram client
client = TelegramClient('bot', api_id=25120562, api_hash='0bd8eb78385a059f64f6032ebefc4615')

async def scheduler():
    """Schedule quiz polls every hour."""
    while True:
        current_time = datetime.datetime.utcnow()
        groups = db.group_settings.find()
        for group in groups:
            group_id = group["_id"]
            last_poll_time = group.get("last_poll_time")
            if not last_poll_time or (current_time - last_poll_time).total_seconds() >= 3600:
                await post_quiz_poll(client, group_id)
                db.group_settings.update_one(
                    {"_id": group_id},
                    {"$set": {"last_poll_time": current_time}}
                )
        await asyncio.sleep(60)  # Check every minute

@client.on(events.ChatAction)
async def on_group_join(event):
    """Handle bot being added to a group."""
    if event.user_added and event.user_id == (await client.get_me()).id:
        group_id = event.chat_id
        set_group_language(group_id, "en")
        await post_quiz_poll(client, group_id)
        db.group_settings.update_one(
            {"_id": group_id},
            {"$set": {"last_poll_time": datetime.datetime.utcnow()}},
            upsert=True
        )

@client.on(events.NewMessage(pattern=r'/setlanguage (\w+)'))
async def set_language(event):
    """Set the language for the group."""
    if not event.is_group:
        await event.reply("This command works only in groups.")
        return
    language = event.pattern_match.group(1)
    if language in SUPPORTED_LANGUAGES:
        set_group_language(event.chat_id, language)
        await event.reply(f"Language set to {language}")
    else:
        await event.reply(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}")

@client.on(events.PollAnswer)
async def on_poll_answer(event):
    """Process poll answers."""
    await handle_poll_answer(client, event)

async def main():
    """Start the bot and run the scheduler."""
    init_db()
    await client.start(bot_token=BOT_TOKEN)
    client.loop.create_task(scheduler())
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())