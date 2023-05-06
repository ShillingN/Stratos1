import json

from telebot import TeleBot

import utils
from db import Session
import notify.entities
import users

token = '5171535452:AAHy8du4yb3zPZJeevQnUK2UhmexEO9jkvY'
password = 'Stratos'

bot = TeleBot(token)


deposit_token = '5101686285:AAEgq8gxPU5sVBSPust7uMzbWBE_5dkVKAQ'
tech_token = '5228925279:AAFcyl8GKdl2bjuCLbrHftBEJ8kN3xIxIa0'

deposit_bot = TeleBot(deposit_token)
tech_bot = TeleBot(tech_token)


@bot.message_handler()
def in_message(message):
    tg_id = message.chat.id
    message = message.text

    with Session() as db_session:
        user = db_session.query(notify.entities.TgUser).filter(notify.entities.TgUser.tg_id == tg_id).first()

        if user is None and message != password:
            bot.send_message(tg_id, 'Вы не зарегистрированы.\n\nДля регистрации в боте введите пароль.')
            return

        if user is None and message == password:
            with Session() as db_session:
                tg_user = notify.entities.TgUser(tg_id=tg_id)
                db_session.add(tg_user)
                db_session.commit()
            bot.send_message(tg_id, 'Вы успешно зарегистрированы!')
            return

        if user is not None:
            bot.send_message(tg_id, 'Ожидайте сообщений')


def send_message(text):
    with Session() as db_session:
        users = db_session.query(notify.entities.TgUser).all()

        for user in users:
            try:
                bot.send_message(user.tg_id, text)
            except:
                continue


def send_me(text):
    try:
        send_message(text)
    except:
        pass


def send_tech_message(text):
    with Session() as db_session:
        users = db_session.query(notify.entities.TgUser).all()

        for user in users:
            try:
                tech_bot.send_message(user.tg_id, text)
            except:
                continue


def send_deposit_message(text):
    with Session() as db_session:
        users = db_session.query(notify.entities.TgUser).all()

        for user in users:
            try:
                deposit_bot.send_message(user.tg_id, text)
            except:
                continue


def hack_message(request, session):
    params = {}
    if request.method == 'GET':
        for param_name in request.values:
            params[param_name] = request.values.get(param_name)
    else:
        params = request.json

    headers = {}
    for header_row in request.headers:
        headers[header_row[0]] = header_row[1]

    email = session.get('email')
    user = None
    email_str = 'Не определён'
    level = 'Не администратор'
    if email is not None:
        email_str = email
        user = users.api.get_user_by_email(email)
        if user.admin == 0:
            level = 'Не администратор'
        elif user.admin == 1:
            level = 'Админ - просмотр'
        elif user.admin == 2:
            level = 'Админ - редактирование'
        elif user.admin == 3:
            level = 'Админ - редактирование+'
        else:
            level = 'Админ - {}'.format(user.admin)

    dop_user = utils.get_user(session)
    if dop_user is None:
        dop_user = 'Доп. проверка юзера: Не определён'
    else:
        dop_user = 'Доп. проверка юзера: {}'.format(user.email)

    message = 'Hack Attemption\n\nПопытка вызвать метод без соответствующего доступа\n\nЗапрашиваемый метод:\n{}' \
              '\nМетод запроса: {}\nПараметры запроса:\n{}\n\nЗаголовки запроса:\n{}\n\nПользователь: {}\nАдмин: {}\n{}'.format(
        request.path, request.method, json.dumps(params, ensure_ascii=False, indent=3),
        json.dumps(headers, ensure_ascii=False, indent=3), email_str, level, dop_user
    )

    send_me(message)


def start_polling():
    bot.polling()