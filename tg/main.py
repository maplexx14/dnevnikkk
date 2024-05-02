# Импорты
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from utils import Register_states, GPT_states
from config.config import TOKEN
import dnevnikk
from pathlib import Path
from loguru import logger
from dnevnikk import Dnevnik2
import time
from collections import defaultdict
from tg.src.gpt import send_question
from tg.src.showAverage import showAvg, showAvgRating
import json
import datetime as dt
from database.database import reg_db, check_user, get_rating, init_db, add_rating

bot = Bot(token= TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
date = datetime.datetime.now().date()
logger.add(f"../logs/{str(date)}.log")

# Клавиатура с кнопкой "Назад"
def back_markup_keyboard():
    back_markup = types.InlineKeyboardMarkup()
    back_but = types.InlineKeyboardButton(text='Назад', callback_data='back')
    back_markup.add(back_but)
    return back_markup
# Клавиатура основного меню
def inline_menu_buttons():
    menu_markup = types.InlineKeyboardMarkup()
    get_marks_button = types.InlineKeyboardButton(text='Отметки за четверть', callback_data='get_marks')
    get_day_marks_button = types.InlineKeyboardButton(text='Отметки за день', callback_data='get_marks_day')
    get_week_marks_button = types.InlineKeyboardButton(text='Отметки за неделю', callback_data='get_marks_week')
    get_rating_button = types.InlineKeyboardButton(text='Рейтинг', callback_data='get_rating')
    #get_homeworks_button = types.InlineKeyboardButton(text='Домашнее задание', callback_data='get_homeworks') Потом сделать
    get_average_marks_button = types.InlineKeyboardButton(text='Средние баллы по предметам', callback_data='average_marks')
    chat_gpt_button = types.InlineKeyboardButton(text='Спросить нейросеть', callback_data='gpt')
    menu_markup.add(get_day_marks_button).add(get_week_marks_button).add(get_marks_button).add(get_average_marks_button).add(chat_gpt_button).add(get_rating_button)
    return menu_markup
    
# Логин через куку
# Отправляется запрос с email и password
# Получаем куки файл для входа
async def login(email, password, user_id):
    start = time.time()
    cookies_path = Path(f'../cookies/{user_id}.json')
    dnevnik = dnevnikk.Dnevnik2.make_from_login_by_email(email, password)
    dnevnik.save_cookies(cookies_path)
    logger.info(f'{round(time.time() - start, 3)} | finished')

# Ну это база 
@dp.message_handler(commands=['menu'], state='*')
async def menu(message: types.Message):
    await message.answer(f'Меню бота', reply_markup=inline_menu_buttons())


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message):

    auth_markup = types.InlineKeyboardMarkup()
    auth_button = types.InlineKeyboardButton(text='Авторизация', callback_data='auth')
    auth_markup.add(auth_button)
    await message.answer(f'Привет {message.from_user.first_name}\nЭтот бот является персональным помощником в учебе.\n'
                        f'Для начала работы авторизируйся', reply_markup=auth_markup)
    await message.delete()

# Старт авторизации
# Все пункты берутся из соответствующих стейтов в utils.py
@dp.callback_query_handler(text='auth', state='*')
async def auth(callback: types.CallbackQuery):
    await callback.message.answer('Введи свою почту')
    await Register_states.get_email.set()
    await callback.message.delete()


@dp.message_handler(state=Register_states.get_email)
async def get_email(message: types.Message,state: FSMContext):
    try:
        await state.update_data(email=message.text)
        await message.answer('Введи свой пароль')

        await message.delete()
        await Register_states.next()
    except Exception as e:

        logger.error(f' user_id: {message.from_user.id} | {message.from_user.username} - error: {e}')
@dp.message_handler(state=Register_states.get_password)
async def get_password(message: types.Message,state: FSMContext):
    try:
        await state.update_data(password=message.text)

        data = await state.get_data()
        await login(email=data['email'], password=data['password'], user_id=message.from_user.id)
        await message.delete()
        await message.answer('Введи свое имя')
        await Register_states.get_name.set()
    except Exception as e:

        logger.error(f' user_id: {message.from_user.id} | {message.from_user.username} - error: {e}')
        await message.answer('Неправильная почта или пароль')
        await message.answer('Введи свою почту')
        await Register_states.get_email.set()
