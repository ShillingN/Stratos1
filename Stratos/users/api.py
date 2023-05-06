from db import Session
from .entities import User
from errors import *
import utils
import config


def auth(session, email, password):
    user = get_user_by_email(email)
    if user is None:
        return False
    if user.password == password:
        session['user_id'] = user.id
        session['email'] = user.email
        return True
    else:
        return False


def get_user_by_id(user_id):
    with Session() as db_session:
        user = db_session.query(User).filter(User.id == user_id).first()
    return user


def get_user_by_code(code):
    with Session() as db_session:
        user = db_session.query(User).filter(User.code == code).first()
    return user


def get_user_by_email(email, users_list=None):
    if users_list is None:
        with Session() as db_session:
            user = db_session.query(User).filter(User.email == email).first()
        return user
    else:
        result = None
        for user in users_list:
            if str(user.email).lower().strip() == str(email).lower().strip():
                result = user
                break
        return result


def get_users():
    with Session() as db_session:
        user = db_session.query(User).all()
    return user


def create_user(email, send_email=True):

    check = get_user_by_email(email)
    if check is not None:
        raise IncorrectDataValue('Данный Email уже занят')

    code = utils.get_random_code(8)
    check = get_user_by_code(code)
    if check is not None:
        while check is not None:
            code = utils.get_random_code(8)
            check = get_user_by_code(code)

    password = utils.get_random_code(8)
    with Session() as db_session:
        user = User(code=code, email=email, password=password, ref_percent=0.5)
        db_session.add(user)
        db_session.commit()

    user = get_user_by_code(code)

    message = f"""Ваш логин: {email}
Ваш пароль: {password}

Теперь вы можете отслеживать статус своих заявок в личном кабинете, а также участвовать в реферальной программе. 

Спасибо, что вы с нами! 
{config.DOMAIN_NAME}"""
    if send_email is True:
        utils.email(email, 'StratosChange.ru: Регистрация', message)
    return user