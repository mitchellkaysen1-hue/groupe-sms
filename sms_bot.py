import threading
import telebot
import requests
import time
import re
import os
import json
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# ১. আগের বটের তথ্য (গ্রুপ ১)
# ==========================================
BOT_TOKEN_1 = '8685475963:AAEHIgmsMgNN3lRVF-0ehLEE4Mwadv6KUDs'
CHAT_ID_1 = '-1003919009698'
PANEL_TOKEN_1 = 'Q1ZXQjRSQn5zVlhDZm2FaEljjnRbi5iHW4J0gX5PhUGDImhFYHiQ'
API_URL_1 = 'http://51.77.216.195/crapi/konek/viewstats'

bot1 = telebot.TeleBot(BOT_TOKEN_1)

# ==========================================
# ২. নতুন বটের তথ্য (গ্রুপ ২)
# ==========================================
BOT_TOKEN_2 = '8861443748:AAHSx7yHrRPIyzTq0fazbYwynzP3ON4-UqQ'
API_URL_2 = 'https://panel.lamix.org/api/v1/messages'
PANEL_TOKEN_2 = 'M61_HpNtW6tXNgl4k8lgaM7vNnIUUDBq3RQQOvHAnVw'

bot2 = telebot.TeleBot(BOT_TOKEN_2)

# ডুপ্লিকেট মেসেজ আইডি সেভ করার ফাইল (উভয় বটের জন্য আলাদা ডাটাবেজ)
PROCESSED_DB_1 = 'group_processed.json'
PROCESSED_DB_2 = 'new_group_processed.json'

# --- ডুপ্লিকেট চেক ডাটাবেজ ফাংশন ---
def load_processed_ids(db_file):
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r') as f:
                return set(json.load(f))
        except: 
            return set()
    return set()

def save_processed_ids(id_set, db_file):
    try:
        to_save = list(id_set)[-200:]
        with open(db_file, 'w') as f:
            json.dump(to_save, f)
    except: 
        pass

processed_sms_ids_1 = load_processed_ids(PROCESSED_DB_1)
processed_sms_ids_2 = load_processed_ids(PROCESSED_DB_2)

def extract_otp(message):
    """মেসেজ থেকে ওটিপি কোড খুঁজে বের করার লজিক"""
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
    """নম্বরের প্রথম ৩ এবং শেষ ৩ ডিজিট রেখে মাঝখানে NB বসানোর লজিক"""
    clean_num = str(num).strip()
    if len(clean_num) >= 6:
        first_three = clean_num[:3]
        last_three = clean_num[-3:]
        return f"{first_three}NB{last_three}"
    return clean_num

