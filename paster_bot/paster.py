import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

from aiogram import Bot, F, Dispatcher, html, Router 
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, reply_keyboard_markup, InlineQuery, InputTextMessageContent, InlineQueryResultArticle, InlineQueryResultDocument, InlineQueryResultsButton, User
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ChosenInlineResult
)
import numpy as np
import random
from datetime import datetime, timezone, timedelta
import time
from database import *
import html

db = Database()

load_dotenv()
TOKEN = os.getenv("TOKEN_PASTER")
rng = np.random.default_rng()
router = Router()
dp = Dispatcher()

from threading import Timer

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()
    
    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)
    
    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True
    
    def stop(self):
        self._timer.cancel()
        self.is_running = False

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

WAIT_TIME = 30 # Seconds
last_winner = ""
leaderboard = {}
next_finish_time = ""

def get_current_time():
    timezone_offset = +3.0  # Moscow (UTC+03:00)
    tzinfo = timezone(timedelta(hours=timezone_offset))
    return str((datetime.now(tzinfo)).strftime("%H:%M:%S"))


last_checked_day = 0

def reset_leaderboard():
    global leaderboard
    global last_winner
    global next_finish_time

    global last_checked_day
    
    if last_checked_day == time.localtime()[:3]:
        return

    # New day
    print("New day - new leaderboard")
    last_checked_day = time.localtime()[:3]

    # for i in range(len(leaderboard)):
        # print("{0}) {1} : {2}%\n".format(str(i+1), list(leaderboard.values())[i][1], list(leaderboard.values())[i][0]))
    if len(leaderboard.values()) > 0:
        last_winner = list(leaderboard.values())[0][1]
        if len(last_winner) > 0:
            db.add_winner(last_winner, float(list(leaderboard.values())[0][1])) 
    else:
        last_winner = ""
    leaderboard = {}


def set_result(user : User, score):

    global leaderboard

    db.add_leaderboard_user(html.escape(user.full_name))

    if user.id in leaderboard:
        if float(leaderboard[user.id][0]) > float(score):
            leaderboard[user.id] = score, html.escape(user.full_name), time.time()
        else:
            leaderboard[user.id] = leaderboard[user.id][0], leaderboard[user.id][1], time.time()
    else:
        leaderboard[user.id] = score, html.escape(user.full_name), time.time()

    # sort by score
    leaderboard = dict(sorted(leaderboard.items(), key=lambda item: float(item[1][0])))


def get_full_leaderboard():
    global leaderboard
    global last_winner
    global next_finish_time

    res = ""
    for i in range(len(leaderboard)):
        res += ("<b>{0}. {1}</b>: {2}%\n".format(str(i+1), list(leaderboard.values())[i][1], list(leaderboard.values())[i][0]))

    # print(len(leaderboard) if len(leaderboard) < 5 else 5)

    w = str(last_winner)
    if len(w) == 0:
        w = "ПУСТО"
    res += "\nПоследний победитель: " + w + "\n"
    res += "Раунд закончится в 00:00 по МСК"
    return res

def get_leaderboard():
    global leaderboard
    global last_winner
    global next_finish_time

    res = ""
    for i in range(len(leaderboard) if len(leaderboard) < 5 else 5):
        res += ("{0}. {1}: {2}%\n".format(str(i+1), html.unescape(list(leaderboard.values())[i][1]), list(leaderboard.values())[i][0]))

    # print(len(leaderboard) if len(leaderboard) < 5 else 5)

    # res += "\nПоследний победитель: " + str(last_winner) + "\n"
    # res += "Раунд закончится в 00:00 по МСК"
    return res

def generate_new_value():
    worst_value = 0
    for i in range(2):
        number = abs(rng.normal(1,0.5))
        while number > 1:
            number = number - 0.5
        if number > 0.2:
            worst_value = number
            break
        if number > worst_value:
            worst_value = number

    return "%.2f" % (worst_value * 100)

