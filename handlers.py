from aiogram.filters import CommandStart, Command  # , StateFilter
# import copy
import sqlite3 as sqlite
from aiogram import types, F  # , Bot
# from aiogram.types import Message
from loader import msg_router, callback_router, bot  # , dp
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from random import *
from aiogram.utils.keyboard import InlineKeyboardBuilder


class RegisterState(StatesGroup):
    writing_gender = State()
    registered = State()


@msg_router.message(CommandStart())  # реакция на команду /start
async def cmd_start_handler(msg: types.Message) -> None:
    await msg.answer(f"Привет, {msg.from_user.first_name}.")
    builder = InlineKeyboardBuilder()
    builder.button(text="Зарегистрироваться", callback_data="register")
    await msg.answer("Это сервис для диалогов вслепую! \n"
                     "Чтобы начать поиск собеседника, вам нужно сначала зарегистрироваться.",
                     reply_markup=builder.as_markup(resize_keyboard=True))


@msg_router.message(Command('find'), RegisterState.registered)  # реакция на команду /find
async def message_find(message: types.Message, state: FSMContext):
    await cmd_find_handler(message, state)


@msg_router.message(Command('open'), RegisterState.registered)  # реакция на команду /open
async def cmd_open_handler(msg: types.Message) -> None:
    await msg.answer("Теперь вас могут найти собеседники!")
    await msg.answer("Если вы устали от общения, то  можете использовать /close!")
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()

        cursor.execute(f'''UPDATE Users SET hidden = 0 WHERE user_id = {msg.from_user.id}''')
        conn.commit()
    except Exception as e:
        print(e)
        await msg.answer("Произошла непредвиденная ошибка!")


@msg_router.message(Command('close'), RegisterState.registered)  # реакция на команду /close
async def cmd_close_handler(msg: types.Message) -> None:
    await msg.answer("Теперь вас не могут найти собеседники!")
    await msg.answer("Если вы снова хотите общаться, то можете использовать /open!")
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()

        cursor.execute(f'''UPDATE Users SET hidden = 1 WHERE user_id = {msg.from_user.id}''')
        conn.commit()
    except Exception as e:
        print(e)
        await msg.answer("Произошла непредвиденная ошибка!")


@msg_router.message(Command('break'), RegisterState.registered)  # реакция на команду /close
async def cmd_break_handler(msg: types.Message) -> None:
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT * FROM Users WHERE user_id = {msg.from_user.id}''')
        user = cursor.fetchone()
        cursor.execute(f'''UPDATE Users SET link_id = -1 WHERE user_id = {user[3]}''')
        cursor.execute(f'''UPDATE Users SET link_id = -1 WHERE user_id = {msg.from_user.id}''')
        conn.commit()
        await msg.answer("Вы разорвали связь")
        await msg.answer("Если вы снова хотите общаться, то можете использовать /open!\n"
                         "Чтобы найти собеседника, используйте команду /find!")
        await bot.send_message(user[3], "Похоже, ваш собеседник разорвал с вами диалог!\n"
                                        "Сочувствуем вам!")
    except Exception as e:
        print(e)
        await msg.answer("Произошла непредвиденная ошибка!")


@msg_router.message(Command('profile'), RegisterState.registered)  # реакция на команду /close
async def cmd_break_handler(msg: types.Message) -> None:
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT * FROM Users WHERE user_id = {msg.from_user.id}''')
        user = cursor.fetchone()
        await msg.answer("Ваш профиль:\n"
                         f"Пользователь #{user[0]}\n"
                         f"ID пользователя: {user[1]}\n"
                         f"Пол:{user[2]}\n"
                         f"ID собеседника:{user[3]}\n"
                         f"Открыт:{user[4] == 1}\n")

    except Exception as e:
        print(e)
        await msg.answer("Произошла непредвиденная ошибка!")


@msg_router.message(RegisterState.writing_gender)  # функция обработки ввода пола
async def gender_handler(msg: types.Message, state: FSMContext) -> None:
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT * FROM Users WHERE user_id = {msg.from_user.id}''')
        users = cursor.fetchall()
        if len(users) < 1:
            cursor.execute(f'''INSERT INTO Users (user_id, gender, link_id, hidden) VALUES ({msg.from_user.id}, ?,-1, 1)
                ''', msg.text)

            conn.commit()
            await state.set_state(RegisterState.registered)
            await msg.answer("Отлично, регистрация завершена!")
            await msg.answer("Чтобы вас могли найти собеседники, используйте команду /open!\n"
                             "Чтобы найти собеседника, используйте команду /find!")
        else:
            await state.set_state(RegisterState.registered)
            await msg.answer("Кажется, ваш аккаунт уже был зарегистрирован здесь когда-то")
            await msg.answer("Чтобы вас могли найти собеседники, используйте команду /open!\n"
                             "Чтобы найти собеседника, используйте команду /find!")
    except Exception as e:
        print(e)
        await msg.answer("Произошла непредвиденная ошибка!")


@msg_router.message(RegisterState.registered)  # реакция на рандомные сообщения
async def reroute_words(msg: types.Message) -> None:
    conn = sqlite.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM Users WHERE user_id = {msg.from_user.id}''')
    user = cursor.fetchone()
    link = user[3]
    if link != -1:
        if msg.text:
            await bot.send_message(link, msg.text)
        elif msg.photo is not None:
            await bot.send_photo(link, photo=msg.photo[-1].file_id,
                                 caption=msg.text)
        elif msg.document is not None:
            await bot.send_document(link, document=msg.document.file_id,
                                    caption=msg.text)
    else:
        await msg.answer("?")


