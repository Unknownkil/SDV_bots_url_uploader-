import telebot
import os
from telebot import types
import time

# Telegram bot token
TOKEN = '7610132838:AAFCZHxS96lqIejFQAfjcRjnjhm-GHMPZb0'
bot = telebot.TeleBot(TOKEN)

# Bot start confirmation
print(" bot start ho gya GuRu")

# Global temp_data dictionary for storing temporary data
temp_data = {}

# Authorized users with expiration times
authorized_users = {
    '5443679321': float('inf')  # Permanent authorization for the owner
}

# Function to check if user is authorized
def is_authorized(user_id):
    return user_id in authorized_users and time.time() < authorized_users[user_id]

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if not is_authorized(user_id):
        bot.send_message(message.chat.id, " Unauthorized access.")
        return

    username = message.from_user.username or "User"
    welcome_text = f" Welcome, @{username}! Welcome to the Ultimate Bot \nChoose an option below to get started:"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    owner_btn = types.InlineKeyboardButton(" Owner", url="https://t.me/Ansh2561")
    developer_btn = types.InlineKeyboardButton(" Developer", url="https://t.me/unknownkiller7777")
    functions_btn = types.InlineKeyboardButton(" Functions", callback_data="show_functions")
    markup.add(owner_btn, developer_btn, functions_btn)
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# /addid command
@bot.message_handler(commands=['addid'])
def add_user(message):
    user_id = str(message.from_user.id)
    if user_id != '5443679321':
        bot.send_message(message.chat.id, " Only the owner can use this command.")
        return

    msg = bot.send_message(message.chat.id, "Please send the user ID to authorize.")
    bot.register_next_step_handler(msg, ask_for_duration)

