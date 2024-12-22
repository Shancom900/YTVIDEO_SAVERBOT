from telegram import Update, InputFile, InputMediaDocument
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp
import os
from time import time, strftime

# Replace with your actual bot token and channel usernames
BOT_TOKEN = "7904555084:AAEIHudaLyuN-hIagfaHkXTkype2dR3NkQA"
CHANNEL_USERNAME = "@GlobalTalkers"
LOG_CHANNEL_USERNAME = "@SH0NU_BOTLOGS"

USER_DATA_FILE = "ytdownuser.txt"
last_upload_time = 0  # Track the last time the file was uploaded
last_uploaded_message_id = None  # Track the message ID of the last uploaded file

def save_user_data(username, user_id):
    """Save username and user_id to the file only if not already present."""
    try:
        # Read existing user data
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        # Check if the user already exists
        user_exists = any(f"{username}, {user_id}\n" == line for line in lines)

        # Add user only if they don't already exist
        if not user_exists:
            with open(USER_DATA_FILE, "a") as f:
                f.write(f"{username}, {user_id}\n")
    except Exception as e:
        print(f"Error saving user data: {e}")

async def upload_user_data(context: CallbackContext):
    """Upload the user data file to the specified channel, replacing old uploads."""
    global last_uploaded_message_id
    try:
        # Title with bot username and timestamp
        title = f"@YTVIDEO_SAVERBOT User Data\nDate & Time: {strftime('%Y-%m-%d %H:%M:%S')}"

        with open(USER_DATA_FILE, "rb") as file:
            if last_uploaded_message_id:
                # Replace previous file
                await context.bot.edit_message_media(
                    chat_id=LOG_CHANNEL_USERNAME,
                    message_id=last_uploaded_message_id,
                    media=InputMediaDocument(file, caption=title)
                )
            else:
                # Upload the file as a new message
                msg = await context.bot.send_document(
                    chat_id=LOG_CHANNEL_USERNAME,
                    document=InputFile(file),
                    caption=title
                )
                last_uploaded_message_id = msg.message_id  # Save the message ID for future edits
    except Exception as e:
        print(f"Error uploading user data: {e}")

async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message and check for channel membership."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Save the user data to the file
    save_user_data(username, user_id)

    # Check if user is in the required channel
    chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
    if chat_member.status in ["member", "administrator", "creator"]:
        await update.message.reply_text("Welcome! Send me a YouTube link, and I'll download the video for you.")
    else:
        await update.message.reply_text(f"Please join the channel {CHANNEL_USERNAME} to use this bot.")

    # Upload the user data file
    await upload_user_data(context)

async def download_video(update: Update, context: CallbackContext) -> None:
    """Download video from YouTube and send to user."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    if "youtube.com" in user_message or "youtu.be" in user_message:
        progress_message = await update.message.reply_text("Downloading your video... 0% completed.")

        def progress_hook(d):
            if d['status'] == 'downloading':
                percentage = d['_percent_str'].strip()
                context.bot.edit_message_text(
                    f"Downloading your video... {percentage} completed.",
                    chat_id=chat_id,
                    message_id=progress_message.message_id
                )

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'nocolor': True,
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([user_message])

            with open("video.mp4", "rb") as video:
                await context.bot.send_video(chat_id=chat_id, video=video)

            await update.message.reply_text("Here is your video!")
            os.remove("video.mp4")
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {e}")
    else:
        await update.message.reply_text("Please send a valid YouTube link.")

def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Message handler for receiving the YouTube video link
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
