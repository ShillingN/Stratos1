from flask import blueprints, session, request, abort, redirect, render_template
from errors import *
from db import Session
from .entities import Recovery
import utils
import users
import datetime
import recoveries

app = blueprints.Blueprint('Recovery', __name__, url_prefix='/recoveries/api')


@app.route('/create')
def create():
    email = request.values.get('email', '', str)
    user = users.api.get_user_by_email(email)

    if user is None:
        return utils.get_error('Пользователь с таким Email не найден')

    try:
        recovery = recoveries.api.create_recovery(user)
    except Exception as e:
        return utils.get_error(e.args[0])
    return utils.get_answer('Письмо с дальнейшими инструкциями отправлено на {}'.format(user.email))


@app.route('/activate/<string:code>')
def activate(code):
    result = recoveries.api.activate(code)
    if result:
        return redirect('/?recovery=1')
    else:
        return redirect('/?recovery=-1')