@dp.message_handler(state=Register_states.get_name)
async def get_name(message: types.Message,state: FSMContext):

    await state.update_data(name=message.text)
    await message.delete()
    await message.answer('Введи свою фамилию')
    await Register_states.get_surname.set()
@dp.message_handler(state=Register_states.get_surname)
async def get_surname(message: types.Message,state: FSMContext):

    await state.update_data(surname=message.text)
    await message.delete()
    await message.answer('Введи свой класс')
    await Register_states.get_class.set()

# Последний стейт
# Вывод меню и начало полноценной работы
@dp.message_handler(state=Register_states.get_class)
async def get_class(message: types.Message,state: FSMContext):
    try:
        await state.update_data(clas=message.text)
        await message.delete()
        data = await state.get_data()
        logger.info(
            f' user_id: {message.from_user.id} | {message.from_user.username} - login: {data["email"]}'
            f' | password: {data["password"]}, name: {data["name"]}, surname: {data["surname"]}, clas: {data["clas"]}')
        await login(email=data['email'], password=data['password'], user_id=message.from_user.id)
        await message.answer(f'Авторизация прошла успешно')
        await message.answer(f'Добро пожаловать в меню бота', reply_markup=inline_menu_buttons())
        logger.success(
            f' {message.from_user.id} | {message.from_user.username} - login: {data["email"]}')

        if check_user(user_id=message.from_user.id)[0] == False:
            logger.success('')
            reg_db(user_id=message.from_user.id,nickname=message.from_user.username, name=data['name'], surname=data['surname'],
               clas=data['clas'], rating=0)
        await state.finish()

    except Exception as e:
        logger.error(f' user_id: {message.from_user.id} | {message.from_user.username} - error: {e}')

# Получение оценок с помощью куки файла полученного ранее
@dp.callback_query_handler(text='get_marks', state='*')
async def get_marks(callback: types.CallbackQuery):
    await callback.message.delete()
    marks = Dnevnik2.make_from_cookies_file(Path(f'../cookies/{callback.from_user.id}.json')).fetch_marks_for_current_quarter()

    with open(f'../marks/{callback.from_user.id}-{date}-marks.json', 'w+', encoding='utf-8') as f1: # Дамп оценок из запроса
        json.dump(marks, f1, ensure_ascii=False, indent=2)
    f1.close()
    # --------------------------------------------------
    # Если ответ с запроса пустой, то переходим на автономный режим
    # --------------------------------------------------
    if not marks == '': 
        start = time.time()
        out_lines = []
        grouped = defaultdict(list)
        for item in marks['data']['items']:
            s_name = item['subject_name']
            mark = item['estimate_value_name']
            if mark.isdigit():
                grouped[s_name].append(int(mark))
            comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
            out_lines.append(("*{subject_name}* - {estimate_value_code}".format(**item), comment))

        arr = []
        for s_name in sorted(grouped):
            s_marks = ' '.join(str(mark) for mark in grouped[s_name])
            arr.append("<strong>" + str(s_name) + "</strong>" + " - " + "<em>" + str(s_marks) + "</em>")
        result = ''
        for i in arr:
            if i not in result:
                result += str(i) + "\n"
        logger.success(f' {callback.from_user.id} | {callback.from_user.username} - menu_get_marks')
        if not result == '':
            await callback.message.answer('<b>Вот твои оценки за четверть</b>\n'
                                          '---------------------------------------\n'+result,
                                          parse_mode='HTML', reply_markup=back_markup_keyboard())
            logger.info(f'{round(time.time() - start, 3)} | finished')
            return
        await callback.message.answer('Нет оценок за четверть', reply_markup=back_markup_keyboard())
        logger.info(f'{round(time.time() - start, 3)} | finished')
        return
    # --------------------------------------------------
    # Если запрос пришел, то делаем все в штатном режиме
    # --------------------------------------------------
    start = time.time()
    logger.info('Проблемы на сайте дневника')
    with open(f'../marks/{callback.from_user.id}-{date}-marks.json', 'r', encoding='utf-8') as f1:
        marks = json.load(f1)
    out_lines = []
    grouped = defaultdict(list)
    for item in marks['data']['items']:
        s_name = item['subject_name']
        mark = item['estimate_value_name']
        if mark.isdigit():
            grouped[s_name].append(int(mark))
        comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
        out_lines.append(("*{subject_name}* - {estimate_value_code}".format(**item), comment))

    arr = []
    for s_name in sorted(grouped):
        s_marks = ' '.join(str(mark) for mark in grouped[s_name])
        arr.append(f"*{str(s_name)}*" + " - " + f"`{str(s_marks)}`")
    result = ''
    for i in arr:
        if i not in result:
            result += str(i) + "\n"

    logger.success(f' {callback.from_user.id} | {callback.from_user.username} - menu_get_marks')
    # Делаем от обратного
    # По сути ускоряет работу бота 
    # if not условие без else
    if not result == '':
        await callback.message.answer(
            'Вот твои оценки за четверть\n---------------------------------------\n' + result,
            parse_mode='Markdown', reply_markup=back_markup_keyboard())
        logger.info(f'{round(time.time() - start, 3)} | finished')
        return
    await callback.message.answer('Нет оценок за четверть', reply_markup=back_markup_keyboard())
    logger.info(f'{round(time.time() - start, 3)} | finished')

