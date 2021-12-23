from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.emoji import emojize
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

import pandas as pd

import time
import asyncio
import sqlite3

from config import TOKEN


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


admin = 325053382

kb_reg = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_unreg = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_reg = KeyboardButton(emojize(':registered:Зарегистрировать команду:registered:'))
btn_upd = KeyboardButton(emojize(':registered:Изменить название команды:registered:'))
btn_rules = KeyboardButton(emojize(':scroll:Как играть?:scroll:'))
btn_test = KeyboardButton(emojize(':scroll:ТЕСТ:scroll:'))
btn_join = KeyboardButton(emojize(':scroll:УЧАВСТВОВАТЬ:scroll:'))
kb_unreg.add(btn_reg).add(btn_rules)
kb_reg.row(btn_upd, btn_test).add(btn_rules, btn_join)

inline_btn_time = InlineKeyboardButton('ВРЕМЯ', callback_data='seconds_left')
inline_kb_time = InlineKeyboardMarkup()
inline_kb_time.add(inline_btn_time)
inline_btn_ques = InlineKeyboardButton('ВОПРОС', callback_data='send_question')
inline_btn_back = InlineKeyboardButton('ВЫЙТИ', callback_data='exit_rules')
inline_kb_rules = InlineKeyboardMarkup()
inline_kb_rules.row(inline_btn_ques, inline_btn_back)
inline_btn_quick_answer = InlineKeyboardButton('НЕ ЖДАТЬ', callback_data='quick_answer')
inline_kb_quick_answer = InlineKeyboardMarkup()
inline_kb_quick_answer.add(inline_btn_quick_answer)
correct = ['Поздравляю! Ты ответил правильно и получил 1 очко! Давай попробуем ещё!',
           'Поздравляю! У тебя отлично получается!',
           'Правильно! Так держать, чемпион!',
           'Как ты догадался?! Загулил? Признайся!',
           'Точное попадание! Браво!',
           'Точный ответ! Ты полностью готов к игре!']
uncorrect = ['Эх! Ты ошибся. Пока что у тебя 0 очков. Попробуй ещё раз!',
             'Бывает. Все делают ошибки.',
             'Немного не хватило! Ничего страшного.',
             'Не правильно... Со всеми бывает. Можешь попытаться нагуглить правильный ответ, если конечно успеешь.',
             'Мимо... Как же так..?',
             'В этот раз не повезло, повезёт в игре!']


class QuizStates(StatesGroup):
    REG = State()
    UPD = State()
    ANSWER = State()
    QUESTION = State()


