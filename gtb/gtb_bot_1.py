from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor, exceptions
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN, admin, id_chat

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
btn_msg =KeyboardButton(emojize('Сообщение:envelope:'))
btn_round = KeyboardButton(emojize('Раунд:crab:'))
btn_round_description = KeyboardButton(emojize('Описание раунда:amphora:'))
btn_start = KeyboardButton(emojize('START_GAME:vulcan_salute:'))
btn_ques = KeyboardButton(emojize('Вопрос:camping:'))
btn_stat = KeyboardButton(emojize('Статистика:fountain:'))
btn_res = KeyboardButton(emojize('Результат:sun_with_face:'))
btn_fun_res = KeyboardButton(emojize('Фан:rainbow:'))
btn_rst = KeyboardButton(emojize(':cross_mark:СБРОС'))
admin_kb.row(btn_msg, btn_round, btn_round_description).add(btn_start, btn_ques, btn_stat).add(btn_res, btn_fun_res)

inline_btn_time = InlineKeyboardButton('ВРЕМЯ', callback_data='seconds_left')
inline_kb_time = InlineKeyboardMarkup()
inline_kb_time.add(inline_btn_time)

inline_btn_ready = InlineKeyboardButton(emojize(':superhero:ГОТОВ!'), callback_data='ready_user')
inline_kb_ready = InlineKeyboardMarkup()
inline_kb_ready.add(inline_btn_ready)

mes_help = emojize('Напомним правила первого этапа:OK_hand:\n\n:disguised_face:Первый этап состоит из 5 раундов, в каждом из которых по 7 вопросов. ' \
    'Для ответа на каждый вопрос отводится 60 секунд. В течении этого времени нужно отправить ответ.\n\n:disguised_face:Важно ' \
    'обращать внимание на правильность написания ответа, так как ответ принимается автоматически. ' \
    'Во избежание спорных ситуаций, если в вопросе специально не указано в каком виде должен быть написан ответ, ' \
    'то ответ должен быть написан в единственном числе, именительном падеже. Регистр букв не имеет значения\n\n:disguised_face:' \
    '7 вопросов каждого раунда задаются подряд. Через 60 секунд после каждого вопроса приходит правильный ответ. Если вы ответили правильно, ' \
    'вам начисляется 1 призовой бал. После семи вопросов подводится промежуточная статистика игры. ' \
    'По окончанию 5 раундов 6 команд с максимальным числом призовых баллов проходят в финал. ' \
    'В случае равного числа призовых баллов у нескольких команд, учитываются баллы за сложность вопроса.\n\n' \
    ':disguised_face:Балл за сложность вопроса рассчитывается для каждого вопроса как разница между общим числом команд ' \
    'и числом команд, правильно ответивших на этот вопрос.\n\n' \
    ':disguised_face:В случае равного числа и призовых баллов и баллов за сложность вопроса у нескольких команд, учитывается минимальное ' \
    'время затраченное командой для ответа на все вопросы.\n\n:raising_hands:Приятной игры!')


class QuizStates(StatesGroup):
    MSG = State()
    STAT = State()
    UPD_QUES = State()
    RND = State()
    RND_DESC = State()
    QUESTION = State()


conn = sqlite3.connect('gtb_db.db')
cur = conn.cursor()

# список для рассылки
cur.execute("SELECT telegram_id FROM game_team_1")
res = cur.fetchall()
players = []
for i in res:
    players.append(i[0])


