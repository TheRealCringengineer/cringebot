import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from aiogram import F
from aiogram import Bot, Dispatcher, html, Router 
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup, InlineKeyboardButton, inline_keyboard_markup, reply_keyboard_markup, InlineQuery, InputTextMessageContent, InlineQueryResultArticle, InlineQueryResultDocument, ContentType, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    CallbackQuery
)
from pathlib import Path

from magic_filter.operations import call
from database import *
import html

load_dotenv()
TOKEN = os.getenv("TOKEN_PROJECTS")
ADMIN = os.getenv("ADMIN")

router = Router()
db = Database()
dp = Dispatcher()

RUSSIAN_LANG = "Русский"
ENGLISH_LANG = "English"

LANGUAGE = 'Language/Язык'

UNIQUE_USERS_RU = "Количество уникальных пользователей"
UNIQUE_USERS_ENG = "Unique users "

MAIN_LINKS_RU = '''Основные ссылки:
<a href="boosty.to/cringengineer">БУСТИ</a>\n
<a href="t.me/cringengineer_channel">ТЕЛЕГРАМ</a>\n
<a href="www.youtube.com/@PantheonDev">YOUTUBE</a>

<b>Проекты можно скачать из списка внизу</b>
'''
MAIN_LINKS_ENG = '''Links:
<a href="boosty.to/cringengineer">BOOSTY</a>\n
<a href="t.me/cringengineer_channel">TELEGRAM</a>\n
<a href="www.youtube.com/@PantheonDev">YOUTUBE</a>

<b>You can download projects from the list below</b>
'''

UNKNOWN_COMMAND_RU = "Неизвестная команда"
UNKNOWN_COMMAND_ENG = "Unknown command"

LANGUAGE_SET_RU = "Язык установлен на Русский"
LANGUAGE_SET_ENG = "Language set as English"

@dp.message(CommandStart())
async def command_start(message: Message):
    languages = [[
                    InlineKeyboardButton(text=RUSSIAN_LANG, callback_data=RUSSIAN_LANG),
                    InlineKeyboardButton(text=ENGLISH_LANG, callback_data=ENGLISH_LANG),
                ]]

    reply_markup=InlineKeyboardMarkup(
            inline_keyboard = languages,
            resize_keyboard=True,
        )

    await message.answer(LANGUAGE, reply_markup=reply_markup)

@dp.message(Command("language"))
async def command_lang(message: Message):
    languages = [[
                    InlineKeyboardButton(text=RUSSIAN_LANG, callback_data=RUSSIAN_LANG),
                    InlineKeyboardButton(text=ENGLISH_LANG, callback_data=ENGLISH_LANG),
                ]]

    reply_markup=InlineKeyboardMarkup(
            inline_keyboard = languages,
            resize_keyboard=True,
        )

    await message.answer(LANGUAGE, reply_markup=reply_markup)

@dp.message(Command("stats"))
async def command_start(message: Message):
    lang = db.get_language(message.from_user.id)
    if lang == RUSSIAN_LANG:
        await message.answer(f'{UNIQUE_USERS_RU} : {db.get_unique_count()}')
    else:
        await message.answer(f'{UNIQUE_USERS_ENG} : {db.get_unique_count()}')

@dp.message(Command("list"))
async def get_projects(message: Message):
    projects = db.get_projects()

    result = []

    for project in projects:
        result.append([InlineKeyboardButton(text=project["name"], callback_data=project["name"])])

    reply_markup=InlineKeyboardMarkup(
            inline_keyboard = result,
            resize_keyboard=True,
        )

    lang = db.get_language(message.from_user.id)
    if lang == RUSSIAN_LANG:
        await message.answer(MAIN_LINKS_RU, reply_markup=reply_markup)
    else:
        await message.answer(MAIN_LINKS_ENG, reply_markup=reply_markup)


async def select_russian(callback : CallbackQuery):
    message = callback.message
    if not message:
        await callback.answer("ERROR")
        return

    projects = db.get_projects()

    result = []

    for project in projects:
        result.append([InlineKeyboardButton(text=project["name"], callback_data=project["name"])])

    reply_markup=InlineKeyboardMarkup(
            inline_keyboard = result,
            resize_keyboard=True,
        )

    await callback.answer()
    if not db.add_new_user(callback.from_user.id, callback.from_user.full_name, RUSSIAN_LANG):
        db.update_language(callback.from_user.id, RUSSIAN_LANG)
    await message.answer(f"{LANGUAGE_SET_RU}\n\n{MAIN_LINKS_RU}", reply_markup = reply_markup)

