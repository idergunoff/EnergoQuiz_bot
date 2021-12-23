from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor, exceptions
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN, admin

import pandas as pd

import matplotlib.pyplot as plt

import time
import asyncio
import sqlite3
import random

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

admin_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_msg =KeyboardButton(emojize('Сообщение всем:envelope:'))
btn_round = KeyboardButton(emojize('Раунд'))
btn_round_description = KeyboardButton(emojize('Описание раунда'))
btn_ques = KeyboardButton(emojize('Вопрос'))
btn_stat = KeyboardButton(emojize('Статистика'))
btn_res = KeyboardButton(emojize('Результат'))
btn_fun_res = KeyboardButton(emojize('Фан-результат'))
btn_rst = KeyboardButton(emojize(':cross_mark:СБРОС'))
admin_kb.row(btn_msg, btn_round, btn_round_description).add(btn_ques, btn_stat).add(btn_res, btn_fun_res, btn_rst)

inline_btn_time = InlineKeyboardButton('ВРЕМЯ', callback_data='seconds_left')
inline_kb_time = InlineKeyboardMarkup()
inline_kb_time.add(inline_btn_time)


class QuizStates(StatesGroup):
    MSG = State()
    STAT = State()
    UPD_QUES = State()
    RND = State()
    RND_DESC = State()
    ANSWER = State()
    QUESTION = State()


conn = sqlite3.connect('gtb_tgru.db')
cur = conn.cursor()

# список для рассылки
cur.execute("SELECT telegram_id FROM game_team_1")
res = cur.fetchall()
players = []
for i in res:
    players.append(i[0])