@dp.message_handler(lambda message: message.text == emojize('Сообщение:envelope:'))
async def message_for_all(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.MSG.set()
        mes = 'Напишите через ";" id получателя и текст сообщения\nЕсли сообщение всем пользователям, напишите только текст сообщения.'
        await msg.reply(mes)


@dp.message_handler(state=QuizStates.MSG)
async def send_message_for_all(msg: types.Message, state:FSMContext):
    text = msg.text.split(';')
    await state.finish()
    if len(text) > 1:
        await bot.send_message(text[0], text[1])
    else:
        await send_for_list(players, msg.text, 'text', False, False)


@dp.message_handler(lambda message: message.text == emojize('START_GAME:vulcan_salute:'))
async def start_game(msg: types.Message):
    mes =emojize('Через пару минут мы начинаем наш :Santa_Claus:Новогодний:evergreen_tree:Онлайн:evergreen_tree:Квиз:Santa_Claus:!\n'
                 'Ты готов?')
    for i in players:
        try:
            await bot.send_message(i, mes, reply_markup=inline_kb_ready)
        except exceptions.BotBlocked:
            await bot.send_message(admin, 'блокировка бота пользователем ' + str(i))
            players.remove(i)


@dp.callback_query_handler(text='ready_user')
async def second_left(callback_query: types.CallbackQuery):
    markup = types.ReplyKeyboardRemove()
    await bot.send_message(callback_query.from_user.id, mes_help, reply_markup=markup)
    cur.execute("SELECT team_name FROM game_team_1 WHERE telegram_id=?", (callback_query.from_user.id, ))
    team_name = cur.fetchone()[0]
    await bot.send_message(id_chat, 'Команда "{}" готова к игре!'.format(team_name))


@dp.message_handler(commands=['help'])
async def start(msg: types.Message):
    await bot.send_message(msg.from_user.id, mes_help + '\n\nВопросы пишите @idergunoff')


@dp.message_handler(lambda message: message.text == emojize('Статистика:fountain:'))
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
    await bot.send_message(admin, 'Статистика отправлена')


@dp.message_handler(lambda message: message.text == emojize('Результат:sun_with_face:'))
async def calc_result(msg: types.Message):
    if msg.from_user.id == admin:
        cur.execute("""
        SELECT team_name, telegram_id, sum_point, sum_wpoint, sum_time
        FROM game_team_1
        ORDER BY sum_point DESC, sum_wpoint DESC, sum_time ASC LIMIT 6
        """)
        res = cur.fetchall()
        res_shuffle = res.copy()
        random.shuffle(res_shuffle)
        cur.executemany("""
        INSERT INTO game_team_2
        (team_name, telegram_id, sum_point, sum_wpoint, sum_time) 
        VALUES (?, ?, ?, ?, ?)
        """, res_shuffle)
        conn.commit()
        # todo: отправка xls c результатами в чат
        mes = emojize(':trophy:По результатам первого этапа в финал выходят:\n\n:one: место - команда "{}" - {}'\
        ' правильных ответов\n:two: место - команда "{}" - {} правильных ответов\n:three: место - команда "{}" - {}'\
        ' правильных ответов\n:four: место - команда "{}" - {} правильных ответов\n:five: место - команда "{}" - {}'\
        ' правильных ответов\n:six: место - команда "{}" - {} правильных ответов'.format(res[0][0], res[0][2],
        res[1][0], res[1][2], res[2][0], res[2][2], res[3][0], res[3][2], res[4][0], res[4][2], res[5][0], res[5][2]))
        await send_for_list(players, mes, 'text', False, False)
        table = pd.read_sql("SELECT * FROM game_team_1", conn)
        table = table.drop(['id', 'telegram_id', 'time_ques', 'ques'], axis=1)
        table.to_excel('1_этап.xlsx')
        print(table)
        for user_id in players:
            try:
                await bot.send_document(user_id, open('1_этап.xlsx', 'rb'))
            except exceptions.BotBlocked:
                await bot.send_message(admin, 'блокировка бота пользователем ' + str(user_id))
                players.remove(user_id)
        await bot.send_document(id_chat, open('1_этап.xlsx', 'rb'))
        await bot.send_message(admin, 'Результаты 1 этапа отправлены')


@dp.message_handler(lambda message: message.text == emojize(':cross_mark:СБРОС'))
async def reset_db(msg: types.Message):
    # ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ. полностью обнуляет таблицу игры первого этапа
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


@dp.message_handler(lambda message: message.text == emojize('Раунд:crab:'))
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
    await asyncio.sleep(20)
    for i in nums_ques.split(','):
        await auto_question(i)
        await asyncio.sleep(5)
    await calc_stat(nums_ques)
    await bot.send_message(admin, 'Раунд {} сыгран. Статистика отправлена'.format(msg.text))


@dp.message_handler(lambda message: message.text == emojize('Описание раунда:amphora:'))
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
    await bot.send_message(admin, 'Описание раунда {} отправлено'.format(msg.text))


@dp.message_handler(lambda message: message.text == emojize('Вопрос:camping:'))
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


async def send_for_list(list_players, message, type_mes, save_time, btn_time):
    list_players_copy = list_players.copy()
    if type_mes in ['audio', 'video']:
        message = message.split("; ")
    random.shuffle(list_players_copy)
    for user_id in list_players_copy:
        try:
            if btn_time:
                if type_mes == 'text':
                    await bot.send_message(user_id, message, reply_markup=inline_kb_time)
                elif type_mes == 'photo':
                    await bot.send_photo(user_id, message, reply_markup=inline_kb_time)
                elif type_mes == 'audio':
                    await bot.send_audio(user_id, message[0])
                    await bot.send_message(user_id, message[1], reply_markup=inline_kb_time)
                elif type_mes == 'video':
                    await bot.send_video(user_id, message[0])
                    await bot.send_message(user_id, message[1], reply_markup=inline_kb_time)
            else:
                if type_mes == 'text':
                    await bot.send_message(user_id, message)
                elif type_mes == 'photo':
                    await bot.send_photo(user_id, message)
                elif type_mes == 'audio':
                    await bot.send_audio(user_id, message[0])
                    await bot.send_message(user_id, message[1])
                elif type_mes == 'video':
                    await bot.send_video(user_id, message[0])
                    await bot.send_message(user_id, message[1])
        except exceptions.BotBlocked:
            await bot.send_message(admin, 'блокировка бота пользователем ' + str(user_id))
            players.remove(user_id)
        if save_time:
            cur.execute("UPDATE game_team_1 SET time_ques=?, ques=? WHERE telegram_id=?;", (time.time(), message,
                                                                                                 user_id))
            conn.commit()
    if type_mes == 'text':
        await bot.send_message(id_chat, message)
    elif type_mes == 'photo':
        await bot.send_photo(id_chat, message)
    elif type_mes == 'audio':
        await bot.send_audio(id_chat, message[0])
        await bot.send_message(id_chat, message[1])
    elif type_mes == 'video':
        await bot.send_video(id_chat, message[0])
        await bot.send_message(id_chat, message[1])


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
    await bot.send_message(admin, 'Вопрос {} отправлен'.format(num_q))
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
    await bot.send_message(admin, 'Ответ на вопрос {} отправлен'.format(num_q))


async def calc_stat(num_list):
    point_list = []
    point_list_to_table = []
    for i in num_list.split(','):
        point_list.append('point_' + i)
        point_list_to_table.append('вопрос ' + i)
    point_str = ', '.join(point_list)
    # получаем баллы по раунду и промежуточные результаты
    cur.execute("""SELECT team_name, {}, sum_point, sum_wpoint 
            FROM game_team_1 ORDER BY sum_point DESC, sum_wpoint DESC, sum_time ASC;""".format(point_str))
    res = cur.fetchall()
    rows = range(1, len(res) + 1)
    cols = ['Команда'] + point_list_to_table + ['Сумма баллов', 'Сложность']
    colors = [[("Linen" if c == 0 or c == len(cols) - 1 or c == len(cols) - 2 else "white") for c in range(len(cols))]
              for r in range(len(rows))]
    fig = plt.figure(figsize=(len(cols) * 0.8, len(rows) * 0.24), dpi=120)
    ax = plt.subplot()
    ax.set_axis_off()
    table_state = ax.table(cellText=res,
             rowLabels=rows,
             colLabels=cols,
             cellLoc='center',
             loc='center',
             rowLoc='center',
             cellColours=colors,
             rowColours=["Wheat"] * len(rows),
             colColours=["Wheat"] * len(cols),
             colWidths=[0.28, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.14, 0.13])
    table_state.auto_set_font_size(False)
    table_state.set_fontsize(7)
    plt.tight_layout(pad=0.2)
    plt.savefig('table_stat.jpg')
    for i in players:
        await bot.send_photo(i, types.InputFile('table_stat.jpg'))
    await bot.send_photo(id_chat, types.InputFile('table_stat.jpg'))


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
                cur.execute("SELECT {}, team_name FROM game_team_1 WHERE telegram_id=?;".format('answer_' + str(num)),
                            (msg.from_user.id,))
                res = cur.fetchone()
                user_answ, team_name = res[0], res[1]
                if user_answ:
                    await msg.reply(emojize(':man_shrugging:Вы уже ответили - "{}"'.format(user_answ)))
                else:
                    await msg.reply('Вы ответили "{}" за {} секунд'.format(msg.text, str(round(time_answ, 2))))
                    await bot.send_message(admin, '{} ответил "{}" за {} секунд'.format(msg.text, str(round(time_answ, 2)), team_name)) # todo потестить
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


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
