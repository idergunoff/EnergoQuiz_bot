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

teams = pd.read_excel('teams.xlsx', header=0, index_col=0)
print(teams)
questions = pd.read_excel('questions.xlsx', header=0, index_col=0)
print(questions)
admin = 325053382
quiz_chat_id = -1001262701497
nq = 0
tq = 0


class QuizStates(StatesGroup):
    REG = State()
    ANSWER = State()
    QUESTION = State()


keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
button1 = KeyboardButton('/question')
button2 = KeyboardButton('/answer')
button3 = KeyboardButton('/stat')
keyboard.row(button1, button2, button3)
inline_btn_time = InlineKeyboardButton('Сколько осталось секунд?', callback_data='seconds_left')
inline_kb = InlineKeyboardMarkup()
inline_kb.add(inline_btn_time)


@dp.message_handler(commands=['start'])
async def get_password(message: types.Message):
    mes = emojize(str(message.from_user.first_name) + ", приветствуем Вас на игре\n:zap:ЭнергоКвиз:zap: #ВместеЯрче!"
                                                      "\nДля регистрации отправьте пароль.")
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
                await bot.send_message(admin, 'В команду "' + str(teams['title'][n]) + '" зарегистрировался ' +
                                       str(msg.from_user.first_name) + '\nЗарегистрировано ' + str(count_user) + ' из '
                                       + str(len(teams['title'])) + ' команд')
                if (count_user % 10 == 0) or (count_user > len(teams['title']) - 10):
                    await bot.send_message(quiz_chat_id, 'Зарегистрировано ' + str(count_user) + ' из ' +
                                           str(len(teams['title'])) + ' команд')
                    for i in teams['user_id']:
                        if not pd.isna(i):
                            await bot.send_message(i, 'Зарегистрировано ' + str(count_user) + ' из ' +
                                                   str(len(teams['title'])) + ' команд')
            else:
                await bot.send_message(msg.from_user.id, "Участник от команды " + str(teams['title'][n]) +
                                       ' уже заявился.')
        else:
            await bot.send_message(msg.from_user.id, "Неверный пароль! " + msg.text +
                                   " Отравьте команду /start и введите корректный пароль")

    else:
        await bot.send_message(msg.from_user.id, str(msg.from_user.first_name) + ", Вы уже зарегистрировались.")
    await state.finish()


@dp.message_handler(commands=['help'])
async def get_password(message: types.Message):
    mes = 'На размышление над вопросом у вас есть 60 секунд\nОтвет можно отправлять сразу после получения ' \
          'вопроса\nДля контроля оставшегося времени нажмите кнопку "Сколько осталось секунд?" '
    await bot.send_message(message.from_user.id, mes)


@dp.message_handler(commands=['admin'])
async def admin_menu(message: types.Message):
    if message.from_user.id == admin:
        await message.reply("Меню администратора", reply_markup=keyboard)


@dp.message_handler(commands=['game'])
async def get_password(message: types.Message):
    if message.from_user.id == admin:
        mes = 'Все участники зарегистрированы\nЧерез 1 минуту мы начинаем игру\n\nНа размышление над вопросом у вас ' \
              'есть 60 секунд\nОтвет можно отправлять сразу после получения вопроса\nДля контроля оставшегося времени ' \
              'нажмите кнопку "Сколько осталось секунд?" '
        await bot.send_message(quiz_chat_id, mes)
        for i in teams['user_id']:
            if not pd.isna(i):
                await bot.send_message(i, mes)


@dp.message_handler(commands=['stat'])
async def save_stat(msg: types.Message):
    if msg.from_user.id == admin:
        teams_t = teams.transpose()
        for i in teams_t:
            point_sum = teams_t[i].iloc[7:47].sum()
            point_weight_sum = teams_t[i].iloc[167:207].sum()
            time_sum = teams_t[i].iloc[87:127].sum()
            check_time_sum = teams_t[i].iloc[127:167].sum()
            teams_t[i]['point_sum'] = point_sum
            teams_t[i]['point_weight_sum'] = point_weight_sum
            teams_t[i]['time_sum'] = time_sum
            teams_t[i]['check_time_sum'] = check_time_sum
        teams_result = teams_t.transpose()
        teams_result = teams_result.sort_values(by=['point_sum', 'point_weight_sum'], ascending=False).reset_index()
        teams_result.to_excel('teams_result.xlsx')
        await msg.reply("Статистика сохранена в файл teams_result.xlsx")