async def select_english(callback : CallbackQuery):
    message = callback.message
    if not message:
        await callback.answer("ERROR")
        return

    projects = db.get_projects()

    result = []

    for project in projects:
        result.append([InlineKeyboardButton(text=project["name"], callback_data=project["name"])])

    reply_markup=InlineKeyboardMarkup(
            inline_keyboard = result,
            resize_keyboard=True,
        )

    await callback.answer()
    if not db.add_new_user(callback.from_user.id, callback.from_user.full_name, ENGLISH_LANG):
        db.update_language(callback.from_user.id, ENGLISH_LANG)
    await message.answer(f"{LANGUAGE_SET_ENG}\n\n{MAIN_LINKS_ENG}", reply_markup = reply_markup)

PROJECT_OPEN_TAG = "<project>"
PROJECT_CLOSE_TAG = "</project>"

def extract_project_name(caption):
    start = caption.find(PROJECT_OPEN_TAG)
    end = caption.find(PROJECT_CLOSE_TAG)

    if start == -1 or end == -1:
        return ""

    return caption[start+len(PROJECT_OPEN_TAG):end]

def extract_russian(caption):
    start = caption.find("🇷🇺")
    end = caption.find("🇺🇸")

    if start == -1 or end == -1:
        return ""

    return caption[start+len("🇷🇺"):end]

def extract_english(caption):
    start = caption.find("🇺🇸")

    if start == -1:
        return ""

    return caption[start+len("🇺🇸"):]

@dp.message(F.document)
async def upload_file(message: Message):
    if message.from_user is None or message.from_user.username != ADMIN:
        await message.answer("❌❌❌❌❌❌❌❌")
        return

    if message.document is None:
        await message.answer("❌ No document for some reason ❌")
        return

    project_name = extract_project_name(message.caption)
    if len(project_name) == 0:
        await message.answer(html.escape(f"No {PROJECT_OPEN_TAG} tag"))
    else:
        ru = extract_russian(message.caption)
        eng = extract_english(message.caption)
        logging.error(f"File : {message.document.file_id} Text RU : {ru} ENG : {eng}")

        full_path = f"projects/{message.document.file_name}"

        file_info = await bot.get_file(message.document.file_id)

        await bot.download_file(file_info.file_path, full_path)

        if db.create_project(project_name, ru, eng, full_path):
            await message.answer(f"File : {message.document.file_name} was uploaded for project {project_name}")
        else:
            db.update_project(project_name, ru, eng, full_path)
            await message.answer(f"File : {message.document.file_name} was uploaded for project {project_name}")

@dp.callback_query()
async def process_query(callback: CallbackQuery):
    message = callback.message
    if not message:
        await callback.answer("ERROR")
        return

    if callback.data == RUSSIAN_LANG:
        await select_russian(callback)
        return
    if callback.data == ENGLISH_LANG:
        await select_english(callback)
        return

    projects = db.get_projects()

    lang = db.get_language(callback.from_user.id)

    for project in projects:
        if project["name"] == callback.data:

            text = "text_eng"
            if lang == RUSSIAN_LANG:
                text = "text_ru"

            await callback.answer() # Disable glowing
            # await message.answer(project["text"])
            if db.is_cached(project["name"]):
                await message.answer_document(document=project["cache"], caption=project[text])
            else:
                res = await message.answer_document(document=FSInputFile(project["file"]), caption=project[text])
                db.set_cache_if_not_exist(project["name"], str(res.document.file_id))
            return

    await callback.answer() # Disable glowing
    if lang == RUSSIAN_LANG:
        await message.answer(UNKNOWN_COMMAND_RU)
    else:
        await message.answer(UNKNOWN_COMMAND_ENG)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Initialize Bot instance with default bot properties which will be passed to all API calls

    # And the run events dispatching
    await dp.start_polling(bot)

if __name__ == "__main__":

    projects = db.get_projects()

    for project in projects:
        db.clear_cache(project["name"])

    Path("projects").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