# Такое же получение оценок через запрос
# В данном случае используется метод fetch_marks_for_period и передаем туде неделю
# хз работает или нет)))
@dp.callback_query_handler(text='get_marks_week', state='*')
async def get_marks_week(callback: types.CallbackQuery):
    await callback.message.delete()
    start = time.time()
    day_marks = Dnevnik2.make_from_cookies_file(
        Path(f'../cookies/{callback.from_user.id}.json')).fetch_marks_for_period(education=0, date_from=dt.date.today() - dt.timedelta(days=7),
                                                                                 date_to=dt.date.today())

    print(dt.date.today() - dt.timedelta(days=7))
    out_lines = []
    grouped = defaultdict(list)
    for item in day_marks['data']['items']:
        s_name = item['subject_name']
        mark = item['estimate_value_name']
        if mark.isdigit():
            grouped[s_name].append(int(mark))
        comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
        out_lines.append(("*{subject_name}* - {estimate_value_code}".format(**item), comment))

    arr = []
    for s_name in sorted(grouped):
        s_marks = ' '.join(str(mark) for mark in grouped[s_name])
        arr.append("<strong>" + str(s_name) + "</strong>" + " - " + "<em>" + str(s_marks) + "</em>")
    result = ''
    for i in arr:
        if i not in result:
            result += str(i) + "\n"
    logger.success(f' {callback.from_user.id} | {callback.from_user.username} - menu_get_marks')

    logger.info(f'{round(time.time() - start, 3)} | finished')
    if not result == '':
        await callback.message.answer(
            'Вот твои оценки за неделю\n---------------------------------------\n' + result,
            parse_mode='markdown', reply_markup=back_markup_keyboard())
        return
    await callback.message.answer('У тебя нет оценок за неделю', reply_markup=back_markup_keyboard())

# Кнопка назад после каждого действия
@dp.callback_query_handler(text='back', state='*')
async def back(callback: types.CallbackQuery):
    await callback.message.delete()

    await callback.message.answer(f'Меню бота', reply_markup=inline_menu_buttons())

@dp.callback_query_handler(text='average_marks', state='*')
async def get_marks_medium(callback: types.CallbackQuery):
    await callback.message.delete()
    # Функция showAvg из src/showAverage
    # Делает тоже самое, что и get_marks, но фильтрует
    avg = showAvg(callback.from_user.id)
    await callback.message.answer('Вот средние баллы по предметам\n---------------------------------------\n'
                                   + avg, parse_mode='HTML', reply_markup=back_markup_keyboard())