@dp.message_handler(commands=['question'])
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
            await bot.send_message(quiz_chat_id, 'Внимание!!! Вопрос № ' + str(nq))
            for i in teams['user_id']:
                if not pd.isna(i):
                    await bot.send_message(i, 'Внимание!!! Вопрос № ' + str(nq))
            time.sleep(7)
            await bot.send_photo(quiz_chat_id, text_question)
            for i in teams['user_id']:
                if not pd.isna(i):
                    await bot.send_photo(i, text_question, reply_markup=inline_kb)
            await bot.send_message(admin, 'Вопрос отправлен!', reply_markup=inline_kb)

        tq = time.time()
    else:
        await msg.reply('некорректный номер вопроса')
        nq = 0
    await state.finish()


@dp.message_handler(commands=['answer'])
async def send_answer(msg: types.Message):
    global nq, tq
    if msg.from_user.id == admin:
        if nq != 0:
            if time.time() - tq > 61:
                correct_answer = len(teams.loc[teams['point' + str(nq)] == 1])
                point_weight = len(teams['title']) - correct_answer
                for a in range(0, len(teams['title'])):
                    if teams['point' + str(nq)][a] == 1:
                        teams['point_weight' + str(nq)][a] = point_weight
                for b in range(0, len(teams['title'])):
                    if pd.isna(teams['time' + str(nq)][b]):
                        teams['time' + str(nq)][b] = 60
                mean_time = round(teams['time' + str(nq)].mean(), 2)
                mes = emojize(':nerd_face: Правильный ответ - \n"') + str(questions['answer'][nq]) + '"\n\n' + \
                      str(questions['comment'][nq]) + '\n\nПравильно ответили - ' + str(correct_answer) + ' из ' + \
                      str(len(teams['title'])) + ' команд\nСреднее время ответа - ' + str(mean_time) + ' cекунд'
                await bot.send_message(quiz_chat_id, mes)
                for i in teams['user_id']:
                    if not pd.isna(i):
                        await bot.send_message(i, mes)
                nq = 0
                teams.to_excel("teams.xlsx")
            else:
                await msg.reply('Отправлять правильный ответ еще рано, должно пройти 60 секунд')
        else:
            await msg.reply('Сначала нужно отправить вопрос')
    else:
        await msg.reply('Вы не туда попали. Каждый должен заниматься своим делом!')


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
                      '\n\n:racehorse: Самая быстрая команда - "' + str(team_speed) + '" - ответила на все вопросы за ' +
                      str(team_speed_result_min) + ' минут ' + str(team_speed_result_sec) + ' секунд'
                      '\n\n:snail: Самая медленная команда - "' + str(team_slow) + '" - ответила на все вопросы за ' +
                      str(team_slow_result_min) + ' минут ' + str(team_slow_result_sec) + ' секунд'
                      '\n\n:alarm_clock::snake: Самая хладнокровная команда - "' + str(team_snake) +
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
                if pd.isna(teams['point' + str(nq)][team]):
                    answer = str(questions['answer'][nq]).lower().split('/ ')
                    if msg.text.lower() in answer:
                        await msg.reply('Вы ответили - "' + msg.text + '" за ' + str(int(ta)) + ' секунд')
                        teams['answer' + str(nq)][team] = msg.text
                        teams['time' + str(nq)][team] = int(ta)
                        teams['point' + str(nq)][team] = 1
                    else:
                        await msg.reply('Вы ответили - "' + msg.text + '" за ' + str(int(ta)) + ' секунд')
                        teams['answer' + str(nq)][team] = msg.text
                        teams['time' + str(nq)][team] = int(ta)
                        teams['point' + str(nq)][team] = 0
                else:
                    await msg.reply('Вы уже ответили - "' + str(teams['answer' + str(nq)][team]) + '" /help')
            else:
                await msg.reply("Время истекло! Ответы больше не принимаются. /help")
        else:
            await msg.reply("Вопрос еще не задан! /help")


@dp.callback_query_handler(lambda callback_query: 'seconds_left')
async def second_left(callback_query: types.CallbackQuery):
    global tq, nq
    time_left = int(60 - (time.time() - tq))
    if time_left > 0:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, 'Осталось ' + str(time_left) + ' секунд')
        if callback_query.from_user.id != admin:
            team = teams.loc[teams['user_id'] == callback_query.from_user.id].index[0]
            if pd.isna(teams['check_time' + str(nq)][team]):
                teams['check_time' + str(nq)][team] = 1
            else:
                teams['check_time' + str(nq)][team] += 1
    else:
        await bot.send_message(callback_query.from_user.id, 'Самое время сосредоточиться перед следующим вопросом!')


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
