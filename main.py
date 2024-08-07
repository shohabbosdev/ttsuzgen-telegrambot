import io
import requests
import telebot
from latin_cyrillic_symbols import to_cyrillic
from pydub import AudioSegment
from pydub.exceptions import PydubException
from dotenv import dotenv_values
import os

config = dotenv_values(".env")

bot = telebot.TeleBot(config['token'], parse_mode='HTML')

API_URL = "https://api-inference.huggingface.co/models/shohabbosdev/text-to-audio"
headers = {"Authorization": f"Bearer {config['htoken']}"}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Assalomu alaykum, bu botdan foydalanish uchun matnli xabar yozib qoldiring. Tez orada javobni oling.")

def text_to_speech(text, language="uz"):
    try:
        text = text.replace('\n', ' ')
        text = text if any('\u0400' <= char <= '\u04FF' for char in text) else to_cyrillic(text)
        
        payload = {"inputs": text}
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.status_code, text, response.content
        else:
            return response.status_code, text, None
    
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        return None, None, None

def convert_to_ogg(audio_content):
    try:
        # Save the audio content to a temporary file
        with io.BytesIO(audio_content) as input_file:
            input_file.seek(0)
            audio = AudioSegment.from_file(input_file, format='flac')
            audio = audio.set_frame_rate(48000)
            
            temp_file = io.BytesIO()
            audio.export(temp_file, format="ogg", parameters=["-acodec", "libopus", "-vbr", "on"])
            temp_file.seek(0)
            return temp_file

    except PydubException as e:
        print(f"Error in convert_to_ogg: {e}")
        return None

@bot.message_handler(func=lambda message: True)
def echo_all(message):
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