@msg_router.message()
async def random_words(msg: types.Message) -> None:
    await msg.answer("Запустите бота /start для регистрации")


@callback_router.callback_query(F.data == "register")  # функция регистрации
async def register(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RegisterState.writing_gender)
    await bot.send_message(callback.message.chat.id, "Ваша регистрация почти завершена, осталось лишь ввести пол!")


@callback_router.callback_query(F.data == 'find')  # вызов поиска через кнопку
async def inline_find(callback: types.CallbackQuery, state: FSMContext):
    message = await state.get_data()
    await callback.message.delete()
    await cmd_find_handler(message['msg'], state)


@callback_router.callback_query(F.data == 'finish_find')  # прекратить поиск собеседника
async def inline_finish(callback: types.CallbackQuery):
    await callback.message.delete()


@callback_router.callback_query(F.data.find('accept_invite') != -1)  # принять приглашение
async def inline_finish(callback: types.CallbackQuery):
    sender_id = int((callback.data.split('/'))[1])
    await callback.message.delete()
    conn = sqlite.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM Users WHERE user_id = {callback.message.chat.id}''')
    users = cursor.fetchone()
    cursor.execute(f'''SELECT * FROM Users WHERE user_id = {sender_id}''')
    sender = cursor.fetchone()
    if sender[3] == -1:
        cursor.execute(f'''UPDATE Users SET link_id={sender_id} WHERE user_id = {callback.message.chat.id}''')
        cursor.execute(f'''UPDATE Users SET link_id={callback.message.chat.id} WHERE user_id = {sender_id}''')
        conn.commit()
        await bot.send_message(callback.message.chat.id, "Вы приняли приглашение!\n"
                                                         "Пора начать общение!\n"
                                                         "Для разрыва диалога используйте /break\n")
        await bot.send_message(sender_id, f"Отлично, пользователь #{users[0]} принял ваше приглашение!\n"
                                          f"Пора начать общение!\n"
                                          f"Для разрыва диалога используйте /break")
    else:
        await bot.send_message(callback.message.chat.id, "Похоже, этот человек уже нашёл другого собеседника!\n"
                                                         "Сочувствуем вам!\n"
                                                         "Может, стоит уделять чату больше внимания?\n")


@callback_router.callback_query(F.data.find('reject_invite') != -1)  # принять приглашение
async def inline_finish(callback: types.CallbackQuery):
    sender_id = int((callback.data.split('/'))[1])
    await callback.message.delete()
    conn = sqlite.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM Users WHERE user_id = {callback.message.chat.id}''')
    users = cursor.fetchone()
    await bot.send_message(sender_id, f"К сожалению, пользователь #{users[0]} отклонил ваше приглашение")


@callback_router.callback_query(F.data == 'send_talk_request')  # отправить запрос на общение
async def send_request(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    await callback.message.delete()
    await bot.send_message(callback.message.chat.id, "Вы успешно отправили запрос на общение!")
    conn = sqlite.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM Users WHERE user_id = {user_data['sender_id']}''')
    users = cursor.fetchone()
    builder = InlineKeyboardBuilder()
    builder.button(text="Принять", callback_data=f"accept_invite/{callback.message.chat.id}")
    builder.button(text="Отклонить", callback_data=f"reject_invite/{callback.message.chat.id}")
    await bot.send_message(user_data['target_id'], "Вам пришёл запрос на общение!"
                                      f"Пользователь #{users[0]}:\n"
                                      f"Пол: {users[2]} \n",
                           reply_markup=builder.as_markup(resize_keyboard=True))


async def cmd_find_handler(msg: types.Message, state: FSMContext) -> None:  # функция поиска собеседника
    try:
        conn = sqlite.connect('my_database.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT * FROM Users WHERE hidden = 0 AND link_id = -1 AND user_id != {msg.from_user.id}''')
        users = cursor.fetchall()
        if len(users) < 1:
            builder = InlineKeyboardBuilder()
            builder.button(text="Закончили", callback_data="finish_find")
            builder.button(text="Поискать ещё", callback_data="find")
            await msg.answer("Похоже, никого кроме тебя нет!",
                             reply_markup=builder.as_markup(resize_keyboard=True))
        else:
            id_choice = randint(1, len(users))
            user = (users[id_choice - 1])
            builder = InlineKeyboardBuilder()
            builder.button(text="Общаться!", callback_data="send_talk_request")
            await state.update_data(target_id=user[1], sender_id=msg.from_user.id, msg=msg)
            builder.button(text="Поискать ещё", callback_data="find")
            builder.button(text="Закончили", callback_data="finish_find")
            builder.adjust(2, 1)
            await msg.answer(f"Пользователь #{user[0]}:\n"
                             f"Пол: {user[2]} \n"
                             f"Статус:свободен(на)", reply_markup=builder.as_markup(resize_keyboard=True))
    except Exception as e:
        print(e)
        await msg.answer("Произошла непредвиденная ошибка!")