@dp.message(CommandStart())
async def start(message: Message):
    args = message.text.split(" ")

    rules =f"""
    Основные правила такие:\n\n
1) Раз в {WAIT_TIME} секунд вы можете сгенерировать новое случайное число через @am_i_a_paster_bot\n
2) Меньше - лучше\n
3) Раунд завершается в 00:00 по МСК каждый день\n
4) Таблицу лидеров можно посмотреть в боте через команду в @am_i_a_paster_bot или /leaderboard
    """

    if len(args) < 2:
        await message.answer(rules)
        return
    if args[1] != "leaderboard":
        await message.answer(rules)
        return

    await message.answer(text=get_full_leaderboard(),parse_mode="HTML")

@dp.message(Command("leaderboard"))
async def leaders(message: Message):
    await message.answer(text=get_full_leaderboard(),parse_mode="HTML")

@dp.message(Command("rules"))
async def rules(message: Message):
    rules =f"""
    Основные правила такие:\n
1) Раз в {WAIT_TIME} секунд вы можете сгенерировать новое случайное число через @am_i_a_paster_bot\n
2) Меньше - лучше\n
3) Раунд завершается в 00:00 по МСК каждый день\n
4) Таблицу лидеров можно посмотреть в боте через команду в @am_i_a_paster_bot или /leaderboard
    """
    await message.answer(rules)
    

@dp.callback_query(F.data == 'top5')
async def process_callback_button1(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id, text=get_leaderboard(), show_alert=True)
    # await bot.send_message(callback_query.from_user.id, 'Нажата первая кнопка!')


@dp.chosen_inline_result()
async def result(chosen: ChosenInlineResult):
    if chosen.from_user.id in leaderboard:
        last_time = leaderboard[chosen.from_user.id][2]
        seconds_pass = int(time.time() - last_time )
        if seconds_pass < WAIT_TIME:
            return

    text = ''
    # value = rng.randint(0,100)
    v = generate_new_value() 
    value = int(float(v))

    text += f"<b>Я пастер на {str(v)} %!</b>\n\n"

    text += "— <i>"

    if value == 0:
        text += "Нихуя себе! Получаю 300к в наносекунду?"
    elif value == 69:
        text += "Ха ха! Смешное секс число"
    elif value > 0 and value < 3:
        text += "500 РУБЛЕЙ!!!! СЮДАА"
    elif value >= 3 and value < 10:
        text += "Я был близок к 500 рублям но проиграл:("
    elif value >= 10 and value < 20:
        text += "Держу почти весь рынок платных читов на себе"
    elif value >= 20 and value < 30:
        text += "Имею дохуя репутации на StackOverflow"
    elif value >= 30 and value < 40:
        text += "\"Ну мам, это пацаны пастили, а я просто рядом стоял\""
    elif value >= 40 and value < 43:
        text += "\"Я сам код пишу, а пасту ебашу чисто для души!\""
    elif value >= 43 and value < 45:
        text += "Каждый баг — это возможность спастить что-то новое"
    elif value >= 45 and value < 50:
        text += "\"Да вообще я всё знаю, просто забыл\""
    elif value >= 50 and value < 54:
        text += "Робин гуд от мира кода"
    elif value >= 54 and value < 57:
        text += "Пастор вечного кода, чьи молитвы — это \"копировать\" и \"вставить\""
    elif value >= 57 and value < 60:
        text += "Дефолтный пользователь UnknownCheats"
    elif value >= 60 and value < 63:
        text += "Магистр копипасты, который верит в силу Ctrl+C и Ctrl+V"
    elif value >= 63 and value < 65:
        text += "Программист без собственной фантазии, но с гигантским буфером обмена"
    elif value >= 65 and value < 67:
        text += "\"Ребят, купите мой софт. Реально не ратка\""
    elif value >= 67 and value < 72:
        text += "Кодер, чье единственное правило: \"Нашел, спастил!\""
    elif value == 72:
        text += "TODO: Спастить смешное описание из ChatGPT"
    elif value > 72 and value < 75:
        text += "Великий исследователь чужих репозиториев"
    elif value >= 75 and value < 77:
        text += "Пират на просторах GitHub, всегда готов к похищению чужих решений"
    elif value >= 77 and value < 80:
        text += "Никогда не решаю проблему сам, всегда нахожу чужое решение и называю его своим"
    elif value >= 80 and value < 85:
        text += "Великий мастер склеивания чужих кусков кода"
    elif value >= 85 and value < 87:
        text += "Сделал и продал OpenGL пасту на STALCRAFT"
    elif value >= 87 and value < 90:
        text += "Программист-коллекционер: всё копирую, всё собираю"
    elif value >= 90 and value < 93:
        text += "Переименовал и продал OpenGL пасту на STALCRAFT"
    elif value >= 93 and value < 96:
        text += "Писатель эпопеи, где каждый абзац — это строка из Stack Overflow"
    elif value >= 96 and value < 100:
        text += "Дефолтный пользователь югейма"
    else:
        text += "Выпишите мне бан, это просто пиздец!"
    
    text += "</i> "

    emoji = ["💻","🖥","💾","💿","📺", "📟", "📀", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫️", "⚪️", "🟤"]
    text += " " + emoji[rng.integers(0,len(emoji))]

    set_result(chosen.from_user, v)

    pos = list(leaderboard.keys()).index(chosen.from_user.id) + 1
    text += f"\n\nМой лучший результат : {str(leaderboard[chosen.from_user.id][0] )}%"
    if pos == 1:
        text += "\nЯ на первом! СОСАТЬ + ЛЕЖАТЬ 🎉"
    else:
        text += f"\nМоё место: {str(pos)}"

    reply=InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Показать ТОП-5", callback_data="top5"),
            ]
        ],
        resize_keyboard=True,
    )


    await bot.edit_message_text(text=text, inline_message_id=chosen.inline_message_id, reply_markup=reply)


