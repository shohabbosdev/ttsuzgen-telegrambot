import io
import requests
import telebot
from latin_cyrillic_symbols import to_cyrillic
from pydub import AudioSegment
from dotenv import dotenv_values
import os

config = dotenv_values(".env") 

bot = telebot.TeleBot(config['token'], parse_mode='HTML')

# Hugging Face API URL va token
API_URL = "https://api-inference.huggingface.co/models/shohabbosdev/text-to-audio"
headers = {"Authorization": f"Bearer {config['htoken']}"}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Assalomu alaykum bu botdan foydalanish uchun matnli xabar yozib qoldiring. Tez orada javobni oling")

def text_to_speech(text, language="uz"):
    try:
        text = text.replace('\n', ' ')
        text = text if any('\u0400' <= char <= '\u04FF' for char in text) else to_cyrillic(text)
        
        payload = {"inputs": text}
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            with open('debug_audio.bin', 'wb') as f:
                f.write(response.content)            
            return response.status_code, text, response.content
        else:
            return response.status_code, text, None
    
    except Exception as e:
        return None, None, None

def convert_to_ogg(audio_content):
    try:
        with open('temp_audio.flac', 'wb') as f:
            f.write(audio_content)
        audio = AudioSegment.from_file('temp_audio.flac', format='flac')
        audio = audio.set_frame_rate(48000)
        temp_file = io.BytesIO()
        audio.export(temp_file, format="ogg", parameters=["-acodec", "libopus", "-vbr", "on"])
        temp_file.seek(0)
        os.remove('temp_audio.flac')

        return temp_file
    except Exception as e:
        return None

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # Foydalanuvchi xabar yuborganda "Typing..." belgisi chiqariladi
    bot.send_chat_action(message.chat.id, 'record_voice')
    
    status_code, text, audio_content = text_to_speech(message.text)

    if status_code == 200 and audio_content:
        ogg_audio = convert_to_ogg(audio_content)
        if ogg_audio:
            bot.send_voice(message.chat.id, voice=ogg_audio, caption=f'<code>{text}</code>\n\n@shohabbosdev') 
        else:
            bot.reply_to(message, "Audio faylni konvert qilishda xatolik yuz berdi. Iltimos, dasturchi bilan bog'laning.")
    else:
        bot.reply_to(message, f"Text-to-speech xizmati xatosi: ❌ <code>{status_code}</code>")
    bot.send_chat_action(message.chat.id, 'record_voice')  

bot.infinity_polling()
