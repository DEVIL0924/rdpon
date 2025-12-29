# bot_python.py - English Version
import telebot
import os
import subprocess
import json
import time
import psutil
import threading
from datetime import datetime
from pathlib import Path

TOKEN = input("7342954599:AAFK38xhJxNi3B--BuxtYqTUZERibUCYyYw")
OWNER_ID = input("6462069341")

bot = telebot.TeleBot(TOKEN)

DATA_DIR = "bot_data"
FILES_DIR = os.path.join(DATA_DIR, "python_files")
PROCESSES_FILE = os.path.join(DATA_DIR, "processes.json")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

running_processes = {}

def load_processes():
    global running_processes
    if os.path.exists(PROCESSES_FILE):
        try:
            with open(PROCESSES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for file_id, info in data.items():
                    if 'pid' in info:
                        if psutil.pid_exists(info['pid']):
                            try:
                                process = psutil.Process(info['pid'])
                                if process.is_running():
                                    running_processes[file_id] = info
                            except:
                                pass
        except:
            running_processes = {}
    return running_processes

def save_processes():
    with open(PROCESSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(running_processes, f, ensure_ascii=False, indent=2)

def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

def run_python_file(file_path, file_id):
    log_file = os.path.join(LOGS_DIR, f"{file_id}.log")
    
    # Use nohup to run in background
    cmd = f"nohup python3 -u {file_path} > {log_file} 2>&1 &"
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setpgrp
    )
    
    time.sleep(1)
    
    # Find the actual process ID
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'python3' in ' '.join(cmdline) and file_path in ' '.join(cmdline):
                pid = proc.info['pid']
                running_processes[file_id] = {
                    'pid': pid,
                    'file_path': file_path,
                    'start_time': datetime.now().isoformat(),
                    'log_file': log_file
                }
                save_processes()
                return pid
        except:
            continue
    
    return None

def stop_process(file_id):
    if file_id in running_processes:
        pid = running_processes[file_id]['pid']
        try:
            process = psutil.Process(pid)
            # Kill child processes first
            for child in process.children(recursive=True):
                child.kill()
            process.kill()
            del running_processes[file_id]
            save_processes()
            return True
        except:
            del running_processes[file_id]
            save_processes()
            return False
    return False

def get_process_status(file_id):
    if file_id not in running_processes:
        return "Stopped"
    
    pid = running_processes[file_id]['pid']
    try:
        process = psutil.Process(pid)
        if process.is_running():
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / 1024 / 1024
            return f"Running\n💾 Memory: {memory:.2f} MB\n⚡ CPU: {cpu:.1f}%"
        else:
            del running_processes[file_id]
            save_processes()
            return "Stopped"
    except:
        del running_processes[file_id]
        save_processes()
        return "Stopped"

def get_main_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("📤 Upload New File", callback_data="upload"),
        telebot.types.InlineKeyboardButton("📋 Uploaded Files", callback_data="list_files"),
        telebot.types.InlineKeyboardButton("🔄 Active Processes", callback_data="active_processes"),
        telebot.types.InlineKeyboardButton("🗑️ Delete All", callback_data="delete_all")
    )
    return markup

def get_file_menu(file_id):
    status = get_process_status(file_id)
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    if "Running" in status:
        markup.add(
            telebot.types.InlineKeyboardButton("⏹️ Stop", callback_data=f"stop_{file_id}"),
            telebot.types.InlineKeyboardButton("📊 Status", callback_data=f"status_{file_id}")
        )
    else:
        markup.add(
            telebot.types.InlineKeyboardButton("▶️ Start", callback_data=f"start_{file_id}")
        )
    
    markup.add(
        telebot.types.InlineKeyboardButton("📄 Logs", callback_data=f"logs_{file_id}"),
        telebot.types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{file_id}"),
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="list_files")
    )
    
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Sorry, this bot is for owner only")
        return
    
    welcome_text = """
🤖 Welcome to Python File Runner Bot

✨ Features:
• Run Python files permanently
• Full file and process management
• Continuous running even after bot restart
• Performance monitoring and logs

Choose from menu below:
"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if not is_owner(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Not authorized")
        return
    
    if call.data == "upload":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📤 Send Python (.py) file now:")
        bot.register_next_step_handler(call.message, handle_file_upload)
    
    elif call.data == "list_files":
        bot.answer_callback_query(call.id)
        files = [f for f in os.listdir(FILES_DIR) if f.endswith('.py')]
        
        if not files:
            bot.edit_message_text(
                "📋 No uploaded files",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_menu()
            )
            return
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for file_name in files:
            file_id = file_name[:-3]
            status = "🟢" if file_id in running_processes else "🔴"
            markup.add(
                telebot.types.InlineKeyboardButton(
                    f"{status} {file_name}",
                    callback_data=f"file_{file_id}"
                )
            )
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
        
        bot.edit_message_text(
            "📋 Uploaded Files:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data.startswith("file_"):
        bot.answer_callback_query(call.id)
        file_id = call.data.replace("file_", "")
        file_path = os.path.join(FILES_DIR, f"{file_id}.py")
        
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ File not found")
            return
        
        status = get_process_status(file_id)
        file_info = f"""
