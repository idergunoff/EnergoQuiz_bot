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

import asyncio

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

teams = pd.read_excel('teams.xlsx', header=0, index_col=0)
print(teams)
questions = pd.read_excel('questions.xlsx', header=0, index_col=0)
print(questions)
admin = 325053382
quiz_chat_id = -459625629 # test chat
# quiz_chat_id = -1001291680097 #TN
# quiz_chat_id = -1001472198772 #TGRU
nq = 0
tq = 0


class QuizStates(StatesGroup):
    REG = State()
    ANSWER = State()
    QUESTION = State()


keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
button1 = KeyboardButton('Отправить вопрос')
button2 = KeyboardButton('/answer')
button3 = KeyboardButton('/stat')
keyboard.row(button1, button2, button3)
inline_btn_time = InlineKeyboardButton('Сколько осталось секунд?', callback_data='seconds_left')
inline_kb = InlineKeyboardMarkup()
inline_kb.add(inline_btn_time)


@dp.message_handler(commands=['start'])
async def get_password(message: types.Message):
    mes = emojize(':wink: ' + str(message.from_user.first_name) + ", приветствуем Вас на игре\n:zap:Новогодний "
                                                                  "онлайн-квиз:zap: \n\nДля регистрации отправьте "
                                                                  "пароль.")
    await bot.send_message(message.from_user.id, mes)
    await QuizStates.REG.set()


