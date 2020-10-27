from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.emoji import emojize
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time

from config import TOKEN
import pandas as pd

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

teams = pd.read_excel('teams2.xlsx', header=0, index_col=0)
print(teams)
questions = pd.read_excel('questions2.xlsx', header=0, index_col=0)
print(questions)
admin = 325053382
quiz_chat_id = -1001262701497
nr = False  # номер раунда
nq = 0  # номер вопроса
tq = 0  # время вопроса
i_player1 = False  # индекс игрока 1
i_player2 = False  # индекс игрока 2
dop_time = False  # Первая команда дала не правильный ответ
player_dop_time = list()


class QuizStates(StatesGroup):
    NUM_ROUND = State()
    CHOICE_PLAYER = State()
    ANSWER = State()
    QUESTION = State()


keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
button1 = KeyboardButton('/round')
button2 = KeyboardButton('/question')
button3 = KeyboardButton('/answer')
button4 = KeyboardButton('/stat')
keyboard.row(button1, button2, button3, button4)
inline_btn_time = InlineKeyboardButton('Сколько осталось секунд?', callback_data='seconds_left')
inline_kb = InlineKeyboardMarkup()
inline_kb.add(inline_btn_time)


@dp.message_handler(commands=['admin'])
async def admin_menu(message: types.Message):
    if message.from_user.id == admin:
        await message.reply("Меню администратора", reply_markup=keyboard)


@dp.message_handler(commands='round')
async def round_menu(msg: types.Message):
    if msg.from_user.id == admin:
        await QuizStates.NUM_ROUND.set()
        await msg.reply('Отправь номер раунда (1, 2 или 3):')


@dp.message_handler(state=QuizStates.NUM_ROUND)
async def num_round(msg: types.Message):
    global nr  # номер раунда
    try:
        if 1 <= int(msg.text) <= 3:
            nr = int(msg.text)
            await msg.reply(str(nr) + 'тур\nОтправьте через запятую номера команд участников данного сражения (от 0 '
                                      'до 5)')
            await QuizStates.CHOICE_PLAYER.set()
        else:
            await msg.reply('Некорректный номер раунда, отправьте 1, 2 или 3')
    except ValueError:
        await msg.reply('Некорректный номер раунда, отправьте 1, 2 или 3')


@dp.message_handler(state=QuizStates.CHOICE_PLAYER)
async def choice_player(msg: types.Message, state: FSMContext):
    global i_player1, i_player2
    players = msg.text.split(',')
    try:
        i_player1 = int(players[0])
        i_player2 = int(players[1])
        if (0 <= i_player1 <= 5) and (0 <= i_player1 <= 5) and (i_player1 != i_player2):
            mes = 'Внимание!!! \nБой ' + str(nr) + ' раунда второго тура игры ЭнергоКвиз\n между командами "' + \
                  str(teams['title'][i_player1]) + '" и "' + str(teams['title'][i_player2]) + '"'
            await bot.send_message(quiz_chat_id, mes)
            for i in teams['user_id']:
                await bot.send_message(i, mes)
            await state.finish()
        else:
            await msg.reply('Некорректно введены номера команд, повторите\nОтправьте через запятую номера команд '
                            'участников данного сражения (от 0 до 5), например - 0,5')
    except ValueError:
        await msg.reply('Некорректно введены номера команд, повторите\nОтправьте через запятую номера команд '
                        'участников данного сражения (от 0 до 5), например - 0,5')
    except IndexError:
        await msg.reply('Некорректно введены номера команд, повторите\nОтправьте через запятую номера команд '
                        'участников данного сражения (от 0 до 5), например - 0,5')


