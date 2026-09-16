import telebot
import os
from flask import Flask
from threading import Thread
from telebot import types

# --- Flask Server (২৪ ঘণ্টা সচল রাখার জন্য) ---
app = Flask('')
@app.route('/')
def home():
    return "Formatter Bot is Alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- বট কনফিগারেশন ---
BOT_TOKEN = '8714062183:AAEDMDGfg_byuz4CiAZMw6RHVlQ-X8oQ3Pc'
bot = telebot.TeleBot(BOT_TOKEN)
user_config = {}

# --- মেইন মেনু বাটন ফাংশন ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('/start')
    btn2 = types.KeyboardButton('/format')
    btn3 = types.KeyboardButton('/support')
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (f"👋 **স্বাগতম! নাহিদ হাসানের নাম্বার ফরমেটার বটে।**\n\n"
                    f"শুরু থেকে কতটি ডিজিট কাটতে চান তা সংখ্যায় লিখে পাঠান।\n"
                    f"যেমন: `3` লিখে পাঠালে আমি প্রতিটি নাম্বারের শুরু থেকে ৩টি ডিজিট বাদ দিয়ে দেব।")
    bot.reply_to(message, welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(commands=['support'])
def support_info(message):
    support_text = (f"🆘 **সাপোর্ট প্রয়োজন?**\n\n"
                    f"যেকোনো সমস্যায় বা বটের নতুন আপডেটের জন্য সরাসরি যোগাযোগ করুন:\n"
                    f"👤 **Admin:** @nb269\n"
                    f"🤖 **Bot Creator:** Nahid Hasan")
    bot.reply_to(message, support_text, parse_mode='Markdown')

@bot.message_handler(commands=['format'])
def format_info(message):
    format_text = (f"🔢 **নাম্বার কাটার নিয়ম:**\n\n"
                   f"১. প্রথমে আমাকে একটি সংখ্যা পাঠান (যেমন: 3)।\n"
                   f"২. এরপর আপনার নাম্বারের লিস্ট থাকা `.txt` ফাইলটি পাঠান।\n"
                   f"৩. আমি সাথে সাথে আপনাকে ফ্রেশ ফাইল ফেরত দেব।")
    bot.reply_to(message, format_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text.isdigit())
def set_digit_count(message):
    user_config[message.chat.id] = int(message.text)
    bot.reply_to(message, f"✅ ঠিক আছে, এখন থেকে প্রতি লাইনে **{message.text}টি** ডিজিট কাটা হবে।\n📁 এখন আপনার `.txt` ফাইলটি পাঠান।", parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    if chat_id not in user_config:
        bot.reply_to(message, "⚠️ আগে কতটি ডিজিট কাটতে চান সেই সংখ্যাটি পাঠান (যেমন: 3)।")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_fn = f"in_{chat_id}.txt"
        output_fn = f"fixed_{chat_id}.txt"
        
        with open(input_fn, 'wb') as f:
            f.write(downloaded_file)
        
        digit_to_cut = user_config[chat_id]
        with open(input_fn, 'r', encoding='utf-8') as f:
            lines = [line.strip()[digit_to_cut:] for line in f if len(line.strip()) > digit_to_cut]

        if not lines:
            bot.reply_to(message, "❌ ফাইলে কোনো ভ্যালিড নাম্বার পাওয়া যায়নি!")
            return

        with open(output_fn, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        with open(output_fn, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"✅ সফলভাবে {digit_to_cut}টি ডিজিট কাটা হয়েছে!\n\n🤖 **Bot by Nahid Hasan**\n🆘 **Support:** @nb269")
        
        os.remove(input_fn)
        os.remove(output_fn)
        
    except Exception as e:
        bot.reply_to(message, "❌ দুঃখিত, ফাইলটি প্রসেস করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।")

if __name__ == "__main__":
    keep_alive()
    print("Full Updated Formatter Bot Started...")
    bot.polling(none_stop=True)