@dp.message_handler(lambda message: message.text == emojize('Сообщение всем:envelope:'))
async def message_for_all(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.MSG.set()
        mes = 'Отправьте сообщение для всех'
        await msg.reply(mes)


@dp.message_handler(state=QuizStates.MSG)
async def send_message_for_all(msg: types.Message, state:FSMContext):
    await state.finish()
    await send_for_list(players, msg.text, 'text', False, False)


@dp.message_handler(lambda message: message.text == emojize('Статистика'))
async def stat(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.STAT.set()
        mes = 'Отправьте номер раунда'
        await msg.reply(mes)


@dp.message_handler(state=QuizStates.STAT)
async def send_stat(msg: types.Message, state:FSMContext):
    await state.finish()
    # список номеров вопросов
    cur.execute("SELECT nums_ques FROM table_rounds_1 WHERE num_round=?;", (msg.text))
    num_list = cur.fetchone()[0]
    await calc_stat(num_list)


@dp.message_handler(lambda message: message.text == emojize('Результат'))
async def calc_result(msg: types.Message):
    if msg.from_user.id == admin:
        cur.execute("""
        SELECT team_name, telegram_id, sum_point, sum_wpoint, sum_time
        FROM game_team_1
        ORDER BY sum_point DESC, sum_wpoint DESC, sum_time ASC LIMIT 6
        """)
        res = cur.fetchall()
        random.shuffle(res)
        cur.executemany("""
        INSERT INTO game_team_2
        (team_name, telegram_id, sum_point, sum_wpoint, sum_time) 
        VALUES (?, ?, ?, ?, ?)
        """, res)
        conn.commit()

        # mes = emojize(':trophy:По результатам первого этапа в полуфинал выходят:\n\n:one: место - команда "{}" - {}'\
        # ' правильных ответов\n:two: место - команда "{}" - {} правильных ответов\n:three: место - команда "{}" - {}'\
        # ' правильных ответов\n:four: место - команда "{}" - {} правильных ответов\n:five: место - команда "{}" - {}'\
        # ' правильных ответов\n:six: место - команда "{}" - {} правильных ответов'.format(res[0][0], res[0][2],
        # res[1][0], res[1][2], res[2][0], res[2][2], res[3][0], res[3][2], res[4][0], res[4][2], res[5][0], res[5][2]))
        # await send_for_list(players, mes, 'text', False, False)
        # table = pd.read_sql("SELECT * FROM game_team_1", conn)
        # print(table)


@dp.message_handler(lambda message: message.text == emojize(':cross_mark:СБРОС'))
async def reset_db(msg: types.Message):
    if msg.from_user.id == admin:
        cur.execute("""ALTER TABLE game_team_1 RENAME TO game_team_1_old;""")
        cur.execute("""CREATE TABLE game_team_1(
            id             INTEGER PRIMARY KEY,
            telegram_id    INTEGER UNIQUE,
            team_name      TEXT    UNIQUE,
            time_ques      INTEGER,
            ques           TEXT,
            sum_point      INTEGER,
            sum_wpoint     INTEGER,
            sum_time       REAL);""")
        cur.execute("""INSERT INTO game_team_1(id, telegram_id, team_name)
                    SELECT id, telegram_id, team_name FROM game_team_1_old; """)
        cur.execute("""DROP TABLE game_team_1_old;""")
        conn.commit()
        cur.execute("UPDATE number_question SET num=0, num_list=NULL WHERE id=1")
        conn.commit()
        await msg.reply('Результаты сброшены')


@dp.message_handler(commands=["admin"])
async def admin_menu(msg: types.Message):
    if msg.from_user.id == admin:
        await bot.send_message(msg.from_user.id, "Здравствуйте, хозяин!", reply_markup=admin_kb)
    else:
        await bot.send_message(msg.from_user.id, "Поднесите телефон к левому глазу для сканирования сетчатки...")


@dp.message_handler(lambda message: message.text == emojize('Раунд'))
async def round_start(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.RND.set()
        mes = 'Отправьте номер раунда'
        await msg.reply(mes)


@dp.message_handler(state=QuizStates.RND)
async def send_round_start(msg: types.Message, state: FSMContext):
    await state.finish()
    cur.execute("SELECT * FROM table_rounds_1 WHERE num_round=?;", (msg.text,))
    res = cur.fetchone()
    name, desc, nums_ques = res[1], res[2], res[3]
    mes = 'Раунд №{}. {}\n{}'.format(msg.text, name, desc)
    await send_for_list(players, mes, 'text', False, False)
    await asyncio.sleep(15)
    for i in nums_ques.split(','):
        await auto_question(i)
        await asyncio.sleep(5)
    await calc_stat(nums_ques)


@dp.message_handler(lambda message: message.text == emojize('Описание раунда'))
async def round_description(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.RND_DESC.set()
        mes = 'Отправьте номер раунда'
        await bot.send_message(msg.from_user.id, mes)


@dp.message_handler(state=QuizStates.RND_DESC)
async def send_round_description(msg: types.Message, state: FSMContext):
    cur.execute("SELECT name_round, desc_round FROM table_rounds_1 WHERE num_round=?;", (msg.text,))
    res = cur.fetchone()
    name, desc = res[0], res[1]
    mes = 'Раунд №{}. {}\n{}'.format(msg.text, name, desc)
    await send_for_list(players, mes, 'text', False, False)
    await state.finish()


@dp.message_handler(lambda message: message.text == emojize('Вопрос'))
async def number_question(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.QUESTION.set()
        mes = 'Отправьте номер вопроса'
        await bot.send_message(msg.from_user.id, mes)


@dp.message_handler(state=QuizStates.QUESTION)
async def send_question(msg: types.Message, state: FSMContext):
    await state.finish()
    await auto_question(msg.text)


@dp.message_handler(state=QuizStates.UPD_QUES)
async def update_question(msg: types.Message, state: FSMContext):
    if msg.text != '0':
        # обнуляем значения в столбцах
        cur.execute("UPDATE game_team_1 SET {}=NULL, {}=0, {}=0, {}=60".format('answer_' + msg.text,
                    'point_' + msg.text, 'wpoint_' + msg.text, 'time_' + msg.text))
        conn.commit()
        mes = 'Результаты по вопросу {} обнулены'.format(msg.text)
        await bot.send_message(admin, mes)
    await state.finish()


@dp.message_handler()
async def accept_answer(msg: types.Message):
    if msg.from_user.id in players:
        cur.execute("SELECT ques, time_ques FROM game_team_1 WHERE telegram_id=?;", (msg.from_user.id,))
        res = cur.fetchone()
        ques, time_ques = res[0], res[1]
        if ques != '0':
            cur.execute("SELECT num, answer FROM quest_1 WHERE question=?;", (ques,))
            res = cur.fetchone()
            num, answ = res[0], res[1]
            time_answ = time.time() - time_ques
            if time_answ < 61:
                cur.execute("SELECT {} FROM game_team_1 WHERE telegram_id=?;".format('answer_' + str(num)),
                            (msg.from_user.id,))
                user_answ = cur.fetchone()[0]
                if user_answ:
                    await msg.reply(emojize(':man_shrugging:Вы уже ответили - {}'.format(user_answ)))
                else:
                    await msg.reply('Вы ответили {} за {} секунд'.format(msg.text, str(round(time_answ, 2))))
                    answ_list = answ.lower().split('/ ')
                    point = 1 if msg.text.lower() in answ_list else 0
                    cur.execute("""UPDATE game_team_1 SET {}=?, {}=?, {}=? 
                    WHERE telegram_id=?;""".format('answer_' + str(num), 'time_' + str(num), 'point_' + str(num)),
                                (msg.text, time_answ, point, msg.from_user.id,))
                    conn.commit()
            else:
                await msg.reply(emojize(':hourglass:Время истекло! Ответы больше не принимаются!'))
        else:
            await msg.reply(emojize(':no_entry:Вопрос еще не задан. Или ты не уложился в 60 секунд'))


async def send_for_list(list_players, message, type_mes, save_time, btn_time):
    for user_id in list_players:
        try:
            if btn_time:
                if type_mes == 'text':
                    await bot.send_message(user_id, message, reply_markup=inline_kb_time)
                elif type_mes == 'photo':
                    await bot.send_photo(user_id, message, reply_markup=inline_kb_time)
                elif type_mes == 'audio':
                    await bot.send_audio(user_id, message, reply_markup=inline_kb_time)
                elif type_mes == 'video':
                    await bot.send_video(user_id, message, reply_markup=inline_kb_time)
            else:
                if type_mes == 'text':
                    await bot.send_message(user_id, message)
                elif type_mes == 'photo':
                    await bot.send_photo(user_id, message)
                elif type_mes == 'audio':
                    await bot.send_audio(user_id, message)
                elif type_mes == 'video':
                    await bot.send_video(user_id, message)
        except exceptions.BotBlocked:
            await bot.send_message(admin, 'блокировка бота пользователем ' + str(user_id))
        if save_time:
            cur.execute("UPDATE game_team_1 SET time_ques=?, ques=? WHERE telegram_id=?;", (time.time(), message,
                                                                                                 user_id))
            conn.commit()


async def auto_question(num_q):
    # получаем вопрос - ответ
    cur.execute("SELECT * FROM quest_1 WHERE num=?;", (num_q,))
    res = cur.fetchone()
    ques, answ, comm, comm_photo, type_ques = res[1], res[2], res[3], res[4], res[5]
    # обновляем номер вопроса и список отправленных вопросов
    cur.execute("SELECT num_list FROM number_question WHERE id=1;")
    num_list = cur.fetchone()[0]
    if num_list:
        if num_q not in num_list.split(','):
            num_list += ',' + num_q
    else:
        num_list = num_q
    cur.execute("UPDATE number_question SET num=?, num_list=? WHERE id=1;", (num_q, num_list,))
    conn.commit()
    try:
        # добавляем столбцы результатов по вопросу в таблицу игры 1 тура
        cur.execute("ALTER TABLE game_team_1 ADD COLUMN {} TEXT".format('answer_' + num_q))
        conn.commit()
        cur.execute("ALTER TABLE game_team_1 ADD COLUMN {} INTEGER DEFAULT 0".format('point_' + num_q))
        conn.commit()
        cur.execute("ALTER TABLE game_team_1 ADD COLUMN {} INTEGER DEFAULT 0".format('wpoint_' + num_q))
        conn.commit()
        cur.execute("ALTER TABLE game_team_1 ADD COLUMN {} REAL DEFAULT 60".format('time_' + num_q))
        conn.commit()
    except sqlite3.OperationalError:
        await QuizStates.UPD_QUES.set()
        mes = 'Колонки этого вопроса уже существуют. Сбросить значеня?\nЕсли да отправь номер вопроса еще раз, если ' \
              'нет отправь 0'
        await bot.send_message(admin, mes)
        await asyncio.sleep(10)
    mes = emojize(':rotating_light:Внимание!!!:rotating_light:\n\nВопрос № {}'.format(num_q))
    await send_for_list(players, mes, 'text', False, False)
    await asyncio.sleep(5)
    await send_for_list(players, ques, type_ques, True, True)
    await asyncio.sleep(62)
    # вычисляем процент правильных ответов и среднее время ответа
    cur.execute("SELECT SUM({}), SUM({}) FROM game_team_1".format('point_' + num_q, 'time_' + num_q))
    res = cur.fetchone()
    percent_correct_team = str(round(res[0] / len(players) * 100, 2))
    mean_time = str(round(res[1] / len(players), 2))
    wpoint = len(players) - res[0]
    cur.execute("UPDATE number_question SET num=0 WHERE id=1;")
    conn.commit()
    for i in players:
        # перебираем пользователей если ответ правильный записываем весовой поинт
        cur.execute("SELECT {} FROM game_team_1 WHERE telegram_id=?;".format('point_' + num_q), (i,))
        if cur.fetchone()[0] == 1:
            cur.execute("UPDATE game_team_1 SET {}=? WHERE telegram_id=?;".format('wpoint_' + num_q),
                        (wpoint, i,))
            conn.commit()
        # считаем и обновляем суммарные результаты
        sum_point, sum_wpoint, sum_time = 0, 0, 0
        for j in num_list.split(','):
            cur.execute("SELECT {}, {}, {} FROM game_team_1 WHERE telegram_id=?;".format('point_' + j, 'wpoint_' + j,
                                                                                         'time_' + j), (i,))
            res = cur.fetchone()
            sum_point += res[0]
            sum_wpoint += res[1]
            sum_time += res[2]
        cur.execute("""UPDATE game_team_1 SET ques='0', sum_point=?, sum_wpoint=?, sum_time=? 
            WHERE telegram_id=?;""", (sum_point, sum_wpoint, sum_time, i,))
        conn.commit()
    if comm_photo:
        await send_for_list(players, comm_photo, 'photo', False, False)
    mes = emojize((':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face: {}\n\n:+1:Правильно ответили - {} % '
                   'команд\n:stopwatch:Среднее время ответа - {} cекунд').format(answ, comm, percent_correct_team,
                                                                                 mean_time))
    await send_for_list(players, mes, 'text', False, False)


async def calc_stat(num_list):
    point_list = []
    for i in num_list.split(','):
        point_list.append('point_' + i)
    point_str = ', '.join(point_list)
    cur.execute("""SELECT team_name, {}, sum_point, sum_wpoint 
            FROM game_team_1 ORDER BY sum_point DESC, sum_wpoint DESC, sum_time ASC;""".format(point_str))
    res = cur.fetchall()
    rows = range(1, len(res) + 1)
    cols = ['name'] + point_list + ['sum_point', 'sum_wpoint']
    colors = [[("Linen" if c == 0 or c == len(cols) - 1 or c == len(cols) - 2 else "white") for c in range(len(cols))]
              for r in range(len(rows))]
    fig = plt.figure(figsize=(len(cols) * 0.8, len(rows) * 0.24), dpi=120)
    ax = plt.subplot()
    ax.set_axis_off()
    ax.table(cellText=res,
             rowLabels=rows,
             colLabels=cols,
             cellLoc='center',
             loc='center',
             rowLoc='center',
             cellColours=colors,
             rowColours=["Wheat"] * len(rows),
             colColours=["Wheat"] * len(cols))
    plt.tight_layout(pad=0.2)
    plt.savefig('table_stat.jpg')
    for i in players:
        await bot.send_photo(i, types.InputFile('table_stat.jpg'))


@dp.callback_query_handler(text='seconds_left')
async def second_left(callback_query: types.CallbackQuery):
    # определяем время вопроса
    cur.execute("SELECT time_ques FROM game_team_1 WHERE telegram_id=?;", (callback_query.from_user.id,))
    time_ques = cur.fetchone()[0]
    time_left = round(60 - (time.time() - time_ques),2)
    if time_left > 0:
        await bot.answer_callback_query(callback_query.id, emojize(':hourglass_flowing_sand:Осталось ' + str(time_left)
                                                                    + ' секунд'), show_alert=True)
    else:
        await bot.answer_callback_query(callback_query.id, emojize(':thinking_face:Самое время сосредоточиться перед '
                                                                    'следующим вопросом!'), show_alert=True)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