@dp.message_handler(commands=['game'])
async def get_password(message: types.Message):
    if message.from_user.id == admin:
        mes = 'Внимание!!!\nЧерез 1 минуту мы начинаем второй тур игры ЭнергоКвиз #ВместеЯрче\n\nВо второй тур' \
              'проходят 6 лидирующих в первом туре команд.\nВторой тур игры проходит в формате "Брейн-Ринг"' \
              '\nВ каждом бое одновременно принимают участие 2 команды.	После отправления вопроса, правильно ' \
              'ответившим считается тот, от кого первого пришел правильный ответ. За правильный ответ команде ' \
              'присуждается 1 очко; в случае неправильного ответа право ответа переходит к противоположной команде,' \
              'у которой остается 30 секунд а ответ. Каждый бой играется до трех очков.'
        await bot.send_message(quiz_chat_id, mes)
        for i in teams['user_id']:
            await bot.send_message(i, mes)


#
#
# @dp.message_handler(commands=['stat'])
# async def save_stat(msg: types.Message):
#     if msg.from_user.id == admin:
#         teams_t = teams.transpose()
#         for i in teams_t:
#             point_sum = teams_t[i].iloc[7:47].sum()
#             point_weight_sum = teams_t[i].iloc[167:207].sum()
#             time_sum = teams_t[i].iloc[87:127].sum()
#             check_time_sum = teams_t[i].iloc[127:167].sum()
#             teams_t[i]['point_sum'] = point_sum
#             teams_t[i]['point_weight_sum'] = point_weight_sum
#             teams_t[i]['time_sum'] = time_sum
#             teams_t[i]['check_time_sum'] = check_time_sum
#         teams_result = teams_t.transpose()
#         teams_result = teams_result.sort_values(by=['point_sum', 'point_weight_sum'], ascending=False).reset_index()
#         teams_result.to_excel('teams_result.xlsx')
#         await msg.reply("Статистика сохранена в файл teams_result.xlsx")
#
#
@dp.message_handler(commands=['question'])
async def set_nq(msg: types.Message):
    if msg.from_user.id == admin:
        if nr != False:
            if nq == 0:
                await QuizStates.QUESTION.set()
                await msg.reply('Отправь номер вопроса: ')
            else:
                await msg.reply('Вы еще не дали ответ на предыдущий вопрос')
        else:
            await msg.reply('Сначала выберите раунд и участников')
    else:
        await msg.reply("Быть или не быть?")


@dp.message_handler(state=QuizStates.QUESTION)
async def ask_questions(msg: types.Message, state: FSMContext):
    global nq, tq
    try:
        nq = int(msg.text)
        if 0 < nq <= len(questions['question']):
            text_question = questions['question'][nq]
            if msg.from_user.id == admin:
                mes = 'Внимание!!! Вопрос № ' + str(nq) + '\nОтвечают команды "' + teams['title'][i_player1] + '" и "' \
                      + teams['title'][i_player2] + '"'
                await bot.send_message(quiz_chat_id, mes)
                for i in teams['user_id']:
                    await bot.send_message(i, mes)
                time.sleep(7)
                await bot.send_photo(quiz_chat_id, text_question)
                for i in teams['user_id']:
                    await bot.send_photo(i, text_question, reply_markup=inline_kb)
                await bot.send_message(admin, 'Вопрос отправлен!', reply_markup=inline_kb)
                tq = time.time()
        else:
            await msg.reply('некорректный номер вопроса')
            nq = 0
    except ValueError:
        await msg.reply('некорректный номер вопроса')
        nq = 0
    await state.finish()


@dp.message_handler(commands=['answer'])
async def send_answer(msg: types.Message):
    global nq, tq, dop_time
    if msg.from_user.id == admin:
        if nq != 0:
            mes = emojize(':nerd_face: Правильный ответ - \n"') + str(questions['answer'][nq]) + '"\n\n' + \
                  str(questions['comment'][nq] + '\n\nНи одна команда не зарабатывает ни одного очка.')
            if dop_time == False:
                if time.time() - tq > 61:
                    await bot.send_message(quiz_chat_id, mes)
                    for i in teams['user_id']:
                        await bot.send_message(i, mes)
                    nq = 0
                else:
                    await msg.reply('Отправлять правильный ответ еще рано, должно пройти 60 секунд')
            else:
                if time.time() - tq > 31:
                    await bot.send_message(quiz_chat_id, mes)
                    for i in teams['user_id']:
                        await bot.send_message(i, mes)
                    nq = 0
                    dop_time = False
                else:
                    await msg.reply('Отправлять правильный ответ еще рано, должно пройти 30 секунд')
        else:
            await msg.reply('Сначала нужно отправить вопрос')
    else:
        await msg.reply('Вы не туда попали. Каждый должен заниматься своим делом!')


