from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor, exceptions
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN, admin, id_chat
from gtb_bot_1 import send_for_list
from gtb_bot_1 import players as all_players

import pandas as pd

import matplotlib.pyplot as plt

import time
import asyncio
import sqlite3

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


admin_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_msg =KeyboardButton(emojize('Сообщение:envelope:'))
btn_round = KeyboardButton(emojize(':round_pushpin:Раунд:round_pushpin:'))
btn_ques = KeyboardButton(emojize(':chequered_flag:Вопрос:chequered_flag:'))
btn_final = KeyboardButton(emojize(':airplane:Финал'))
btn_s_final = KeyboardButton(emojize(':rocket:Суперфинал'))
btn_res = KeyboardButton(emojize(':bellhop_bell:Результат'))

admin_kb.row(btn_msg, btn_round).add(btn_ques).add(btn_final, btn_s_final, btn_res)

inline_btn_time = InlineKeyboardButton('ВРЕМЯ', callback_data='seconds_left')
inline_kb_time = InlineKeyboardMarkup()
inline_kb_time.add(inline_btn_time)

mes_help = emojize('Напомним правила финала:cowboy_hat_face:\n\n:disguised_face:Финал проходит в режиме дуэлей. '
           'Вопросы в телеграм-бот получают только капитаны команд участников дуэли. Команды не участвующие в данной '
           'дуэли и зрители наблюдают за поединком в телеграм-канале игры.\n\n:disguised_face:Каждая дуэль состоит из нескольких (минимум 3 вопросов). ' \
            'На каждый вопрос также по 60 секунд. Призовой балл зарабатывает команда, первая ответившая на вопрос. '
           'В случае если первая команда отвечает не правильно, команда-оппонент должна отправить свой ответ в течении 30 секунд. '\
           'Если обе команды ошибаются, никто не зарабатывает призовой балл. Дуэль ведется, пока одна из команд не заработает 3 призовых балла.'
           '\n\n:disguised_face:Первые 3 дуэли проводятся между случайными парами команд из 6 финалистов. ' \
            'Победители этих дуэлей проходят в суперфинал, проигравшие команды выбывают из игры. Суперфинал это 3 дуэли между суперфиналистами. ' \
            'За победу в дуэли в суперфинале команда получает победное очко. Команда набравшая максимальное количество '\
           'победных очков признается победителем игры.\n\n:disguised_face:В случае равного количества победных очков у нескольких команд, '\
           'учитывается дуэльные баллы. Дуэльные баллы начисляются команде победившей ' \
            'в дуэли в количестве равном разнице счёта дуэли. В случае равного количества и победных очков и дуэльных баллов у нескольких команд, ' \
            'учитывается место занятое командой в первом этапе игры.')


class QuizStates(StatesGroup):
    RND = State()
    MSG = State()


conn = sqlite3.connect('gtb_db.db')
cur = conn.cursor()


@dp.message_handler(commands=["admin"])
async def admin_menu(msg: types.Message):
    if msg.from_user.id == admin:
        await bot.send_message(msg.from_user.id, "Здравствуйте, хозяин!", reply_markup=admin_kb)
    else:
        await bot.send_message(msg.from_user.id, "Поднесите телефон к левому глазу для сканирования сетчатки...")


@dp.message_handler(commands=['help'])
async def start(msg: types.Message):
    await bot.send_message(msg.from_user.id, mes_help + '\n\nВопросы пишите @idergunoff')