conn = sqlite3.connect('gtb_db.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS teams(
id INTEGER PRIMARY KEY, 
telegram_id INTEGER, 
team_name TEXT UNIQUE);
""")
conn.commit()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # проверка зарегестрирован ли пользователь
    cur.execute("SELECT * FROM teams WHERE telegram_id=?", (message.from_user.id, ))
    result = cur.fetchone()
    if result:
        mes = emojize(result[2] + ", добро пожаловать в\n:brain:GameToBrain:brain:!")
        await bot.send_message(message.from_user.id, mes, reply_markup=kb_reg)
    else:
        mes = emojize(str(message.from_user.first_name) + ", добро пожаловать в\n:brain:GameToBrain:brain:!")
        await bot.send_message(message.from_user.id, mes, reply_markup=kb_unreg)


@dp.callback_query_handler(text='exit_rules')
async def exit_rules(call: types.CallbackQuery):
    # количество тестовых вопросов
    cur.execute("SELECT COUNT(id) FROM ques_for_rules")
    count_ques = cur.fetchone()[0]
    # получаем time_id данной сессии
    cur.execute("SELECT MAX(time_id) FROM teams_for_rules WHERE telegram_id=?;", (call.from_user.id,))
    time_id = cur.fetchone()[0]
    # при выходе обновляем до последнего номера вопроса + 1
    cur.execute("UPDATE teams_for_rules SET number_question=? WHERE time_id=?;", (count_ques + 1, time_id))
    conn.commit()
    await start(call)


@dp.message_handler(lambda message: message.text == emojize(':scroll:ТЕСТ:scroll:'))
async def test(msg: types.Message):
    mes = 'тестовое сообщение'
    n = 0
    while n < 50:
        await bot.send_message(325053382, mes)
        n += 1
        cur.execute("INSERT INTO test_table VALUES(?, ?);", (n, time.time()))
        conn.commit()
    await bot.send_message(396309697, mes)


@dp.message_handler(lambda message: message.text == emojize(':registered:Зарегистрировать команду:registered:'))
async def registration(message: types.Message):
    await QuizStates.REG.set()
    mes = 'Отправьте название вашей команды'
    await bot.send_message(message.from_user.id, mes)


@dp.message_handler(state=QuizStates.REG)
async def add_team(message: types.Message, state: FSMContext):
    # проверка уникальность названия команды
    cur.execute("SELECT * FROM teams WHERE team_name=?", (message.text, ))
    if len(cur.fetchall()) > 0:
        mes = 'Команда с названием ' + message.text + ' уже существует. Отправьте другое название'
        await bot.send_message(message.from_user.id, mes)
    else:
        # добавляем команду
        team = (None, message.from_user.id, message.text, time.time())
        cur.execute("INSERT INTO teams VALUES(?, ?, ?, ?);", team)
        conn.commit()
        mes = 'Команда ' + message.text + ' успешно зарегистрирована!'
        await bot.send_message(message.from_user.id, mes, reply_markup=kb_reg)
        await state.finish()


@dp.message_handler(lambda message: message.text == emojize(':registered:Изменить название команды:registered:'))
async def update_name(message: types.Message):
    await QuizStates.UPD.set()
    mes = 'Отправьте новое название вашей команды'
    await bot.send_message(message.from_user.id, mes)


@dp.message_handler(state=QuizStates.UPD)
async def update_team(message: types.Message, state: FSMContext):
    cur.execute("SELECT * FROM teams WHERE team_name=?", (message.text, ))
    # проверка уникальность названия команды
    if len(cur.fetchall()) > 0:
        mes = 'Команда с названием ' + message.text + ' уже существует. Отправьте другое название'
        await bot.send_message(message.from_user.id, mes)
    else:
        # изменяем название команды
        team = (message.text, message.from_user.id)
        cur.execute("UPDATE teams SET team_name=? WHERE telegram_id=?;", team)
        conn.commit()
        mes = 'Поздравляю! Теперь ваша команда называется - ' + message.text
        await bot.send_message(message.from_user.id, mes)
        await state.finish()

        cur.execute("UPDATE game_team_1 SET team_name=? WHERE telegram_id=?;", team)
        conn.commit()


@dp.message_handler(lambda message: message.text == emojize(':scroll:УЧАВСТВОВАТЬ:scroll:'))
async def join_team(msg: types.Message):
    cur.execute("SELECT team_name FROM teams WHERE telegram_id=?;", (msg.from_user.id, ))
    team_name = cur.fetchone()[0]
    if team_name:
        cur.execute("""INSERT INTO game_team_1 (id, telegram_id, team_name, time_ques, ques)
        VALUES (?, ?, ?, ?, ?)""", (None, msg.from_user.id, team_name, None, None))
        conn.commit()
        mes = 'Команда {} добавлена в список участников'.format(team_name)
    else:
        mes = 'Сначала зарегистрируй команду.'
    await bot.send_message(msg.from_user.id, mes)
    await bot.send_message(admin, team_name + ' принимает участие в игре')


@dp.message_handler(lambda message: message.text == emojize(':scroll:Как играть?:scroll:'))
async def rules(message: types.Message):
    time_id = int(time.time()*100)
    # создаем нового участника для показа правил
    cur.execute("""INSERT INTO teams_for_rules
    (time_id, telegram_id, number_question)
    VALUES
    (?, ?, ?);
    """, (time_id, message.from_user.id, 1, ))
    conn.commit()
    mes = emojize(':brain:Игра в Мозги:brain: - интелектуально:exploding_head:развлекательная командная игра в '
                  'online-формате на базе социальной сети Телеграм.\nВ игре:victory_hand:2 тура.\nВ первом туре '
                  'участвуют:stadium:все команды.\nНа каждый вопрос отводится:stopwatch:60 секунд, чтобы отправить '
                  'ответ.\n:dizzy:Давай попробуем!')
    await bot.send_message(message.from_user.id, mes, reply_markup=inline_kb_rules)


@dp.message_handler()
async def answer_rules(message: types.Message):
    # получаем time_id последней записи пользователя
    cur.execute("SELECT MAX(time_id) FROM teams_for_rules WHERE telegram_id=?;", (message.from_user.id, ))
    time_id = cur.fetchone()[0]
    # получаем время и номер вопроса по time_id
    cur.execute("SELECT time_question, number_question FROM teams_for_rules WHERE time_id=?;", (time_id,))
    result = cur.fetchone()
    time_ques, number_ques = result[0], result[1]
    time_answer = time.time() - time_ques
    # проверяем есть ли уже ответ
    cur.execute("SELECT {} FROM teams_for_rules WHERE time_id=?;".format('answer_' + str(number_ques)), (time_id,))
    answer_team = cur.fetchone()[0]
    if answer_team:
        mes = 'Ты уже ответил - {}. Дождись правильного ответа.'.format(answer_team)
    else:
        # получаем правильный ответ
        cur.execute("SELECT answer FROM ques_for_rules WHERE id=?;", (number_ques, ))
        answer = str(cur.fetchone()[0]).lower().split('/ ')
        point = 1 if message.text.lower() in answer and time_answer < 60 else 0
        # отправляем ответ, время ответа и поинт
        cur.execute("UPDATE teams_for_rules SET {}=?, {}=?, {}=? WHERE time_id=?;".format('answer_' + str(number_ques),
                                                                                          'time_' + str(number_ques),
                                                                                          'point_' + str(number_ques)),
                    (message.text, time_answer, point, time_id))
        conn.commit()
        mes = 'Ты ответил - {} на {} секунде. {} Подожди немного, когда пройдет 60 секунд, ты узнаешь правильный ' \
              'ответ'.format(message.text, int(time_answer),
                             'К сожалению ты не уложился в 60 секунд. ' if time_answer > 60 else '')
    await bot.send_message(message.from_user.id, mes, reply_markup=inline_kb_quick_answer)


@dp.callback_query_handler(text='seconds_left')
async def second_left(callback_query: types.CallbackQuery):
    # определяем time_id
    cur.execute("SELECT MAX(time_id) FROM teams_for_rules WHERE telegram_id=?;", (callback_query.from_user.id,))
    time_id = cur.fetchone()[0]
    # определяем ремя старта вопроса
    cur.execute("SELECT time_question FROM teams_for_rules WHERE time_id=?;", (time_id,))
    time_ques = cur.fetchone()[0]
    time_left = int(60 - (time.time() - time_ques))
    if time_left > 0:
        await bot.answer_callback_query(callback_query.id, emojize(':hourglass_flowing_sand:Осталось ' + str(time_left)
                                                                    + ' секунд'), show_alert=True)
    else:
        await bot.answer_callback_query(callback_query.id, emojize(':thinking_face:Самое время сосредоточиться перед '
                                                                    'следующим вопросом!'), show_alert=True)


@dp.callback_query_handler(text='send_question')
async def send_question_rules(callback_query: types.CallbackQuery):
    # количество тестовых вопросов
    cur.execute("SELECT COUNT(id) FROM ques_for_rules")
    count_ques = cur.fetchone()[0]
    # получаем time_id данной сессии
    cur.execute("SELECT MAX(time_id) FROM teams_for_rules WHERE telegram_id=?;", (callback_query.from_user.id,))
    time_id = cur.fetchone()[0]
    # получаем номер текущего вопроса
    cur.execute("SELECT number_question FROM teams_for_rules WHERE time_id=?;", (time_id,))
    number_ques = cur.fetchone()[0]
    if number_ques <= count_ques:
        mes = emojize(':rotating_light:Внимание!!!:rotating_light:\n\nВопрос № {}'.format(number_ques))
        await bot.send_message(callback_query.from_user.id, mes)
        cur.execute("SELECT * FROM ques_for_rules WHERE id=?;", (number_ques,))
        res = cur.fetchone()
        question, answer, comment, comment_photo, text_rule, text_after_ques = res[1], res[2], res[3], res[4], res[5], res[6]
        await asyncio.sleep(2)
        await bot.send_photo(callback_query.from_user.id, question, reply_markup=inline_kb_time)
        cur.execute("UPDATE teams_for_rules SET time_question=? WHERE time_id=?;", (time.time(), time_id,))
        conn.commit()
        await bot.send_message(callback_query.from_user.id, emojize(text_after_ques))
        await asyncio.sleep(60)
        cur.execute("SELECT number_question FROM teams_for_rules WHERE time_id=?;", (time_id,))
        if number_ques == cur.fetchone()[0]:
            # вычисляем процент правильных ответов и среднее время ответа
            cur.execute("SELECT SUM({}), COUNT({}), SUM({})  FROM teams_for_rules".format('point_' + str(number_ques),
                                                                                          'point_' + str(number_ques),
                                                                                          'time_' + str(number_ques)))
            result = cur.fetchone()
            percent_correct_team = str(round(result[0] / result[1] * 100, 2))
            mean_time = str(round(result[2] / result[1], 2))
            mes = emojize((':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face: {}\n\n:+1:Правильно ответили - {} % '
                           'команд\n:stopwatch:Среднее время ответа - {} cекунд').format(answer, comment, percent_correct_team,
                                                                                         mean_time))
            if comment_photo:
                await bot.send_photo(callback_query.from_user.id, comment_photo)
            await bot.send_message(callback_query.from_user.id, mes)
            # получаем результат пользователя
            cur.execute("SELECT {} FROM teams_for_rules WHERE time_id=?;".format('point_' + str(number_ques)), (time_id,))
            point = cur.fetchone()[0]
            if point:
                mes = 'Точное попадание! Браво!'
            else:
                mes = 'Мимо... Как же так..?'
            await bot.send_message(callback_query.from_user.id, mes)
            await asyncio.sleep(4)
            cur.execute("UPDATE teams_for_rules SET number_question=? WHERE time_id=?;", (number_ques+1, time_id))
            conn.commit()
            await bot.send_message(callback_query.from_user.id, emojize(text_rule), reply_markup=inline_kb_rules)
    else:
        mes = 'Ты ответил на все тестовые вопросы. Теперь остается ждать начала игры'
        await bot.send_message(callback_query.from_user.id, mes)


@dp.callback_query_handler(text='quick_answer')
async def quick_answer(call: types.CallbackQuery):
    # получаем time_id данной сессии
    cur.execute("SELECT MAX(time_id) FROM teams_for_rules WHERE telegram_id=?;", (call.from_user.id,))
    time_id = cur.fetchone()[0]
    # получаем номер текущего вопроса
    cur.execute("SELECT number_question FROM teams_for_rules WHERE time_id=?;", (time_id,))
    number_ques = cur.fetchone()[0]
    cur.execute("SELECT * FROM ques_for_rules WHERE id=?;", (number_ques,))
    res = cur.fetchone()
    answer, comment, comment_photo, text_rule, text_after_ques = res[2], res[3], res[4], res[5], res[6]
    # вычисляем процент правильных ответов и среднее время ответа
    cur.execute("SELECT SUM({}), COUNT({}), SUM({})  FROM teams_for_rules".format('point_' + str(number_ques),
                                                                                  'point_' + str(number_ques),
                                                                                  'time_' + str(number_ques)))
    result = cur.fetchone()
    percent_correct_team = str(round(result[0] / result[1] * 100, 2))
    mean_time = str(round(result[2] / result[1], 2))
    mes = emojize((':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face: {}\n\n:+1:Правильно ответили - {} % '
                   'команд\n:stopwatch:Среднее время ответа - {} cекунд').format(answer, comment, percent_correct_team,
                                                                                 mean_time))
    if comment_photo:
        await bot.send_photo(call.from_user.id, comment_photo)
    await bot.send_message(call.from_user.id, mes)
    # получаем результат пользователя
    cur.execute("SELECT {} FROM teams_for_rules WHERE time_id=?;".format('point_' + str(number_ques)), (time_id,))
    point = cur.fetchone()[0]
    if point:
        mes = correct[number_ques-1]
    else:
        mes = uncorrect[number_ques-1]
    await bot.send_message(call.from_user.id, mes)
    await asyncio.sleep(4)
    cur.execute("UPDATE teams_for_rules SET number_question=? WHERE time_id=?;", (number_ques + 1, time_id))
    conn.commit()
    await bot.send_message(call.from_user.id, emojize(text_rule), reply_markup=inline_kb_rules)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)