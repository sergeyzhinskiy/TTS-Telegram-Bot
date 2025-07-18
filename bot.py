import os
import uuid
import asyncio
import edge_tts
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile
from pydub import AudioSegment
from dotenv import load_dotenv

AudioSegment.ffmpeg = "c:/bot/factory/choc/tools/chocolateyInstall/lib/ffmpeg/tools/ffmpeg/bin/ffmpeg.exe"  # Укажите полный путь к ffmpeg
AudioSegment.ffprobe = "c:/bot/factory/choc/tools/chocolateyInstall/lib/ffmpeg/tools/ffmpeg/bin/ffprobe.exe"  # Укажите полный путь к ffprobe

# Загрузка переменных окружения
load_dotenv()
# Конфигурация бота
TOKEN = os.getenv("BOT_TOKEN")
#TOKEN = "YOUR_BOT_TOKEN"  # Замените на токен вашего бота
DEFAULT_VOICE = 'ru-RU-DmitryNeural'  # Голос по умолчанию

# Поддерживаемые голоса
SUPPORTED_VOICES = {
    'ru_m': 'ru-RU-DmitryNeural',      # Русский (мужской)
    'ru_f': 'ru-RU-SvetlanaNeural',    # Русский (женский)
    'uk_m': 'uk-UA-OstapNeural',       # Украинский (мужской)
    'uk_f': 'uk-UA-PolinaNeural'       # Украинский (женский)
}

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для хранения настроек голоса пользователей
user_voices = {}

async def text_to_speech(text: str, voice: str = DEFAULT_VOICE) -> str:
    """Преобразование текста в речь с сохранением в MP3"""
    output_file = f"temp_{uuid.uuid4().hex}.mp3"
    
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="+0%",
        volume="+0%"
    )
    
    await communicate.save(output_file)
    return output_file

def convert_to_opus(input_mp3: str) -> str:
    """Конвертация MP3 в формат OPUS для телеграма"""
    output_opus = input_mp3.replace('.mp3', '.opus')
    
    # Конвертация с помощью pydub
    audio = AudioSegment.from_mp3(input_mp3)
    audio.export(output_opus, format="opus")
    
    os.remove(input_mp3)  # Удаляем временный MP3
    return output_opus

@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    """Обработка команд /start и /help"""
    user_id = message.from_user.id
    voice = user_voices.get(user_id, DEFAULT_VOICE)
    
    # Определение текущего голоса
    current_voice = next((k for k, v in SUPPORTED_VOICES.items() if v == voice), 'ru_m')
    
    voice_names = {
        'ru_m': 'Русский мужской',
        'ru_f': 'Русский женский',
        'uk_m': 'Украинский мужской',
        'uk_f': 'Украинский женский'
    }
    
    help_text = (
        f"Привет! Я бот для преобразования текста в речь.\n\n"
        f"Просто отправь мне текст (до 1000 символов), и я верну его голосовым сообщением.\n\n"
        f"Текущий голос: {voice_names[current_voice]}\n\n"
        f"Доступные команды:\n"
        f"/ru_m - Русский мужской\n"
        f"/ru_f - Русский женский\n"
        f"/uk_m - Украинский мужской\n"
        f"/uk_f - Украинский женский"
    )
    await message.reply(help_text)

@dp.message(Command("ru_m", "ru_f", "uk_m", "uk_f"))
async def set_voice(message: Message):
    """Смена голоса"""
    user_id = message.from_user.id
    command = message.text[1:]  # Убираем слэш
    
    voice_names = {
        'ru_m': 'Русский мужской',
        'ru_f': 'Русский женский',
        'uk_m': 'Украинский мужской',
        'uk_f': 'Украинский женский'
    }
    
    if command in voice_names:
        user_voices[user_id] = SUPPORTED_VOICES[command]
        await message.reply(f"Голос изменен на: {voice_names[command]}")
    else:
        await message.reply("❌ Неизвестная команда")

@dp.message()
async def convert_text(message: Message):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    voice = user_voices.get(user_id, DEFAULT_VOICE)
    
    # Проверка длины текста
    if len(message.text) > 1000:
        await message.reply("❌ Ошибка: Максимальная длина текста - 1000 символов")
        return
    
    try:
        # Уведомление пользователя о начале обработки
        await bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
        
        # Преобразование текста в речь
        mp3_file = await text_to_speech(message.text, voice)
        opus_file = convert_to_opus(mp3_file)
        
        # Отправка голосового сообщения с использованием FSInputFile
        voice_input = FSInputFile(opus_file)
        await message.reply_voice(voice=voice_input)
        
        # Удаление временного файла
        os.remove(opus_file)
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при обработке: {str(e)}")
        print(f"Error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Проверка наличия ffmpeg
    if not AudioSegment.converter:
        print("ERROR: FFmpeg не найден! Установите ffmpeg и добавьте в PATH")
        exit(1)
    
    print("Бот запущен...")
    asyncio.run(main())