# inline_query_id = 1
@dp.inline_query()
async def inline_echo(inline_query: InlineQuery):

    text = ""
    if not inline_query.from_user:
        article = InlineQueryResultArticle(id=inline_query.id,
                                       title="Насколько я пастер?",
                                        input_message_content=InputTextMessageContent(message_text="Произошла ошибка"))
        await inline_query.answer(results=[article], cache_time=0, is_personal=True)
        return

    leaderboard_start = InlineQueryResultsButton(text="Таблица лидеров", start_parameter="leaderboard")

    if inline_query.from_user.id in leaderboard:
        last_time = leaderboard[inline_query.from_user.id][2]
        seconds_pass = int(time.time() - last_time )
        # print("С последнего запроса " + str(seconds_pass))
        if seconds_pass < WAIT_TIME:
            wait_msg = f"Подождите {str(WAIT_TIME-seconds_pass)} секунд"

            text += f"\nМой лучший результат : {str(leaderboard[inline_query.from_user.id][0] )}%"
            pos = list(leaderboard.keys()).index(inline_query.from_user.id) + 1
            if pos == 1:
                text += "\nЯ на первом! СОСАТЬ + ЛЕЖАТЬ 🎉"
            else:
                text += f"\nМоё место: {str(pos)}"

            wait = InlineQueryResultArticle(id=inline_query.id + "1",
                                       title=wait_msg,
                                        input_message_content=InputTextMessageContent(parse_mode="HTML", message_text=text))
            await inline_query.answer(results=[wait], cache_time=0, button=leaderboard_start, is_personal=True)
            return

    reply=InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Показать ТОП-5", callback_data="top5"),
            ]
        ],
        resize_keyboard=True,
    )


    article = InlineQueryResultArticle(id=inline_query.id,
                                       title="Насколько я пастер?",
                                       reply_markup=reply,
                                        input_message_content=InputTextMessageContent(parse_mode="HTML", message_text="Генерируем хуёвые проценты"))

    await inline_query.answer(results=[article], cache_time=0, button=leaderboard_start, is_personal=True)


if __name__ == "__main__":
    leaderboard[0] = 0, "" # Last winner before restart
    reset_leaderboard()
    rt = RepeatedTimer(60, reset_leaderboard)

    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt as e:
        rt.stop() 
        print("Finishing...")
