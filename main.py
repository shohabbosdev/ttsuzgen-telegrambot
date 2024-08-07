import sox
import io
import requests
import telebot
from latin_cyrillic_symbols import to_cyrillic
from dotenv import dotenv_values

config = dotenv_values(".env")

bot = telebot.TeleBot(config['token'], parse_mode='HTML')

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
            return response.status_code, text, response.content
        else:
            return response.status_code, text, None
    
    except Exception as e:
        return None, None, None

def convert_to_ogg(audio_content):
    try:
        input_file = io.BytesIO(audio_content)
        temp_file = io.BytesIO()
        
        # Convert audio using sox
        tfm = sox.Transformer()
        tfm.set_output_format(format='ogg', rate=48000)
        tfm.build_file(input_file, temp_file)
        
        temp_file.seek(0)
        return temp_file
    except Exception as e:
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

bot.infinity_polling()