@dp.message_handler(lambda message: message.text == emojize('Сообщение:envelope:'))
async def message_for_all(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.MSG.set()
        mes = 'Отправьте сообщение для всех'
        await msg.reply(mes)


@dp.message_handler(state=QuizStates.MSG)
async def send_message_for_all(msg: types.Message, state:FSMContext):
    await state.finish()
    text = msg.text.split(';')
    await state.finish()
    if len(text) > 1:
        await bot.send_message(text[0], text[1])
    else:
        # список для рассылки
        cur.execute("SELECT telegram_id FROM game_team_2")
        res = cur.fetchall()
        players = []
        for i in res:
            players.append(i[0])
        await send_for_list(players, msg.text, 'text', False, False)


@dp.message_handler(lambda message: message.text == emojize(':airplane:Финал'))
async def message_for_all(msg: types.Message):
    cur.execute("SELECT team_name, telegram_id FROM game_team_2 ORDER BY id ASC ")
    res = cur.fetchall()
    mes = emojize(':woman_dancing:Внимание!!!:man_dancing:\nЧерез несколько минут мы начинаем финальные дуэли игры\n'
                  ':Santa_Claus:Новогодний:evergreen_tree:Онлайн:evergreen_tree:Квиз:Santa_Claus:!\n\n' + mes_help +
                  '\n\nВ финале играют:\n'
                  'Первая дуэль - команды :backhand_index_pointing_right: "{}" :crossed_swords: "{}" :backhand_index_pointing_left:\n'
                  'Вторая дуэль - команды :backhand_index_pointing_right: "{}" :crossed_swords: "{}" :backhand_index_pointing_left:\n'
                  'Третья дуэль - команды :backhand_index_pointing_right: "{}" :crossed_swords: "{}" :backhand_index_pointing_left:'.format(
                      res[0][0], res[1][0], res[2][0], res[3][0], res[4][0], res[5][0]))
    players = []
    for i in res:
        players.append(i[1])
    await send_for_list(players, mes, 'text', False, False)


@dp.message_handler(lambda message: message.text == emojize(':rocket:Суперфинал'))
async def message_for_all(msg: types.Message):
    cur.execute("SELECT team_name, telegram_id FROM game_team_3 ORDER BY id ASC ")
    res = cur.fetchall()
    mes = emojize(':saxophone:Внимание!!!:trumpet:\nЧерез несколько минут мы начинаем СУПЕРфинал игры\n'
                  ':Santa_Claus:Новогодний:evergreen_tree:Онлайн:evergreen_tree:Квиз:Santa_Claus:!' 
                  '\n\nВ СУПЕРфинале играют:\n'
                  'Первая дуэль - команды :backhand_index_pointing_right: "{}" :bow_and_arrow::water_pistol: "{}" :backhand_index_pointing_left:\n'
                  'Вторая дуэль - команды :backhand_index_pointing_right: "{}" :hammer_and_wrench: "{}" :backhand_index_pointing_left:\n'
                  'Третья дуэль - команды :backhand_index_pointing_right: "{}" :boomerang::plunger: "{}" :backhand_index_pointing_left:'.format(
                      res[0][0], res[1][0], res[1][0], res[2][0], res[2][0], res[0][0]))
    players = []
    for i in res:
        players.append(i[1])
    await send_for_list(players, mes, 'text', False, False)


@dp.message_handler(lambda message: message.text == emojize(':bellhop_bell:Результат'))
async def message_for_all(msg: types.Message):
    # получаем имена колонок
    get_column_names = cur.execute("SELECT * FROM game_team_3 LIMIT 1")
    col_name = [i[0] for i in get_column_names.description]

    cur.execute("""SELECT team_name, {}, {}, {}, win_point, wpoint_duel FROM game_team_3 
                    ORDER BY win_point DESC, wpoint_duel DESC, sum_point DESC, sum_wpoint DESC, sum_time ASC;""".format(
                    col_name[8], col_name[9], col_name[10]))
    res_tab = cur.fetchall()
    rows = [1, 2, 3]
    cols = ['Команда', col_name[8], col_name[9], col_name[10], 'Победные очки', 'Разница в счёте']
    colors = [[("Linen" if c in [0, 4] else "white") for c in range(len(cols))]
              for r in range(len(rows))]
    fig = plt.figure(figsize=(len(cols), len(rows) * 0.25), dpi=120)
    ax = plt.subplot()
    ax.set_axis_off()
    table_state = ax.table(cellText=res_tab,
                           rowLabels=rows,
                           colLabels=cols,
                           cellLoc='center',
                           loc='center',
                           rowLoc='center',
                           cellColours=colors,
                           rowColours=["Wheat"] * len(rows),
                           colColours=["Wheat"] * len(cols))
    table_state.auto_set_font_size(False)
    table_state.set_fontsize(7)
    plt.tight_layout(pad=0.2)
    plt.savefig('table_result.jpg')
    for i in all_players:
        await bot.send_photo(i, types.InputFile('table_result.jpg'))
    await bot.send_photo(id_chat, types.InputFile('table_result.jpg'))
    cur.execute("SELECT team_name FROM game_team_3 ORDER BY win_point DESC, wpoint_duel DESC, sum_point DESC, sum_wpoint DESC, sum_time ASC ")
    res = cur.fetchall()
    cur.execute("SELECT team_name, sum_time FROM game_team_1 ORDER BY sum_time ASC LIMIT 1")
    speedy = cur.fetchone()
    speedy_name, speedy_time = speedy[0], speedy[1]
    mes = emojize(':trophy:Внимание!!!:trophy:\n Итоги игры\n'
                  ':Santa_Claus:Новогодний:evergreen_tree:Онлайн:evergreen_tree:Квиз:Santa_Claus::\n\n'
                  ':1st_place_medal:Первое место - :party_popper:команда "{}":party_popper:\n'
                  ':2nd_place_medal:Второе место - :confetti_ball:команда "{}":confetti_ball:\n'
                  ':3rd_place_medal:Третье место - :balloon:команда "{}":balloon:\n\nP.S.\n'
                  ':high_voltage:В номинации "Самый быстрый" побежает:\n:racing_car:команда "{}":racing_car:\n'
                  'На 35 вопросов команда потратила всего лишь {} мин. {} сек., это в среднем по {} сек. на вопрос!'.format(
        res[0][0], res[1][0], res[2][0], speedy_name, str(int(speedy_time//60)), str(int(speedy_time%60)), str(int(speedy_time//35))))
    await send_for_list(all_players, mes, 'text', False, False)


@dp.message_handler(lambda message: message.text == emojize(':round_pushpin:Раунд:round_pushpin:'))
async def send_round_number(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.RND.set()
        mes = 'Отправьте номер раунда'
        await msg.reply(mes)


@dp.message_handler(state=QuizStates.RND)
async def set_round(msg: types.Message, state: FSMContext):
    if 0 < int(msg.text) < 7:
        await state.finish()
        # получаем id дуэлянтов
        cur.execute("SELECT teams_duel, nums_ques FROM table_rounds_2 WHERE num_round=?;", (msg.text, ))
        res = cur.fetchone()
        teams_duel, list_questions = res[0], res[1]
        list_team_id, list_team_name = [], []
        game_team = 'game_team_2' if int(msg.text) < 4 else 'game_team_3'
        try:
            cur.execute("ALTER TABLE {} ADD COLUMN {} INTEGER DEFAULT 0".format(game_team, 'point_duel_' + msg.text))
            conn.commit()
        except sqlite3.OperationalError:
            cur.execute("UPDATE {} SET {}=0".format(game_team, 'point_duel_' + msg.text))
            conn.commit()
            mes = 'Колонка этого раунда уже существует. Значения обнулены'
            await bot.send_message(admin, mes)
        for i in teams_duel.split(','):
            cur.execute("SELECT telegram_id, team_name FROM {} WHERE id=?;".format(game_team), (i, ))
            res = cur.fetchone()
            list_team_id.append(str(res[0]))
            list_team_name.append(res[1])
        cur.execute("UPDATE number_question_2 SET round=?, teams=?, team_names=?, list_questions=? WHERE id=1;", (
                    msg.text, ','.join(list_team_id), ','.join(list_team_name), list_questions))
        conn.commit()
        # список для рассылки
        cur.execute("SELECT telegram_id FROM {}".format(game_team))
        res = cur.fetchall()
        players = []
        for i in res:
            players.append(i[0])
        mes = emojize(':horizontal_traffic_light:Внимание!!!:horizontal_traffic_light:\n:crossed_swords:Бой между командами:\n\n"{}"'
        '\n:men_wrestling:\n"{}"'.format(list_team_name[0], list_team_name[1]))
        await send_for_list(players, mes, 'text', False, False)
    else:
        await msg.reply('Неверный номер раунда.')


@dp.message_handler(lambda message: message.text == emojize(':chequered_flag:Вопрос:chequered_flag:'))
async def send_question(msg: types.Message):
    if msg.from_user.id == admin:
        cur.execute("""SELECT round, teams, team_names, list_questions, count_question, time_ques, add_ques 
        FROM number_question_2 WHERE id=1""")
        res = cur.fetchone()
        n_round, teams, team_names, list_questions, count_question, time_ques, add_ques = res[0], res[1], res[2], \
                                                                                          res[3], res[4], res[5], res[6]
        if n_round:
            if time_ques == 0:
                if count_question < 5:
                    id_ques = int(list_questions.split(',')[count_question])
                else:
                    id_ques = add_ques
                    add_ques += 1
                game_team = 'game_team_2' if n_round < 4 else 'game_team_3'
                try:
                    # добавляем столбцы результатов по вопросу в таблицу игры 2 или 3
                    cur.execute("ALTER TABLE {} ADD COLUMN {} TEXT".format(game_team, 'answer_' + str(id_ques)))
                    conn.commit()
                except sqlite3.OperationalError:
                    mes = 'Колонка этого вопроса уже существует.'
                    await bot.send_message(admin, mes)
                cur.execute("SELECT * FROM quest_2 WHERE num=?;", (id_ques,))
                res = cur.fetchone()
                question, answer, comment, comment_photo, type_ques = res[1], res[2].lower().split('/ '), res[3], res[4], res[5]
                team_names = team_names.split(',')
                mes = emojize(':rotating_light:Внимание!!!:rotating_light:\n:question:Вопрос № {}:question:\n\nОтвечают '
                              'команды\n:point_right:"{}"\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t:vs:\n"{}":point_left:'.format(
                                count_question+1, team_names[0], team_names[1]))
                await send_for_list(teams.split(','), mes, 'text', False, False)
                await asyncio.sleep(7)
                await send_for_list(teams.split(','), question, type_ques, False, True)
                new_time = time.time()
                cur.execute("""UPDATE number_question_2 
                                SET number_question=?,count_question=count_question+1, time_ques=?, add_ques=?
                                WHERE id=1;""", (id_ques, new_time, add_ques))
                conn.commit()
                await asyncio.sleep(61)
                cur.execute("SELECT time_ques FROM number_question_2 WHERE id=1")

                if new_time == cur.fetchone()[0]:
                    if comment_photo:
                        await send_for_list(teams.split(','), comment_photo, 'photo', False, False)
                    mes = emojize(':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face:{}'.format(answer[0],
                                                                                                   comment))
                    await send_for_list(teams.split(','), mes, 'text', False, False)
                    score_list = []
                    for i in teams.split(','):
                        cur.execute("SELECT {} FROM {} WHERE telegram_id=?;".format('point_duel_' + str(n_round),
                                                                                    game_team), (i,))
                        score_list.append(str(cur.fetchone()[0]))
                    score = emojize('Ни одна команда не стала рисковать\n'
                                    ':8ball:Счёт прежний: {} - {}'.format(score_list[0], score_list[1]))
                    await send_for_list(teams.split(','), score, 'text', False, False)
                    cur.execute("UPDATE number_question_2 SET number_question=0, time_ques=0, team_add_time=0 WHERE id=1")
                    conn.commit()
            else:
                await msg.reply('Нельзя отправить вопрос. Еще не отправлен ответ на предыдущий вопрос!')
        else:
            await msg.reply('Не выбран номер раунда')


@dp.message_handler()
async def accept_answer(msg: types.Message):
    # получаем номер раунда, вопроса и т.д.
    cur.execute("SELECT round, teams, team_names, number_question, time_ques, team_add_time FROM number_question_2 WHERE id=1")
    res = cur.fetchone()
    num_round, id_teams, team_names, number_question, time_ques, team_add_time = res[0], res[1].split(','), \
                                                                            res[2].split(','), res[3], res[4], res[5]
    id_teams = [int(item) for item in id_teams]
    if msg.from_user.id in id_teams:
        index_team = id_teams.index(msg.from_user.id)
        game_team = 'game_team_2' if num_round < 4 else 'game_team_3'
        time_answer = time.time() - time_ques
        if not team_add_time:
            if number_question != 0:
                if time_answer < 61:
                    cur.execute("SELECT answer, comment, comment_photo FROM quest_2 WHERE num=?;", (number_question,))
                    res = cur.fetchone()
                    answer, comment, comment_photo = res[0].lower().split('/ '), res[1], res[2]
                    if msg.text.lower() in answer:
                        cur.execute("UPDATE number_question_2 SET number_question=0, time_ques=0 WHERE id=1")
                        conn.commit()
                        mes = emojize(':boom:На {} секунде команда "{}" отвечает "{}"\n\n:tada:Поздравляем!:tada:\nЭто '
                                      'правильный ответ. Команда зарабатывает 1 очко	:candy:'.format(
                                        str(round(time_answer, 2)), team_names[index_team], msg.text))
                        await send_for_list(id_teams, mes, 'text', False, False)
                        cur.execute("UPDATE {} SET {}=?, {}={}+1 WHERE telegram_id=?;".format(game_team,
                                      'answer_'+ str(number_question), 'point_duel_'+str(num_round),
                                      'point_duel_'+str(num_round)), (msg.text, msg.from_user.id))
                        conn.commit()
                        if comment_photo:
                            await send_for_list(id_teams, comment_photo, 'photo', False, False)
                        mes = emojize(':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face:{}'.format(answer[0],
                                                                                                       comment))
                        await send_for_list(id_teams, mes, 'text', False, False)
                        score_list = []
                        for i in id_teams:
                            cur.execute("SELECT {} FROM {} WHERE telegram_id=?;".format('point_duel_'+str(num_round),
                                        game_team), (i, ))
                            score_list.append(str(cur.fetchone()[0]))
                        score = emojize(':8ball:Счёт: {} - {}'.format(score_list[0], score_list[1]))
                        await send_for_list(id_teams, score, 'text', False, False)
                    else:
                        team_add_time_id, team_add_time_name = id_teams.copy(), team_names.copy()
                        team_add_time_id.remove(id_teams[index_team])
                        team_add_time_name.remove(team_names[index_team])
                        mes = emojize(':boom:На {} секунде команда "{}" отвечает "{}"\n\nУвы... :worried: Это '
                                      'неправильный ответ. У команды "{}" есть 30 секунд :hourglass_flowing_sand: '
                                      'для ответа на вопрос'.format(str(round(time_answer, 2)), team_names[index_team],
                                                                    msg.text, team_add_time_name[0]))
                        await send_for_list(id_teams, mes, 'text', False, True)
                        cur.execute("UPDATE {} SET {}=? WHERE telegram_id=?;".format(game_team,
                                                                                     'answer_' + str(number_question)),
                                    (msg.text, msg.from_user.id))
                        conn.commit()
                        new_time = time.time()
                        cur.execute("UPDATE number_question_2 SET team_add_time =?, time_ques=? WHERE id=1;", (
                            team_add_time_id[0], new_time))
                        conn.commit()
                        await asyncio.sleep(31)
                        cur.execute("SELECT time_ques FROM number_question_2 WHERE id=1")
                        if cur.fetchone()[0] == new_time:
                            if comment_photo:
                                await send_for_list(id_teams, comment_photo, 'photo', False, False)
                            mes = emojize(':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face:{}'.format(answer[0],
                                                                                                           comment))
                            await send_for_list(id_teams, mes, 'text', False, False)
                            score_list = []
                            for i in id_teams:
                                cur.execute(
                                    "SELECT {} FROM {} WHERE telegram_id=?;".format('point_duel_' + str(num_round),
                                                                                    game_team), (i,))
                                score_list.append(str(cur.fetchone()[0]))
                            score = emojize('Команда "{}" не успевает дать свою версию ответа :pleading_face:\n'
                                            ':8ball:Счёт прежний: {} - {}'.format(team_add_time_name[0], score_list[0], score_list[1]))
                            await send_for_list(id_teams, score, 'text', False, False)
                            cur.execute("UPDATE number_question_2 SET number_question=0, time_ques=0, team_add_time=0 WHERE id=1")
                            conn.commit()
                else:
                    await msg.reply(emojize(":man_shrugging: Время уже истекло! Ответы больше не принимаются. /help"))
            else:
                await msg.reply(
                    emojize(":man_shrugging: Ваш соперник ответил раньше или вопрос еще не задан! /help"))
        else:
            if msg.from_user.id == team_add_time:
                if time_answer < 31:
                    cur.execute("UPDATE number_question_2 SET number_question=0, time_ques=0, team_add_time=0 WHERE id=1")
                    conn.commit()
                    cur.execute("SELECT answer, comment, comment_photo FROM quest_2 WHERE num=?;", (number_question,))
                    res = cur.fetchone()
                    answer, comment, comment_photo = res[0].lower().split('/ '), res[1], res[2]
                    if msg.text.lower() in answer:
                        mes = emojize(':boom:Команда "{}" отвечает "{}"\n\n:tada:Поздравляем!:tada:\nЭто правильный '
                                      'ответ. Команда зарабатывает 1 очко	:candy:'.format(team_names[index_team],
                                                                                             msg.text))
                        await send_for_list(id_teams, mes, 'text', False, False)
                        cur.execute("UPDATE {} SET {}=?, {}={}+1 WHERE telegram_id=?;".format(game_team,
                                      'answer_' + str(number_question), 'point_duel_' + str(num_round),
                                      'point_duel_' + str(num_round)), (msg.text, msg.from_user.id))
                        conn.commit()
                    else:
                        mes = emojize('Команда "{}" отвечает "{}"\n\nУвы... :worried: И это тоже неправильный ответ. '
                                      'Ни одна команда не зарабатывает :o: ни одного очка.'.format(
                            team_names[index_team], msg.text))
                        await send_for_list(id_teams, mes, 'text', False, False)
                        cur.execute("UPDATE {} SET {}=? WHERE telegram_id=?;".format(game_team,
                                                                                     'answer_' + str(number_question)),
                                    (msg.text, msg.from_user.id))
                        conn.commit()
                    if comment_photo:
                        await send_for_list(id_teams, comment_photo, 'photo', False, False)
                    mes = emojize(':sunglasses: Правильный ответ - \n"{}"\n\n:nerd_face:{}'.format(answer[0],
                                                                                                   comment))
                    await send_for_list(id_teams, mes, 'text', False, False)
                    score_list = []
                    for i in id_teams:
                        cur.execute("SELECT {} FROM {} WHERE telegram_id=?;".format('point_duel_' + str(num_round),
                                                                                    game_team), (i,))
                        score_list.append(str(cur.fetchone()[0]))
                    score = emojize(':8ball:Счёт: {} - {}'.format(score_list[0], score_list[1]))
                    await send_for_list(id_teams, score, 'text', False, False)
                else:
                    await msg.reply(emojize(":man_shrugging:Время истекло! Ответы больше не принимаются. /help"))
        cur.execute("SELECT round FROM number_question_2 WHERE id=1;")
        if cur.fetchone()[0] != 0:
            score_list = []
            for i in id_teams:
                cur.execute("SELECT {} FROM {} WHERE telegram_id=?;".format('point_duel_' + str(num_round), game_team), (i,))
                score_list.append(cur.fetchone()[0])
            if score_list[0] >= 3 or score_list[1] >= 3:
                cur.execute("UPDATE number_question_2 SET round=0, count_question=0 WHERE id=1;")
                conn.commit()
                index_win = 0 if score_list[0] > score_list[1] else 1
                cur.execute("UPDATE {} SET win_point=win_point+1, wpoint_duel=wpoint_duel+? WHERE telegram_id=?;".format(
                    game_team), (abs(score_list[0] - score_list[1]), id_teams[index_win]))
                conn.commit()
                mes = emojize(':postal_horn:Внимание!!!\nВ бою между командами\n"{}"\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t:vs:'
                              '\n"{}"\nсо счётом - \n{} : {}\nпобеждает команда\n:tada:"{}":tada:'.format(
                    team_names[0], team_names[1], score_list[0], score_list[1], team_names[index_win]))
                await asyncio.sleep(3)
                await send_for_list(id_teams, mes, 'text', False, False)
                if num_round < 4:
                    mes = emojize('Команда "{}" проходит в суперфинал'.format(team_names[index_win]))
                    await send_for_list(id_teams, mes, 'text', False, False)
                    try:
                        cur.execute("""INSERT 
                        INTO game_team_3(telegram_id, team_name, sum_point, sum_wpoint, sum_time, win_point, wpoint_duel) 
                        SELECT telegram_id, team_name, sum_point, sum_wpoint, sum_time, win_point, wpoint_duel 
                        FROM game_team_2 WHERE telegram_id=?;""", (id_teams[index_win],))
                        conn.commit()
                        cur.execute("ALTER TABLE game_team_3 ADD COLUMN {} TEXT DEFAULT NULL".format(team_names[index_win]))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        mes = 'Пользователь уже в финале'
                        await bot.send_message(admin, mes)
                else:
                    score_0 = str(score_list[0]) + '-' + str(score_list[1])
                    score_1 = str(score_list[1]) + '-' + str(score_list[0])
                    cur.execute("UPDATE game_team_3 SET {}=? WHERE team_name=?;".format(team_names[1]), (score_0, team_names[0]))
                    conn.commit()
                    cur.execute("UPDATE game_team_3 SET {}=? WHERE team_name=?;".format(team_names[0]), (score_1, team_names[1]))
                    conn.commit()


@dp.callback_query_handler(text='seconds_left')
async def second_left(callback_query: types.CallbackQuery):
    # определяем время вопроса
    cur.execute("SELECT time_ques, team_add_time FROM number_question_2 WHERE id=1;")
    res = cur.fetchone()
    time_ques, add_time = res[0], res[1]
    all_time = 60 if not add_time else 30
    time_left = round(all_time - (time.time() - time_ques),2)
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