@dp.message_handler(state=QuizStates.REG)
async def check_password(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in teams['user_id'].tolist():
        if msg.text in teams['password'].tolist():
            n = teams.loc[teams['password'] == msg.text].index[0]
            if pd.isna(teams['user_id'][n]):
                teams['user_id'][n] = msg.from_user.id
                teams.to_excel('teams.xlsx')
                count_user = len(teams['title']) - len(teams.loc[pd.isna(teams['user_id'])])
                await bot.send_message(msg.from_user.id, 'Ваша команда - ' + str(teams['title'][n]))
                mes = emojize(':sparkles:Команда "' + str(teams['title'][n]) +
                              '" успешно прошла регистрацию!\n\n:man_pilot:Капитан - ' + str(msg.from_user.first_name) +
                              '\n\n:pray:Зарегистрировано ' + str(count_user) + ' из ' + str(len(teams['title'])) +
                              ' команд')
                await bot.send_message(admin, mes)
                await bot.send_message(quiz_chat_id, mes)
                for i in teams['user_id']:
                    if not pd.isna(i):
                        await bot.send_message(i, mes)
            else:
                await bot.send_message(msg.from_user.id, 'Капитан команды ' + str(teams['title'][n]) +
                                       ' уже заявился. Обратитесь к администратору - @idergunoff')
        else:
            await bot.send_message(msg.from_user.id, "Неверный пароль! " + msg.text +
                                   " Отравьте команду /start и введите корректный пароль. Обратите внимание, в пароле "
                                   "используются строчные латинские буквы, если у вас присутствует большая О, то это "
                                   "ноль. Если проблема повторяется, обратитесь к администратору - @idergunoff")
    else:
        await bot.send_message(msg.from_user.id, str(msg.from_user.first_name) + ", Вы уже зарегистрировались.")
    await state.finish()


@dp.message_handler(commands=['help'])
async def get_password(msg: types.Message):
    if msg.from_user.id in teams['user_id'].to_list():
        mes = emojize('Правила 1 тура! :nerd_face::point_up:\n\n:envelope:Сообщения с вопросами, правильными ответами и '
                      'статистикой приходят вам (капитанам) в этот чат-бот и дублируются в "общий чат игры" для остальных'
                      ':busts_in_silhouette:участников.\n\nКапитан должен отправлять ответ на вопрос в этот чат-бот. '
                      'Ответить на вопрос вы можете только один раз. Внимательно читайте вопрос:grey_exclamation: и '
                      'обращайте внимание на правильность:memo: написания. Например, если в вопросе указано '
                      'множественное число, то ответ должен быть во множественном числе.\n\n:stopwatch:На размышление над вопросом у вас '
                      'есть 60 секунд. По окончанию 60 секунд ответ просто не:no_entry_sign:отправится. Ответ можно '
                      'отправлять сразу после получения вопроса.\n\nДля контроля оставшегося времени нажмите кнопку '
                      '"Сколько осталось секунд?"\n\n:bar_chart:После 20 вопроса и по окончанию 1 тура в общий чат будет '
                      'выложена турнирная таблица. Вы сможете отправить апелляцию:mag:, если не согласны с незащитанным '
                      'ответом. Для этого отправьте номер вопроса личным сообщением организаторам:man_mechanic:игры.'
                      '\n\nПриятной игры!'
                      ':video_game:')
        await bot.send_message(msg.from_user.id, mes)


@dp.message_handler(commands=['admin'])
async def admin_menu(message: types.Message):
    if message.from_user.id == admin:
        await message.reply("Меню администратора", reply_markup=keyboard)


@dp.message_handler(commands=['game'])
async def get_password(message: types.Message):
    if message.from_user.id == admin:
        mes = emojize(':ok_hand:Все участники зарегистрированы!\nЧерез несколько минут мы начинаем игру:joystick:\n\n'
                      'Правила 1 тура! :nerd_face::point_up:\n\n:envelope:Сообщения с вопросами, правильными ответами '
                      'и статистикой приходят капитанам чат-бот и дублируются в "общий чат игры" для остальных'
                      ':busts_in_silhouette:участников.\n\nКапитан должен отправлять ответ на вопрос в этот чат-бот. '
                      'Ответить на вопрос вы можете только один раз. Внимательно читайте вопрос:grey_exclamation: и '
                      'обращайте внимание на правильность:memo: написания. Например, если в вопросе указано '
                      'множественное число, то ответ должен быть во множественном числе.\n\n:stopwatch:На размышление над вопросом у '
                      'вас есть 60 секунд. По окончанию 60 секунд ответ просто не:no_entry_sign:отправится. Ответ '
                      'можно отправлять сразу после получения вопроса.\n\nДля контроля оставшегося времени нажмите '
                      'кнопку "Сколько осталось секунд?"\n\n:bar_chart:После 20 вопроса и по окончанию 1 тура в общий '
                      'чат будет выложена турнирная таблица. Вы сможете отправить апелляцию:mag:, если не согласны с '
                      'незащитанным ответом. Для этого отправьте номер вопроса личным сообщением организаторам'
                      ':man_mechanic:игры.\n\nПриятной игры!:video_game:')
        await bot.send_message(quiz_chat_id, mes)
        for i in teams['user_id']:
            if not pd.isna(i):
                await bot.send_message(i, mes)


@dp.message_handler(commands=['stat'])
async def save_stat(msg: types.Message):
    if msg.from_user.id == admin:
        for i in range(1, len(questions['question'])+1):
            correct_answer = len(teams.loc[teams['1_point' + str(i)] == 1])
            point_weight = len(teams['title']) - correct_answer
            for a in range(1, len(teams['title']) + 1):
                if teams['1_point' + str(i)][a] == 1:
                    teams['5_point_weight' + str(i)][a] = point_weight
                else:
                    teams['5_point_weight' + str(i)][a] = 0
        teams_t = teams.transpose().sort_index()
        for i in teams_t:
            point_sum = teams_t[i].iloc[0:40].sum()
            point_weight_sum = teams_t[i].iloc[160:200].sum()
            time_sum = teams_t[i].iloc[80:120].sum()
            check_time_sum = teams_t[i].iloc[120:160].sum()
            teams['point_sum'][i] = point_sum
            teams['point_weight_sum'][i] = point_weight_sum
            teams['time_sum'][i] = time_sum
            teams['check_time_sum'][i] = check_time_sum
        teams_result = teams
        teams_result = teams_result.sort_values(by=['point_sum', 'point_weight_sum'], ascending=False).reset_index()
        teams_result_for_user = teams_result.drop(columns=['password', 'user_id', 'time_sum', 'check_time_sum'])
        for i in range(1, 41):
            teams_result_for_user = teams_result_for_user.drop(columns=['3_time'+str(i), '4_check_time'+str(i)])
        teams_result.to_excel('teams_result.xlsx')
        teams_result_for_user.to_excel('teams_result_for_user.xlsx')
        await msg.reply("Статистика сохранена в файл teams_result.xlsx")


@dp.message_handler(lambda message: message.text == "Отправить вопрос")
async def set_nq(msg: types.Message):
    global nq
    if msg.from_user.id == admin:
        if nq == 0:
            await QuizStates.QUESTION.set()
            await msg.reply('Отправь номер вопроса: ')
        else:
            await msg.reply('Вы еще не дали ответ на предыдущий вопрос')
    else:
        await msg.reply("Быть или не быть?")


@dp.message_handler(state=QuizStates.QUESTION)
async def ask_questions(msg: types.Message, state: FSMContext):
    global nq, tq
    nq = int(msg.text)
    if 0 < nq <= len(questions['question']):
        text_question = questions['question'][nq]
        if msg.from_user.id == admin:
            await bot.send_message(quiz_chat_id, emojize(':rotating_light:Внимание!!!:rotating_light:\n\nВопрос № ' + str(nq)))
            for i in teams['user_id']:
                if not pd.isna(i):
                    await bot.send_message(i, emojize(':rotating_light:Внимание!!!:rotating_light:\n\nВопрос № ' + str(nq)))
            time.sleep(7)
            await bot.send_photo(quiz_chat_id, text_question)
            for i in teams['user_id']:
                if not pd.isna(i):
                    await bot.send_photo(i, text_question, reply_markup=inline_kb)
            await bot.send_message(admin, 'Вопрос отправлен!', reply_markup=inline_kb)
            tq = time.time()
            await state.finish()
    else:
        await msg.reply('некорректный номер вопроса')
        nq = 0

    await asyncio.sleep(30)
    correct_answer = len(teams.loc[teams['1_point' + str(nq)] == 1])
    point_weight = len(teams['title']) - correct_answer
    for a in range(1, len(teams['title']) + 1):
        if teams['1_point' + str(nq)][a] == 1:
            teams['5_point_weight' + str(nq)][a] = point_weight
    for b in range(1, len(teams['title']) + 1):
        if pd.isna(teams['3_time' + str(nq)][b]):
            teams['3_time' + str(nq)][b] = 60
    mean_time = round(teams['3_time' + str(nq)].mean(), 2)
    mes = emojize(
        ':sunglasses: Правильный ответ - \n"' + str(questions['answer'][nq]) + '"\n\n:nerd_face:' + \
        str(questions['comment'][nq]) + '\n\n:+1:Правильно ответили - ' + str(correct_answer) + ' из ' + \
        str(len(teams['title'])) + ' команд\n:stopwatch:Среднее время ответа - ' + str(
            mean_time) + ' cекунд')
    await bot.send_message(quiz_chat_id, mes)
    for i in teams['user_id']:
        if not pd.isna(i):
            await bot.send_message(i, mes)
    if not pd.isna(questions['comment_photo'][nq]):
        await bot.send_photo(quiz_chat_id, questions['comment_photo'][nq])
        for i in teams['user_id']:
            if not pd.isna(i):
                await bot.send_photo(i, questions['comment_photo'][nq])
    await bot.send_message(admin, 'Ответ отправлен!')
    nq = 0
    teams.to_excel("teams.xlsx")




# @dp.message_handler(commands=['answer'])
# async def send_answer(msg: types.Message):
#     global nq, tq
#     if msg.from_user.id == admin:
#         if nq != 0:
#             if time.time() - tq > 61:
#                 correct_answer = len(teams.loc[teams['1_point' + str(nq)] == 1])
#                 point_weight = len(teams['title']) - correct_answer
#                 for a in range(1, len(teams['title'])+1):
#                     if teams['1_point' + str(nq)][a] == 1:
#                         teams['5_point_weight' + str(nq)][a] = point_weight
#                 for b in range(1, len(teams['title'])+1):
#                     if pd.isna(teams['3_time' + str(nq)][b]):
#                         teams['3_time' + str(nq)][b] = 60
#                 mean_time = round(teams['3_time' + str(nq)].mean(), 2)
#                 mes = emojize(
#                     ':sunglasses: Правильный ответ - \n"' + str(questions['answer'][nq]) + '"\n\n:nerd_face:' + \
#                     str(questions['comment'][nq]) + '\n\n:+1:Правильно ответили - ' + str(correct_answer) + ' из ' + \
#                     str(len(teams['title'])) + ' команд\n:stopwatch:Среднее время ответа - ' + str(
#                         mean_time) + ' cекунд')
#                 await bot.send_message(quiz_chat_id, mes)
#                 for i in teams['user_id']:
#                     if not pd.isna(i):
#                         await bot.send_message(i, mes)
#                 if not pd.isna(questions['comment_photo'][nq]):
#                     await bot.send_photo(quiz_chat_id, questions['comment_photo'][nq])
#                     for i in teams['user_id']:
#                         if not pd.isna(i):
#                             await bot.send_photo(i, questions['comment_photo'][nq])
#                 await bot.send_message(admin, 'Ответ отправлен!')
#                 nq = 0
#                 teams.to_excel("teams.xlsx")
#             else:
#                 await msg.reply('Отправлять правильный ответ еще рано, должно пройти 60 секунд')
#         else:
#             await msg.reply('Сначала нужно отправить вопрос')
#     else:
#         await msg.reply('Вы не туда попали. Каждый должен заниматься своим делом!')


@dp.message_handler(commands="result")
async def send_result(msg: types.Message):
    if msg.from_user.id == admin:
        teams_result = pd.read_excel('teams_result.xlsx', header=0)
        mes = emojize(':trophy: Результаты на данном этапе:\n\n:one: место - команда "' +
                      str(teams_result['title'][0]) + '" - ' + str(teams_result['point_sum'][0]) +
                      ' правильных ответов\n:two: место - команда "' +
                      str(teams_result['title'][1]) + '" - ' + str(teams_result['point_sum'][1]) +
                      ' правильных ответов\n:three: место - команда "' +
                      str(teams_result['title'][2]) + '" - ' + str(teams_result['point_sum'][2]) +
                      ' правильных ответов\n:four: место - команда "' +
                      str(teams_result['title'][3]) + '" - ' + str(teams_result['point_sum'][3]) +
                      ' правильных ответов\n:five: место - команда "' +
                      str(teams_result['title'][4]) + '" - ' + str(teams_result['point_sum'][4]) +
                      ' правильных ответов\n:six: место - команда "' +
                      str(teams_result['title'][5]) + '" - ' + str(teams_result['point_sum'][5]) +
                      ' правильных ответов')
        await bot.send_message(quiz_chat_id, mes)
        for i in teams['user_id']:
            if not pd.isna(i):
                await bot.send_message(i, mes)


@dp.message_handler(commands="fun")
async def send_result(msg: types.Message):
    if msg.from_user.id == admin:
        teams_result = pd.read_excel('teams_result.xlsx', header=0)
        teams_result1 = teams_result.sort_values(by=['time_sum']).reset_index()
        team_speed = teams_result1['title'][0]
        team_speed_result = teams_result1['time_sum'][0]
        team_speed_result_min = team_speed_result // 60
        team_speed_result_sec = team_speed_result % 60
        teams_result2 = teams_result.sort_values(by=['time_sum'], ascending=False).reset_index()
        team_slow = teams_result2['title'][0]
        team_slow_result = teams_result2['time_sum'][0]
        team_slow_result_min = team_slow_result // 60
        team_slow_result_sec = team_slow_result % 60
        teams_result3 = teams_result.sort_values(by=['check_time_sum']).reset_index()
        team_snake = teams_result3['title'][0]
        team_snake_result = teams_result3['check_time_sum'][0]
        teams_result4 = teams_result.sort_values(by=['check_time_sum'], ascending=False).reset_index()
        team_scream = teams_result4['title'][0]
        team_scream_result = teams_result4['check_time_sum'][0]
        mes = emojize(':gift: БОНУС!!!\n:tada: Лучшие из лучших :tada:'
                      '\n\n:racehorse: Самая быстрая команда - "' + str(
            team_speed) + '" - ответила на все вопросы за ' +
                      str(team_speed_result_min) + ' минут ' + str(team_speed_result_sec) + ' секунд'
                                                                                            '\n\n:snail: Самая медленная команда - "' + str(
            team_slow) + '" - ответила на все вопросы за ' +
                      str(team_slow_result_min) + ' минут ' + str(team_slow_result_sec) + ' секунд'
                                                                                          '\n\n:alarm_clock::snake: Самая хладнокровная команда - "' + str(
            team_snake) +
                      '" - проверила время ' + str(team_snake_result) +
                      ' раз за игру\n\n:alarm_clock::scream: Самая нервная команда - "' + str(team_scream) +
                      '" - проверила время ' + str(team_scream_result) + ' раз за игру')
        await bot.send_message(quiz_chat_id, mes)
        for i in teams['user_id']:
            if not pd.isna(i):
                await bot.send_message(i, mes)


@dp.message_handler()
async def answer_question(msg: types.Message):
    global nq, tq
    if msg.from_user.id in teams['user_id'].to_list():
        team = teams.loc[teams['user_id'] == msg.from_user.id].index[0]
        if nq != 0:
            ta = int(time.time() - tq)
            if ta < 61:
                if pd.isna(teams['1_point' + str(nq)][team]):
                    answer = str(questions['answer'][nq]).lower().split('/ ')
                    if msg.text.lower() in answer:
                        await msg.reply('Вы ответили - "' + msg.text + '" за ' + str(int(ta)) + ' секунд')
                        teams['2_answer' + str(nq)][team] = msg.text
                        teams['3_time' + str(nq)][team] = int(ta)
                        teams['1_point' + str(nq)][team] = 1
                    else:
                        await msg.reply('Вы ответили - "' + msg.text + '" за ' + str(int(ta)) + ' секунд')
                        teams['2_answer' + str(nq)][team] = msg.text
                        teams['3_time' + str(nq)][team] = int(ta)
                        teams['1_point' + str(nq)][team] = 0
                else:
                    await msg.reply(emojize(':man_shrugging:Вы уже ответили - "' + str(teams['2_answer' + str(nq)][team]) + '" /help'))
            else:
                await msg.reply(emojize(":hourglass:Время истекло! Ответы больше не принимаются. /help"))
        else:
            await msg.reply(emojize(":no_entry:Вопрос еще не задан! /help"))


@dp.callback_query_handler(lambda callback_query: 'seconds_left')
async def second_left(callback_query: types.CallbackQuery):
    global tq, nq
    time_left = int(60 - (time.time() - tq))
    if time_left > 0:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, emojize(':hourglass_flowing_sand:Осталось ' + str(time_left)
                                                                    + ' секунд'))
        if callback_query.from_user.id != admin:
            team = teams.loc[teams['user_id'] == callback_query.from_user.id].index[0]
            if pd.isna(teams['4_check_time' + str(nq)][team]):
                teams['4_check_time' + str(nq)][team] = 1
            else:
                teams['4_check_time' + str(nq)][team] += 1
    else:
        await bot.send_message(callback_query.from_user.id, emojize(':thinking_face:Самое время сосредоточиться перед '
                                                                    'следующим вопросом!'))


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