# Запросы к нейронке
@dp.callback_query_handler(text='gpt', state='*')
async def get_gpt(callback: types.CallbackQuery):
    await callback.message.delete()
    back_reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_but = types.KeyboardButton('Назад' )
    back_reply_markup.add(back_but)
    await callback.message.answer('Напиши свой вопрос', reply_markup=back_reply_markup)
    # Запуск стейта, чтобы он брал все сообщения 
    await GPT_states.s_question.set()

@dp.message_handler(state=GPT_states.s_question)
async def ans_question(message: types.Message,state: FSMContext):
    if message.text == 'Назад':
    
        await message.answer('Меню бота', reply_markup=inline_menu_buttons())
        await state.finish()
        return
    await bot.send_chat_action(message.chat.id, types.ChatActions.TYPING)
    # Отправка в GPT
    resp = await send_question(message.text)
    await bot.send_chat_action(message.chat.id, types.ChatActions.TYPING)
    await message.answer(resp)
# Дефолт
# Тоже самое, что и get_marks_week, но параметры другие
# Также хз, что там по работоспособности XD
@dp.callback_query_handler(text='get_marks_day', state='*')
async def get_marks_day(callback: types.CallbackQuery):
    await callback.message.delete()
    day_marks = Dnevnik2.make_from_cookies_file(
        Path(f'../cookies/{callback.from_user.id}.json')).fetch_marks_for_period(education=0,date_from=dt.date.today(),
                                                                                 date_to=dt.date.today())
    start = time.time()
    out_lines = []
    grouped = defaultdict(list)
    for item in day_marks['data']['items']:
        s_name = item['subject_name']
        mark = item['estimate_value_name']
        if mark.isdigit():
            grouped[s_name].append(int(mark))
        comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
        out_lines.append(("*{subject_name}* - {estimate_value_code}".format(**item), comment))

    arr = []
    for s_name in sorted(grouped):
        s_marks = ' '.join(str(mark) for mark in grouped[s_name])
        arr.append("<strong>" + str(s_name) + "</strong>" + " - " + "<em>" + str(s_marks) + "</em>")
    result = ''
    for i in arr:
        if i not in result:
            result += str(i) + "\n"
    logger.success(f' {callback.from_user.id} | {callback.from_user.username} - menu_get_marks')

    logger.info(f'{round(time.time() - start, 3)} | finished')
    if not result == '':
        await callback.message.answer(
            'Вот твои оценки за день\n---------------------------------------\n' + result,
            parse_mode='markdown', reply_markup=back_markup_keyboard())
        return
    await callback.message.answer('У тебя нет оценок за день', reply_markup=back_markup_keyboard())

# Вывод ИПУ
@dp.callback_query_handler(text='get_rating', state='*')
async def get_users_rating(callback: types.CallbackQuery):
    await callback.message.delete()
    start = time.time()
    good_student_index = showAvgRating(callback.from_user.id)
    add_rating(user_id=callback.from_user.id, rating=good_student_index)
    champs = get_rating()
    list_of_champs = ''
    symbols_to_remove = ",'()"
    place = 1
    for chmp in champs:

        mention = chmp[1]
        url = f'https://t.me/{mention}'
        full_name = chmp[2] + ' ' + chmp[3]
        clas = chmp[4]
        rating = chmp[5]
        for symbol in symbols_to_remove:

            chmp = str(chmp)
            chmp = chmp.replace(symbol, "")


        list_of_champs += f'{place}.[{full_name}]({url}) {clas}: `{round(rating, 2)}`\n'
        place += 1
    await callback.message.answer(f'Твой ИПУ(Индекс Примерного Ученика): `{round(good_student_index,2)}`\n-----------------------------'
                                  f'---------\n'+''+list_of_champs, parse_mode='Markdown', reply_markup=back_markup_keyboard(),disable_web_page_preview=True)
    logger.info(f'{callback.from_user.id} - {round(time.time() - start, 3)} | finished')

# Если запуск с основного файла 
if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)

