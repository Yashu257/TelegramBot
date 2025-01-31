
##BOT NAME IS YashuAvatarbot 
##Search in Telegram While running this Code and start to use it


import google.generativeai as genai
from typing import Final
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from datetime import datetime
import os

# Configure Google AI
genai.configure(api_key="AIzaSyCF0nZaDwlKC7r6DVV5rEuZ1q5d54S-bCo")  # Replace with your Gemini API key

# Define Telegram Bot Token
TOKEN: Final = '7266101311:AAFitgMFuE_E1XUAHIQMVA1K3dv6bC6lVJE'  # Replace with your Telegram Bot Token
BOT_USERNAME: Final = '@YourBotUsername'

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017")  # Change URL if using MongoDB Atlas
db = client["telegram_bot"]  # Database name
users_collection = db["users"]  # Collection for user registration
chat_collection = db["chat_history"]  # Collection for chat history
files_collection = db["file_metadata"]  # Collection for storing file metadata

# Function to save user details in MongoDB
def save_user(user_id, first_name, username, phone_number=None):
    user_data = {
        "user_id": user_id,
        "first_name": first_name,
        "username": username,
        "phone_number": phone_number,
        "registered_at": datetime.now()
    }
    
    # Check if user already exists and update phone number if provided
    existing_user = users_collection.find_one({"user_id": user_id})
    if existing_user:
        users_collection.update_one({"user_id": user_id}, {"$set": {"phone_number": phone_number}})
    else:
        users_collection.insert_one(user_data)

# Function to store chat history
def save_chat(user_id, user_message, bot_response):
    chat_entry = {
        "user_id": user_id,
        "user_message": user_message,
        "bot_response": bot_response,
        "timestamp": datetime.now()
    }
    chat_collection.insert_one(chat_entry)

# Function to store file metadata
def save_file_metadata(user_id, file_name, file_description):
    file_data = {
        "user_id": user_id,
        "file_name": file_name,
        "file_description": file_description,
        "timestamp": datetime.now()
    }
    files_collection.insert_one(file_data)

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    # Check if phone number already exists
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data.get("phone_number"):
        await update.message.reply_text(f"Hello {user.first_name}, your phone number is already stored: {user_data['phone_number']}")
    else:
        # Request phone number if not saved
        keyboard = [[KeyboardButton("Send my phone number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Please share your phone number:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
 *Available Commands:*
- `/start` → Register & start chat (requests phone number if not stored)
- `/help` → Show available commands
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Handle Phone Number
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    phone_number = update.message.contact.phone_number
    user_id = user.id

    # Save phone number in MongoDB
    save_user(user_id, user.first_name, user.username, phone_number)

    # Send confirmation message
    await update.message.reply_text(f"Thank you, {user.first_name}! Your phone number {phone_number} has been successfully saved!")

# Google Gemini API for AI responses
async def generate_ai_response(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Web Search Command
async def websearch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = " ".join(context.args)

    if not user_query:
        await update.message.reply_text("Please provide a search query. Example: `/websearch AI news`")
        return

    # Perform Web Search (You need to implement the search functionality here, use Google's Custom Search API)

    # Send Results to User
    await update.message.reply_text(f"Search results for {user_query} coming soon...")

# Handle Image/Document files
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        file_name = f"{file.file_unique_id}.jpg"
    elif update.message.document:
        file = await update.message.document.get_file()
        file_name = file.file_name
    else:
        return

    local_file_path = os.path.join(os.getcwd(), file_name)
    await file.download_to_drive(custom_path=local_file_path)

    description = await generate_ai_response(f"Describe the content of this file: {file_name}")
    save_file_metadata(user_id, file_name, description)

    await update.message.reply_text(f"File saved and described as: {description}")

# Handle Messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_message = update.message.text

    bot_response = await generate_ai_response(user_message)
    await update.message.reply_text(bot_response)
    save_chat(user.id, user_message, bot_response)

# Main Function
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Add Command Handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('websearch', websearch_command))  # Adding the web search command
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_image))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Start the Bot
    print("Bot is running...")
    app.run_polling(poll_interval=3)
