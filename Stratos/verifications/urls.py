from flask import blueprints, session, request, abort, redirect, render_template
from errors import *
from db import Session
import utils
import verifications
import files
import users
import datetime
import admin_log
import notify
import settings

app = blueprints.Blueprint('Verify', __name__, url_prefix='/verification/api')


@app.before_request
def before():
    setting = settings.Setting()
    if setting.tech_stop is True:
        return abort(500)


@app.route('/create')
def create():
    email = request.values.get('email', '', str)
    card_number = request.values.get('card', '', str)
    photo = request.values.get('photo', '', str)

    user = users.api.get_user_by_email(email)
    if user is None:
        user = users.api.create_user(email)

    check = verifications.api.check_verification(card_number, user.email)
    if check:
        return utils.get_error('Данная карта уже верифицирована')

    check = files.api.get_file(photo)
    if check is None:
        return utils.get_error('Фотография не найдена')

    verification = verifications.api.create_verification(card_number, user.id, user.email, photo)
    return utils.get_answer('', {'verification_id': verification})


@app.route('/get')
def get():
    verify_id = request.values.get('id', 0, int)

    verification = verifications.api.get_verification_by_id(verify_id)
    return utils.get_answer('', {'verification': verification})


@app.route('/set')
def set():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    verify_id = request.values.get('id', 0, int)
    status = request.values.get('status', 0, int)
    comment = request.values.get('comment', '', str)

    if status not in [1, -1]:
        return utils.get_error('Неверный статус')

    if status == -1 and len(comment) == 0:
        return utils.get_error('Необходим комментарий')

    db_session = Session()
    verification = db_session.query(verifications.api.Verification).get(verify_id)

    if verification is None:
        db_session.close()
        return utils.get_error('Объект не найден')

    if verification.status != 0:
        db_session.close()
        return utils.get_error('Этот объект нельзя изменить')

    verification.status = status
    verification.comment = comment
    verification.update_date = datetime.datetime.now()

    db_session.commit()
    db_session.close()

    return utils.get_answer('Сохранено')