def ask_for_duration(message):
    user_to_add = message.text.strip()
    temp_data["user_to_add"] = user_to_add

    markup = types.InlineKeyboardMarkup()
    durations = {
        "1 month": 30 * 24 * 3600,
        "2 months": 2 * 30 * 24 * 3600,
        "5 months": 5 * 30 * 24 * 3600,
        "10 months": 10 * 30 * 24 * 3600,
        "1 year": 365 * 24 * 3600
    }

    for label, seconds in durations.items():
        markup.add(types.InlineKeyboardButton(label, callback_data=f"authorize_{seconds}"))
    
    bot.send_message(message.chat.id, "Kitne time ke liye authorization dena chahte hain?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("authorize_"))
def authorize_user(call):
    user_id = temp_data.get("user_to_add")
    if not user_id:
        bot.send_message(call.message.chat.id, " User ID not found.")
        return

    duration = int(call.data.split("_")[1])
    authorized_users[user_id] = time.time() + duration
    bot.answer_callback_query(call.id, " User authorized successfully!")
    bot.delete_message(call.message.chat.id, call.message.message_id)

# Callback for functions
@bot.callback_query_handler(func=lambda call: call.data == "show_functions")
def show_functions(call):
    delete_message(call)
    markup = types.InlineKeyboardMarkup()
    url_uploader_btn = types.InlineKeyboardButton("URL Uploader ", callback_data="url_uploader")
    bulk_uploader_btn = types.InlineKeyboardButton("Bulk Uploader ", callback_data="bulk_uploader")
    markup.add(url_uploader_btn, bulk_uploader_btn)
    
    bot.send_message(call.message.chat.id, "Choose an option:", reply_markup=markup)

# Delete message after selecting button
def delete_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# URL Uploader Functionality
@bot.callback_query_handler(func=lambda call: call.data == "url_uploader")
def url_uploader_start(call):
    delete_message(call)
    msg = bot.send_message(call.message.chat.id, "Please send the download link ")
    bot.register_next_step_handler(msg, process_download_link)

def process_download_link(message):
    url = message.text
    markup = types.InlineKeyboardMarkup()
    yes_btn = types.InlineKeyboardButton("Yes", callback_data="custom_name")
    no_btn = types.InlineKeyboardButton("No", callback_data="default_name")
    markup.add(yes_btn, no_btn)
    
    bot.send_message(message.chat.id, "Do you want to give it a name?", reply_markup=markup)
    
    # Store link in temp_data
    temp_data["url"] = url
    temp_data["chat_id"] = message.chat.id

@bot.callback_query_handler(func=lambda call: call.data == "custom_name")
def ask_name(call):
    delete_message(call)
    msg = bot.send_message(call.message.chat.id, "Please send the name:")
    bot.register_next_step_handler(msg, download_file, custom_name=True)

@bot.callback_query_handler(func=lambda call: call.data == "default_name")
def download_with_default_name(call):
    delete_message(call)
    download_file(call.message, custom_name=False)

def download_file(message, custom_name=False):
    chat_id = message.chat.id
    url = temp_data.get("url", "")
    name = message.text if custom_name else "default_file"
    
    if ".pdf" in url:
        file_extension = ".pdf"
        download_command = f"curl -o '{name}{file_extension}' '{url}'"
    else:
        file_extension = ".mp4"
        download_command = f"ffmpeg -i '{url}' -c copy '{name}{file_extension}'"

    try:
        bot.send_message(chat_id, "Starting download... ")
        os.system(download_command)
        
        with open(name + file_extension, "rb") as file:
            bot.send_document(chat_id, file)
        
        os.remove(name + file_extension)
        bot.send_message(chat_id, " Download complete and file sent.")
    except Exception as e:
        bot.send_message(chat_id, f" Error: {e}")

# Bulk Uploader Functionality
@bot.callback_query_handler(func=lambda call: call.data == "bulk_uploader")
def bulk_uploader_start(call):
    msg = bot.send_message(call.message.chat.id, "Please send the TXT file containing the URLs ")
    bot.register_next_step_handler(msg, process_txt_file)

def process_txt_file(message):
    if not message.document:
        bot.send_message(message.chat.id, " Please upload a valid TXT file.")
        return
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"{message.document.file_name}"
    
    with open(file_path, "wb") as f:
        f.write(downloaded_file)
    
    video_links, pdf_links = [], []
    with open(file_path, "r") as f:
        for line in f:
            name, url = line.split(":", 1)
            if ".pdf" in url:
                pdf_links.append((name.strip(), url.strip()))
            else:
                video_links.append((name.strip(), url.strip()))
    
    os.remove(file_path)  # Clean up after parsing
    
    markup = types.InlineKeyboardMarkup()
    videos_btn = types.InlineKeyboardButton(f"DL Only Videos  ({len(video_links)})", callback_data="dl_videos")
    pdfs_btn = types.InlineKeyboardButton(f"DL Only PDFs  ({len(pdf_links)})", callback_data="dl_pdfs")
    both_btn = types.InlineKeyboardButton("DL Both ", callback_data="dl_both")
    markup.add(videos_btn, pdfs_btn, both_btn)
    
    bot.send_message(message.chat.id, "Choose download option:", reply_markup=markup)
    
    # Store links in temp_data for later download
    temp_data["video_links"] = video_links
    temp_data["pdf_links"] = pdf_links

@bot.callback_query_handler(func=lambda call: call.data in ["dl_videos", "dl_pdfs", "dl_both"])
def bulk_download_handler(call):
    video_links = temp_data.get("video_links", [])
    pdf_links = temp_data.get("pdf_links", [])
    
    if call.data == "dl_videos":
        files = video_links
    elif call.data == "dl_pdfs":
        files = pdf_links
    else:
        files = video_links + pdf_links
    
    bot.send_message(call.message.chat.id, "Starting bulk download... ")
    
    for name, url in files:
        if ".pdf" in url:
            file_extension = ".pdf"
            download_command = f"curl -o '{name}{file_extension}' '{url}'"
        else:
            file_extension = ".mp4"
            download_command = f"ffmpeg -i '{url}' -c copy '{name}{file_extension}'"

        try:
            bot.send_message(call.message.chat.id, f"Starting download for {name}... ")
            os.system(download_command)
            
            with open(name + file_extension, "rb") as file:
                bot.send_document(call.message.chat.id, file)
            
            os.remove(name + file_extension)  # Remove the file after sending
            bot.send_message(call.message.chat.id, f" Download complete for {name}.")
        except Exception as e:
            bot.send_message(call.message.chat.id, f" Error downloading {name}: {e}")

    bot.send_message(call.message.chat.id, " All selected files have been processed.")

# Start the bot
bot.polling(non_stop=True)