from db import Session
from .entities import Recovery
from errors import *
import users
import utils
import config


def get_recoveries_by_user(user_id, status=None):
    with Session() as db_session:
        if status is None:
            recoveries = db_session.query(Recovery).filter(Recovery.user_id == user_id).all()
        else:
            recoveries = db_session.query(Recovery).filter(Recovery.user_id == user_id, Recovery.status == status).all()
    return recoveries


def get_recovery_by_code(code):
    with Session() as db_session:
        recovery = db_session.query(Recovery).filter(Recovery.code == code).first()
    return recovery


def activate(code):
    db_session = Session()
    recovery = db_session.query(Recovery).filter(Recovery.code == code).first()
    if recovery is None:
        db_session.close()
        raise False
    user = db_session.query(users.api.User).filter(users.api.User.id == recovery.user_id).first()

    recovery.status = 1
    user.password = utils.get_random_code(8)
    db_session.commit()

    message = f"""Ваша новый пароль: {user.password}"""
    utils.email(user.email, 'StratosChange.ru: Восстановление пароля', message)

    db_session.close()
    return True


def create_recovery(user):
    with Session() as db_session:
        recovery = Recovery(user_id=user.id, user_email=user.email)
        db_session.add(recovery)
        db_session.commit()

        message = f"""Ваша ссылка для восстановления пароля: {config.DOMAIN_NAME}/recoveries/api/activate/{recovery.code}"""
        utils.email(user.email, 'StratosChange.ru: Восстановление пароля', message)

    return recovery