#
# @dp.message_handler(commands="result")
# async def send_result(msg: types.Message):
#     if msg.from_user.id == admin:
#         teams_result = pd.read_excel('teams_result.xlsx', header=0)
#         mes = emojize(':trophy: Результаты на данном этапе:\n\n:one: место - команда "' +
#                       str(teams_result['title'][0]) + '" - ' + str(teams_result['point_sum'][0]) +
#                       ' правильных ответов\n:two: место - команда "' +
#                       str(teams_result['title'][1]) + '" - ' + str(teams_result['point_sum'][1]) +
#                       ' правильных ответов\n:three: место - команда "' +
#                       str(teams_result['title'][2]) + '" - ' + str(teams_result['point_sum'][2]) +
#                       ' правильных ответов\n:four: место - команда "' +
#                       str(teams_result['title'][3]) + '" - ' + str(teams_result['point_sum'][3]) +
#                       ' правильных ответов\n:five: место - команда "' +
#                       str(teams_result['title'][4]) + '" - ' + str(teams_result['point_sum'][4]) +
#                       ' правильных ответов\n:six: место - команда "' +
#                       str(teams_result['title'][5]) + '" - ' + str(teams_result['point_sum'][5]) +
#                       ' правильных ответов')
#         await bot.send_message(quiz_chat_id, mes)
#         for i in teams['user_id']:
#             if not pd.isna(i):
#                 await bot.send_message(i, mes)
#
#

