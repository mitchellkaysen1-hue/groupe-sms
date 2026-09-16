import telebot
import requests
import time
import re
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# Lamix Bot Configuration
# ==========================================
BOT_TOKEN = '8861443748:AAHSx7yHrRPIyzTq0fazbYwynzP3ON4-UqQ'
CHAT_ID = '-1003919009698'

API_URL = 'https://panel.lamix.org/api/v1/messages'
PANEL_TOKEN = 'M61_HpNtW6tXNgl4k8lgaM7vNnIUUDBq3RQQOvHAnVw'

bot = telebot.TeleBot(BOT_TOKEN)
PROCESSED_DB = 'lamix_processed.json'

# --- JSON Database Logic ---
def load_processed_ids():
    if os.path.exists(PROCESSED_DB):
        try:
            with open(PROCESSED_DB, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed_ids(id_set):
    try:
        to_save = list(id_set)[-200:]
        with open(PROCESSED_DB, 'w') as f:
            json.dump(to_save, f)
    except:
        pass

processed_sms_ids = load_processed_ids()

def extract_otp(message):
    match = re.search(r'(?:is|code|:|💬)\s*([a-zA-Z0-9]{4,8})\b', message, re.IGNORECASE)
    if match:
        return match.group(1)
        
    words = message.strip().split()
    if words:
        last_word = words[-1].strip('.,!:-')
        if 4 <= len(last_word) <= 8:
            return last_word
            
    otp_match = re.search(r'\b[a-zA-Z0-9]{4,8}\b', message)
    return otp_match.group(0) if otp_match else "No OTP"

def format_number(num):
    clean_num = str(num).strip()
    if len(clean_num) >= 6:
        first_three = clean_num[:3]
        last_three = clean_num[-3:]
        return f"{first_three}NB{last_three}"
    return clean_num

# ==========================================
# Main Forwarder Loop
# ==========================================
def start_lamix_forwarder():
    global processed_sms_ids
    print("🚀 Starting Lamix Bot Forwarder...")
    
    while True:
        try:
            params = {
                "token": PANEL_TOKEN
            }
            
            response = requests.get(API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Reading the 'records' array based on your Raw Response
                sms_list = data.get('records', [])

                if isinstance(sms_list, list) and len(sms_list) > 0:
                    for sms in reversed(sms_list):
                        num = str(sms.get('number', 'Unknown')).strip()
                        sms_time = str(sms.get('time', ''))
                        
                        # Unique Identifier
                        msg_unique_id = f"{num}_{sms_time}"
                        
                        if msg_unique_id not in processed_sms_ids:
                            # Correct Keys based on Raw Response: 'content' & 'cli'
                            msg_content = sms.get('content', 'No message')
                            otp = extract_otp(msg_content)
                            
                            service_name = str(sms.get('cli', 'Unknown')).strip()
                            masked_number = format_number(num)
                            
                            text = (
                                f"🎯 <b>NEW SMS RECEIVED!</b>\n\n"
                                f"👤 <b>Number:</b> <code>{masked_number}</code>\n"
                                f"🏢 <b>Service:</b> <code>{service_name}</code>\n"
                                f"💬 <b>Message:</b> {msg_content}\n\n"
                                f"🔑 <b>Code:</b> <code>{otp}</code>"
                            )

                            markup = InlineKeyboardMarkup()
                            markup.row(
                                InlineKeyboardButton("👤 Owner", url="https://t.me/nb269")
                            )

                            try:
                                bot.send_message(CHAT_ID, text, parse_mode='HTML', reply_markup=markup)
                                processed_sms_ids.add(msg_unique_id)
                                save_processed_ids(processed_sms_ids)
                                print(f"✅ Forwarded Message for: {masked_number}")
                                time.sleep(1)
                            except Exception as send_err:
                                print(f"❌ Telegram Send Error: {send_err}")
            else:
                print(f"⚠️ API Http Error Status: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Fetch Error: {e}")
            
        time.sleep(4)

if __name__ == "__main__":
    start_lamix_forwarder()
