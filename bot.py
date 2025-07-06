import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils import executor
import requests
import os

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
API_URL = os.getenv("API_URL")

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

user_images = {}

@dp.message()
async def handle_photo(message: types.Message):
    if message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        content = await bot.download_file(file.file_path)

        if message.from_user.id not in user_images:
            user_images[message.from_user.id] = {"content": content}
            await message.reply("Контент получен. Теперь пришли изображение стиля.")
        else:
            user_images[message.from_user.id]["style"] = content
            await message.reply("Стиль получен. Генерирую...")

            files = {
                "content": ("content.jpg", user_images[message.from_user.id]["content"]),
                "style": ("style.jpg", content),
            }
            r = requests.post(API_URL, files=files)

            if r.status_code == 200:
                with open("result.jpg", "wb") as f:
                    f.write(r.content)
                await message.reply_photo(FSInputFile("result.jpg"))
            else:
                await message.reply("Ошибка во время инференса")

            del user_images[message.from_user.id]
