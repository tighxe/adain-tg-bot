import logging
import os
import requests

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.token import validate_token
from aiogram import Router

from aiofiles.tempfile import NamedTemporaryFile

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
API_URL = os.getenv("API_URL")

# Проверим токен
validate_token(TG_BOT_TOKEN)

# Настраиваем логгирование
logging.basicConfig(level=logging.INFO)

# Создаём сессию, бота, диспетчер и роутер
session = AiohttpSession()
bot = Bot(token=TG_BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Словарь для хранения изображений пользователя
user_images = {}


@router.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    photo = message.photo[-1]

    # Получаем файл
    file = await bot.get_file(photo.file_id)
    content = await bot.download_file(file.file_path)

    # Если это первое изображение
    if user_id not in user_images:
        user_images[user_id] = {"content": content}
        await message.answer("Контент получен. Теперь пришли изображение стиля.")
        return

    # Если это второе изображение — стиль
    user_images[user_id]["style"] = content
    await message.answer("Стиль получен. Генерирую...")

    # Отправляем оба изображения на сервер
    files = {
        "content": ("content.jpg", user_images[user_id]["content"]),
        "style": ("style.jpg", user_images[user_id]["style"]),
    }

    try:
        response = requests.post(API_URL, files=files)

        if response.status_code == 200:
            # Временный файл для ответа
            async with NamedTemporaryFile("wb", suffix=".jpg", delete=False) as f:
                await f.write(response.content)
                file_path = f.name

            await message.answer_photo(FSInputFile(file_path))
            os.remove(file_path)
        else:
            await message.answer("Ошибка во время инференса.")
    except Exception as e:
        logging.exception("Ошибка при отправке запроса")
        await message.answer("Произошла ошибка при обращении к API.")
    finally:
        user_images.pop(user_id, None)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())