@dp.message_handler()
async def answer_question(msg: types.Message):
    global nr, nq, tq, dop_time, player_dop_time
    if nr:
        if dop_time == False:
            if msg.from_user.id in [teams['user_id'][i_player1], teams['user_id'][i_player2]]:
                i_team = teams.loc[teams['user_id'] == msg.from_user.id].index[0]
                if nq != 0:
                    ta = int(time.time() - tq)
                    if ta < 61:
                        answer = str(questions['answer'][nq]).lower().split('/ ')
                        if msg.text.lower() in answer:
                            mes = 'На ' + str(ta) + ' секунде команда "' + str(teams['title'][i_team]) + '" отвечает "' + \
                                  msg.text + '"\n\nПоздравляем! Это правильный ответ. Команда зарабатывает 1 очко.'
                            await bot.send_message(quiz_chat_id, mes)
                            for i in teams['user_id']:
                                await bot.send_message(i, mes)
                            teams['answer' + str(nq)][i_team] = msg.text
                            teams['point' + str(nr)][i_team] += 1
                            mes = emojize(':nerd_face: Правильный ответ - \n"') + str(questions['answer'][nq]) + '"\n\n' + \
                                  str(questions['comment'][nq])
                            await bot.send_message(quiz_chat_id, mes)
                            for i in teams['user_id']:
                                await bot.send_message(i, mes)
                            nq = 0
                            tq = 0
                            teams.to_excel("teams2.xlsx")
                        else:
                            player_dop_time = [i_player1, i_player2]
                            player_dop_time.remove(i_team)
                            mes = 'На ' + str(ta) + ' секунде команда "' + str(teams['title'][i_team]) + '" отвечает "' + \
                                  msg.text + '"\n\nУвы... Это неправильный ответ. У команды "' + \
                                  str(teams['title'][player_dop_time[0]]) + '" есть 30 секунд для ответа на вопрос'
                            await bot.send_message(quiz_chat_id, mes)
                            for i in teams['user_id']:
                                await bot.send_message(i, mes, reply_markup=inline_kb)
                            teams['answer' + str(nq)][i_team] = msg.text
                            dop_time = True
                            tq = time.time()
                    else:
                        await msg.reply("Время истекло! Ответы больше не принимаются. /help")
                else:
                    await msg.reply("Вопрос еще не задан! /help")
        else:
            if msg.from_user.id == teams['user_id'][player_dop_time[0]]:
                i_team = player_dop_time[0]
                ta = int(time.time() - tq)
                if ta < 31:
                    answer = str(questions['answer'][nq]).lower().split('/ ')
                    if msg.text.lower() in answer:
                        mes = 'Команда "' + str(teams['title'][i_team]) + '" отвечает "' + \
                              msg.text + '"\n\nПоздравляем! Это правильный ответ. Команда зарабатывает 1 очко.'
                        await bot.send_message(quiz_chat_id, mes)
                        for i in teams['user_id']:
                            await bot.send_message(i, mes)
                        teams['answer' + str(nq)][i_team] = msg.text
                        teams['point' + str(nr)][i_team] += 1
                    else:
                        mes = 'Команда "' + str(teams['title'][i_team]) + '" отвечает "' + msg.text + \
                              '"\n\nУвы... И это тоже неправильный ответ. Ни одна команда не зарабатывает ни одного очка.'
                        await bot.send_message(quiz_chat_id, mes)
                        for i in teams['user_id']:
                            await bot.send_message(i, mes)
                        teams['answer' + str(nq)][i_team] = msg.text
                    mes = emojize(':nerd_face: Правильный ответ - \n"') + str(questions['answer'][nq]) + '"\n\n' + \
                          str(questions['comment'][nq])
                    await bot.send_message(quiz_chat_id, mes)
                    for i in teams['user_id']:
                        await bot.send_message(i, mes)
                    nq = 0
                    tq = 0
                    dop_time = False
                    teams.to_excel("teams2.xlsx")
                else:
                    await msg.reply("Время истекло! Ответы больше не принимаются. /help")
        if teams['point' + str(nr)][i_player1] >= 3:
            teams['point_win' + str(nr)][i_player1] = 1
            teams['point_weight' + str(nr)][i_player1] = 3 - teams['point' + str(nr)][i_player2]
            mes = 'Внимание!!!\nВ бою ' + str(nr) + ' раунда второго тура между командами "' + str(teams['title'][i_player1]) + \
                  '" и "' + str(teams['title'][i_player2]) + '" со счётом - '+ str(teams['point' + str(nr)][i_player1]) + \
                  ' : ' + str(teams['point' + str(nr)][i_player2]) + ' побеждает команда "' + str(teams['title'][i_player1]) + '"'
            time.sleep(3)
            await bot.send_message(quiz_chat_id, mes)
            for i in teams['user_id']:
                await bot.send_message(i, mes)
            teams.to_excel("teams2.xlsx")
            nr = False
        elif teams['point' + str(nr)][i_player2] >= 3:
            teams['point_win' + str(nr)][i_player2] = 1
            teams['point_weight' + str(nr)][i_player2] = 3 - teams['point' + str(nr)][i_player1]
            mes = 'Внимание!!!\nВ бою ' + str(nr) + ' раунда второго тура между командами "' + str(teams['title'][i_player1]) + \
                  '" и "' + str(teams['title'][i_player2]) + '" со счётом - ' + str(teams['point' + str(nr)][i_player1]) + \
                  ' : ' + str(teams['point' + str(nr)][i_player2]) + ' побеждает команда "' + str(teams['title'][i_player2]) + '"'
            time.sleep(3)
            await bot.send_message(quiz_chat_id, mes)
            for i in teams['user_id']:
                await bot.send_message(i, mes)
            teams.to_excel("teams2.xlsx")
            nr = False


@dp.callback_query_handler(lambda callback_query: 'seconds_left')
async def second_left(callback_query: types.CallbackQuery):
    if dop_time == False:
        timing = 60
    else:
        timing = 30
    time_left = int(timing - (time.time() - tq))
    if time_left > 0:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, 'Осталось ' + str(time_left) + ' секунд')
    else:
        await bot.send_message(callback_query.from_user.id, 'Самое время сосредоточиться перед следующим вопросом!')


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