# ==========================================
# ৩. আগের বটের ফরোয়ার্ড লুপ (Thread 1)
# ==========================================
def run_bot_1_loop():
    global processed_sms_ids_1
    print("🚀 Bot 1 (Old) Forwarder Loop Started...")
    while True:
        try:
            response = requests.get(f"{API_URL_1}?token={PANEL_TOKEN_1}&records=10", timeout=10)
            if response.status_code == 200:
                full_data = response.json()
                if full_data.get('status') == 'success':
                    sms_list = full_data.get('data', [])
                    if isinstance(sms_list, list):
                        for sms in sms_list:
                            num = str(sms.get('num', 'Unknown')).strip()
                            sms_time = sms.get('dt', '')
                            
                            msg_unique_id = f"{num}_{sms_time}"
                            
                            if msg_unique_id not in processed_sms_ids_1:
                                msg_content = sms.get('message', 'No message')
                                otp = extract_otp(msg_content)
                                
                                service_name = sms.get('service') or sms.get('cli') or 'Unknown'
                                service_name = str(service_name).strip()
                                
                                masked_number = format_number(num)
                                
                                text = (
                                    f"🎯 <b>SMS RECEIVED IN YOUR NUMBER!</b>\n\n"
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
                                    bot1.send_message(CHAT_ID_1, text, parse_mode='HTML', reply_markup=markup)
                                    processed_sms_ids_1.add(msg_unique_id)
                                    save_processed_ids(processed_sms_ids_1, PROCESSED_DB_1)
                                    print(f"[Bot 1] Successfully forwarded OTP for {masked_number}")
                                    time.sleep(1)
                                except Exception as send_error:
                                    print(f"[Bot 1] Sending Error: {send_error}")
        except Exception as e:
            print(f"[Bot 1] Fetch Error: {e}")
        time.sleep(4)

# ==========================================
# ৪. নতুন বটের ফরোয়ার্ড লুপ (Dynamic Date System)
# ==========================================
def run_bot_2_loop():
    global processed_sms_ids_2
    print("🚀 Bot 2 (New) Forwarder Loop Started...")
    while True:
        try:
            # Dynamic today and tomorrow calculation (Auto UTC time adjustment)
            now = datetime.utcnow()
            today_str = now.strftime('%Y-%m-%dT00:00:00Z')
            tomorrow_str = (now + timedelta(days=1)).strftime('%Y-%m-%dT23:59:00Z')

            params = {
                "token": PANEL_TOKEN_2,
                "from": today_str,
                "to": tomorrow_str,
                "limit": 25
            }
            
            response = requests.get(API_URL_2, params=params, timeout=10)
            
            if response.status_code == 200:
                full_data = response.json()
                
                if isinstance(full_data, dict):
                    sms_list = full_data.get('data', [])
                elif isinstance(full_data, list):
                    sms_list = full_data
                else:
                    sms_list = []

                if isinstance(sms_list, list):
                    for sms in reversed(sms_list):
                        msg_id = str(sms.get('id', ''))
                        num = str(sms.get('number') or sms.get('phone') or sms.get('num') or 'Unknown').strip()
                        sms_time = str(sms.get('created_at') or sms.get('dt') or '')
                        
                        msg_unique_id = msg_id if msg_id else f"{num}_{sms_time}"
                        
                        if msg_unique_id not in processed_sms_ids_2:
                            msg_content = sms.get('message', 'No message')
                            otp = extract_otp(msg_content)
                            
                            service_name = sms.get('sender') or sms.get('service') or sms.get('cli') or 'Unknown'
                            service_name = str(service_name).strip()
                            
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
                                bot2.send_message(CHAT_ID_1, text, parse_mode='HTML', reply_markup=markup)
                                processed_sms_ids_2.add(msg_unique_id)
                                save_processed_ids(processed_sms_ids_2, PROCESSED_DB_2)
                                print(f"[Bot 2] Successfully forwarded OTP for {masked_number}")
                                time.sleep(1)
                            except Exception as send_error:
                                print(f"[Bot 2] Sending Error: {send_error}")
            else:
                print(f"[Bot 2] HTTP Error Status: {response.status_code}")
                
        except Exception as e:
            print(f"[Bot 2] Fetch Error: {e}")
            
        time.sleep(4)

# ==========================================
# ৫. দুটি বট একসাথে চালু করার মেইন প্রসেস
# ==========================================
if __name__ == "__main__":
    print("🔄 মাল্টি-বট সিস্টেম ব্যাকগ্রাউন্ড থ্রেড সহ চালু হচ্ছে...")
    
    # প্রথম বটের লুপ ব্যাকগ্রাউন্ড থ্রেডে চালু করা হলো
    t1 = threading.Thread(target=run_bot_1_loop, daemon=True)
    t1.start()
    
    # দ্বিতীয় বটের লুপ ব্যাকগ্রাউন্ড থ্রেডে চালু করা হলো
    t2 = threading.Thread(target=run_bot_2_loop, daemon=True)
    t2.start()
    
    # থ্রেড দুটি যাতে ব্যাকগ্রাউন্ডে চলতে থাকে
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 বটের কার্যক্রম বন্ধ করা হয়েছে।")