📄 File: {file_id}.py
📊 Status: {status}
"""
        
        bot.edit_message_text(
            file_info,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_file_menu(file_id)
        )
    
    elif call.data.startswith("start_"):
        file_id = call.data.replace("start_", "")
        file_path = os.path.join(FILES_DIR, f"{file_id}.py")
        
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ File not found")
            return
        
        pid = run_python_file(file_path, file_id)
        
        if pid:
            bot.answer_callback_query(call.id, f"✅ Started successfully (PID: {pid})")
        else:
            bot.answer_callback_query(call.id, "❌ Failed to start")
        
        status = get_process_status(file_id)
        file_info = f"""
📄 File: {file_id}.py
📊 Status: {status}
"""
        
        bot.edit_message_text(
            file_info,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_file_menu(file_id)
        )
    
    elif call.data.startswith("stop_"):
        file_id = call.data.replace("stop_", "")
        
        if stop_process(file_id):
            bot.answer_callback_query(call.id, "✅ Stopped successfully")
        else:
            bot.answer_callback_query(call.id, "⚠️ Already stopped")
        
        status = get_process_status(file_id)
        file_info = f"""
📄 File: {file_id}.py
📊 Status: {status}
"""
        
        bot.edit_message_text(
            file_info,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_file_menu(file_id)
        )
    
    elif call.data.startswith("status_"):
        file_id = call.data.replace("status_", "")
        status = get_process_status(file_id)
        
        bot.answer_callback_query(call.id, f"Status: {status}")
    
    elif call.data.startswith("logs_"):
        bot.answer_callback_query(call.id)
        file_id = call.data.replace("logs_", "")
        log_file = os.path.join(LOGS_DIR, f"{file_id}.log")
        
        if not os.path.exists(log_file):
            bot.send_message(call.message.chat.id, "📄 No logs yet")
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
            
            if not logs.strip():
                bot.send_message(call.message.chat.id, "📄 Logs are empty")
                return
            
            if len(logs) > 4000:
                logs = logs[-4000:]
            
            bot.send_message(call.message.chat.id, f"📄 Logs:\n\n```\n{logs}\n```", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error reading logs: {str(e)}")
    
    elif call.data.startswith("delete_"):
        file_id = call.data.replace("delete_", "")
        
        stop_process(file_id)
        
        file_path = os.path.join(FILES_DIR, f"{file_id}.py")
        log_file = os.path.join(LOGS_DIR, f"{file_id}.log")
        
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(log_file):
            os.remove(log_file)
        
        bot.answer_callback_query(call.id, "✅ Deleted successfully")
        
        files = [f for f in os.listdir(FILES_DIR) if f.endswith('.py')]
        
        if not files:
            bot.edit_message_text(
                "📋 No uploaded files",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_menu()
            )
            return
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for file_name in files:
            file_id_temp = file_name[:-3]
            status = "🟢" if file_id_temp in running_processes else "🔴"
            markup.add(
                telebot.types.InlineKeyboardButton(
                    f"{status} {file_name}",
                    callback_data=f"file_{file_id_temp}"
                )
            )
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
        
        bot.edit_message_text(
            "📋 Uploaded Files:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data == "active_processes":
        bot.answer_callback_query(call.id)
        
        if not running_processes:
            bot.edit_message_text(
                "🔄 No active processes",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_menu()
            )
            return
        
        processes_text = "🔄 Active Processes:\n\n"
        
        for file_id, info in running_processes.items():
            status = get_process_status(file_id)
            processes_text += f"📄 {file_id}.py\n{status}\n\n"
        
        bot.edit_message_text(
            processes_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_menu()
        )
    
    elif call.data == "delete_all":
        bot.answer_callback_query(call.id)
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Yes, Delete All", callback_data="confirm_delete_all"),
            telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            "⚠️ Are you sure you want to delete all files and processes?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data == "confirm_delete_all":
        bot.answer_callback_query(call.id)
        
        for file_id in list(running_processes.keys()):
            stop_process(file_id)
        
        for file_name in os.listdir(FILES_DIR):
            if file_name.endswith('.py'):
                os.remove(os.path.join(FILES_DIR, file_name))
        
        for log_file in os.listdir(LOGS_DIR):
            if log_file.endswith('.log'):
                os.remove(os.path.join(LOGS_DIR, log_file))
        
        bot.edit_message_text(
            "✅ All files and processes deleted successfully",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_menu()
        )
    
    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        
        welcome_text = """
🤖 Main Control Panel

✨ Features:
• Run Python files permanently
• Full file and process management
• Continuous running even after bot restart
• Performance monitoring and logs

Choose from menu below:
"""
        
        bot.edit_message_text(
            welcome_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_menu()
        )

def handle_file_upload(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Not authorized")
        return
    
    if not message.document:
        bot.reply_to(message, "❌ Please send a file")
        return
    
    if not message.document.file_name.endswith('.py'):
        bot.reply_to(message, "❌ File must be .py format")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name
        file_path = os.path.join(FILES_DIR, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        file_id = file_name[:-3]
        markup.add(
            telebot.types.InlineKeyboardButton("▶️ Start Now", callback_data=f"start_{file_id}"),
            telebot.types.InlineKeyboardButton("📋 File List", callback_data="list_files"),
            telebot.types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        
        bot.reply_to(message, f"✅ File uploaded successfully: {file_name}", reply_markup=markup)
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Not authorized")
        return
    
    handle_file_upload(message)

def monitor_processes():
    while True:
        try:
            for file_id in list(running_processes.keys()):
                get_process_status(file_id)
            time.sleep(30)
        except:
            pass

monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
monitor_thread.start()

if __name__ == "__main__":
    print("🤖 Starting bot...")
    load_processes()
    print(f"✅ Loaded {len(running_processes)} active processes")
    bot.infinity_polling()