from flask import Flask, request, session, render_template, redirect, send_file, abort, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from db import Session, init_db
from uuid import uuid4
from threading import Thread
from flask_cors import CORS
import decimal
import utils
import tools
import pairs
import notify
import admin
import api
import files
import verifications
import orders
import settings
import withdraws
import recoveries
import json
import users
import autochange
import whitebit
import json
import datetime
import traceback
import kuna
import admin_log

Thread(target=notify.start_polling).start()
Thread(target=pairs.api.auto_update).start()
Thread(target=autochange.check_plans).start()

init_db()

app = Flask(__name__)
app.secret_key = '12rk23-j tn21qqwrqf_!23%$@!)r923j4-9324321padg2t3214______qw4$#@!%!#@5&&%34'
app.register_blueprint(tools.app)
app.register_blueprint(admin.app)
app.register_blueprint(pairs.app)
app.register_blueprint(api.app)
app.register_blueprint(files.app)
app.register_blueprint(verifications.app)
app.register_blueprint(orders.app)
app.register_blueprint(withdraws.app)
app.register_blueprint(recoveries.app)
CORS(app)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

bad_ip = []

# limiter = Limiter(
#     app,
#     key_func=utils.get_addr,
#     default_limits=["100 per minute", '2 per second']
# )
# limiter.limit('10/hour')(files.app)

pairs.api.generate_export_xml()

orders.api.check_deals()


@app.route('/')
def hello_world():
    user = utils.get_user(session)
    ref_id = request.values.get('rid', '', str)
    recovery = request.values.get('recovery', 0, int)
    auth = request.values.get('auth', 0, int)
    setting = settings.Setting()
    email = session['email'] if session.get('email') is not None else ''

    cur_from = request.values.get('cur_from', '', str)
    cur_to = request.values.get('cur_to', '', str)

    tool_from = None
    tool_to = None

    if len(cur_from) > 0:
        print('cur_from', cur_from)
        tool_from = tools.api.get_tool_by_xml_code(cur_from)
        print(tool_from)
        if tool_from is not None:
            tool_from = tool_from.id
    if len(cur_to) > 0:
        tool_to = tools.api.get_tool_by_xml_code(cur_to)
        if tool_to is not None:
            tool_to = tool_to.id

    print(tool_from, tool_to)

    token = str(uuid4())
    api.create_tokens.append(token)

    print('user', user)

    return render_template('client/index.html', nav=1, len=len, ref_id=ref_id, setting=setting, email=email, auth=auth,
                           recovery=recovery, tool_from=tool_from, tool_to=tool_to, create_token=token)


@app.route('/login')
def login():
    user = utils.get_user(session)
    if user is None:
        user = users.api.get_user_by_email(session.get('email'))
        return redirect('/?auth=1')

    setting = settings.Setting()
    email = session['email'] if session.get('email') is not None else ''

    orders_list = orders.api.get_orders_by_user_id(user.id)
    ref_transactions = orders.api.get_ref_transactions_by_user_id(user.id)
    withdraws_list = withdraws.api.get_withdraws_by_user_id(user.id)
    return render_template('client/me.html', user=user, nav=5, len=len, setting=setting, email=email, orders=orders_list,
                           ref_transactions=ref_transactions, withdraws=withdraws_list)


@app.route('/referral')
def referral():
    user = utils.get_user(session)
    if user is None:
        user = users.api.get_user_by_email(session.get('email'))
        return redirect('/?auth=1')

    setting = settings.Setting()
    email = session['email'] if session.get('email') is not None else ''

    orders_list = orders.api.get_orders_by_user_id(user.id)
    ref_transactions = orders.api.get_ref_transactions_by_user_id(user.id)
    withdraws_list = withdraws.api.get_withdraws_by_user_id(user.id)
    return render_template('client/referral.html', user=user, nav=5, len=len, setting=setting, email=email, orders=orders_list,
                           ref_transactions=ref_transactions, withdraws=withdraws_list)


@app.route('/options')
def options():
    user = utils.get_user(session)
    if user is None:
        user = users.api.get_user_by_email(session.get('email'))
        return redirect('/?auth=1')

    setting = settings.Setting()
    email = session['email'] if session.get('email') is not None else ''

    orders_list = orders.api.get_orders_by_user_id(user.id)
    ref_transactions = orders.api.get_ref_transactions_by_user_id(user.id)
    withdraws_list = withdraws.api.get_withdraws_by_user_id(user.id)
    return render_template('client/options.html', user=user, nav=5, len=len, setting=setting, email=email, orders=orders_list,
                           ref_transactions=ref_transactions, withdraws=withdraws_list)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/order/<string:code>')
def order_url(code):
    user = utils.get_user(session)

    order = orders.api.get_order_by_secret_key(code)
    print('order', order)
    tool_from, tool_to = tools.api.get_tools_by_order(order)
    setting = settings.Setting()
    email = session['email'] if session.get('email') is not None else ''

    order.give_amount = order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))
    order.receipt_amount = order.receipt_amount.quantize(decimal.Decimal(tool_to.rounded_str))

    if order.status == 1 and order.exchange_wallet == 'whitebit':
        payment = whitebit.api.get_payment_by_order_code(order.code)
        whitebit.api.check_payment(payment)
        order = orders.api.get_order_by_secret_key(code)

    deadline = (int(order.create_date.timestamp()) + (setting.order_minutes * 60))
    deadline *= 1000
    if order.status == 0:
        return render_template('client/index_buy.html', user=user, nav=0, email=email, len=len, order=order,
                               tool_from=tool_from, tool_to=tool_to, setting=setting, deadline=deadline)
    else:
        return render_template('client/index_buy.html', user=user, nav=0, email=email, len=len, order=order,
                               tool_from=tool_from, tool_to=tool_to, setting=setting, deadline=deadline)


@app.route('/order-expired/<string:code>')
def order_expired_url(code):
    user = utils.get_user(session)

    with Session() as db_session:
        order = db_session.query(orders.api.Order).filter(orders.api.Order.secret_key == code).first()

        email = session['email'] if session.get('email') is not None else ''

        if order.status == 0:
            order.status = -1
            event = orders.api.Event(event='Сделка отменена по истечению таймера', order_id=order.id)
            db_session.add(event)
            db_session.commit()

            message = f"""Вы отменили заявку!
Будем рады вас видеть в следующий раз у нас на сервисе.

Информация о заявке:
{order.get_info()}

С уважением, администрация StratosChange"""
            utils.email(order.client_email, 'StratosChange.ru: Сделка отменена', message)

        if order.status > 0:
            return redirect('/confirm/{}'.format(order.secret_key))

    setting = settings.Setting()
    return render_template('client/index_buy.html', user=user, nav=0, email=email, len=len, order=order, setting=setting)


@app.route('/confirm/<string:code>')
def confirm(code):
    user = utils.get_user(session)

    with Session() as db_session:
        order = db_session.query(orders.api.Order).filter(orders.api.Order.secret_key == code).first()

    if order.status == -1:
        return redirect('/order-expired/{}'.format(order.secret_key))

    email = session['client_email'] if session.get('client_email') is not None else ''

    if order.status == 0:
        setting = settings.Setting()
        if len(setting.autocommit) > 0 and setting.autocommit == order.to_wallet:
            orders.api.change_order_status(order.id, 3, owner='Автообработка')
            message = 'Клиент нажал "Я оплатил"\nСделка завершена автообработкой.\n\n{}\n\nEmail: {}'.format(order.get_info(), email)
            notify.send_message(message)
        else:
            orders.api.change_order_status(order.id, 1)
            message = 'Клиент нажал "Я оплатил"\n\n{}\n\nEmail: {}'.format(order.get_info(), email)
            notify.send_message(message)
    return redirect('/order/{}'.format(order.secret_key))


@app.route('/status/<string:code>')
def status(code):
    user = utils.get_user(session)

    with Session() as db_session:
        order = db_session.query(orders.api.Order).filter(orders.api.Order.secret_key == code).first()
    return redirect('/order/{}'.format(order.secret_key))


@app.route('/questions')
def faq():
    user = utils.get_user(session)
    email = session['email'] if session.get('email') is not None else ''
    setting = settings.Setting()
    return render_template('client/questions.html', user=user, nav=2, email=email, len=len, setting=setting)


@app.route('/support')
def support():
    user = utils.get_user(session)
    email = session['email'] if session.get('email') is not None else ''
    setting = settings.Setting()
    return render_template('client/support.html', user=user, nav=2, email=email, len=len, setting=setting)


@app.route('/coupon')
def coupon():
    user = utils.get_user(session)
    email = session['email'] if session.get('email') is not None else ''
    setting = settings.Setting()
    return render_template('client/coupon.html', user=user, nav=2, email=email, len=len, setting=setting)


@app.route('/send_quest')
def send_quest():
    name = request.values.get('name', '', str)
    email = request.values.get('email', '', str)
    body = request.values.get('body', '', str)

    if len(body) == 0:
        return utils.get_error('Введите текст сообщения')
    if len(email) == 0:
        return utils.get_error('Укажите Email для ответа')

    notify.send_message('Сообщение с сайта\n\nИмя: {}\nEmail: {}\n\n{}'.format(name, email, body))
    return utils.get_answer('Сообщение успешно отправлено')


@app.route('/rules')
def rules():
    user = utils.get_user(session)
    email = session['email'] if session.get('email') is not None else ''
    setting = settings.Setting()
    return render_template('client/rules.html', user=user, nav=2, email=email, len=len, setting=setting)


@app.route('/about')
def about():
    user = utils.get_user(session)
    email = session['email'] if session.get('email') is not None else ''
    setting = settings.Setting()
    return render_template('client/about.html', user=user, nav=3, email=email, len=len, setting=setting)


@app.route('/partners')
def partners():
    user = utils.get_user(session)
    email = session['email'] if session.get('email') is not None else ''
    setting = settings.Setting()
    return render_template('client/partners.html', user=user, nav=4, email=email, len=len, setting=setting)


@app.route('/admin/orders/webhook', methods=['POST', 'GET'])
def hook():
    if request.method == 'GET':
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:

        try:
            message = 'Получен вебхук:\n\n{}'.format(json.dumps(request.get_json(), ensure_ascii=False, indent=3))
            notify.send_tech_message(message)
        except:
            pass

        method = str(request.get_json()['method'])
        if method != 'deposit.processed':
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


        wallet = request.get_json()['params']['address']
        amount = request.get_json()['params']['amount']
        ticker = request.get_json()['params']['ticker']
        actual_confirmations = request.get_json()['params']['confirmations']['actual']
        required_confirmations = request.get_json()['params']['confirmations']['required']

        value = decimal.Decimal(amount)

        # d_tag_str = d_tag
        # if len(d_tag) == 0:
        #     d_tag = None

        db_session = Session()
        order = db_session.query(orders.api.Order).filter(orders.api.Order.exchange_wallet == wallet).first()

        if order is None:
            message = '#Сделка_не_найдена #Депозит\n\nПолучен депозит:\n{} {}\n\nКошелёк:\n{}'.format(value, ticker,
                                                                                                      wallet)
            notify.send_deposit_message(message)
            db_session.close()
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

        if actual_confirmations < required_confirmations:
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

        tool_from = tools.api.get_tool_by_name(order.tool_from, order.tool_from_network)
        tool_to = tools.api.get_tool_by_name(order.tool_to, order.tool_to_network)
        value = value.quantize(decimal.Decimal(tool_from.rounded_str))

        from_from = tool_from.name if len(tool_from.cost_link) == 0 else tool_from.cost_link
        from_to = tool_to.name if len(tool_to.cost_link) == 0 else tool_to.cost_link

        if tool_from.network is not None:
            from_from += tool_from.network

        if tool_to.network is not None:
            from_to += tool_to.network

        course = '1 {} к {} {}'.format(from_from, order.current_cost, from_to) if len(tool_from.cost_link) == 0 else '1 {} к {} {}'.format(from_to, order.current_cost, from_from)

        if order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)) != value:
            receipt_amount = value * order.current_cost
            receipt_amount = receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str))
            receipt_rub = receipt_amount
            give_rub = receipt_amount
            event_change = orders.api.Event(event='[Webhook] Поступила сумма, отличная от необходимой. Заявка пересчита. '
                                                  'Должно быть поступить: {} {}  Поступило: {} {}  Должны были отправить: {} {}'
                                                  ' Пересчитано: {} {}'.format(order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)),
                                                                               tool_from.name, value, tool_from.name,
                                                                               order.receipt_amount.quantize(decimal.Decimal(tool_to.rounded_str)),
                                                                               tool_to.name, receipt_amount, tool_to.name),
                                            order_id=order.id)
            db_session.add(event_change)

            message = '#{} #Депозит\n\nПолучен депозит\n\nДепозит не соответствует сумме заявки\n\nСделка:\n{}\n\n' \
                      'Кошелёк:\n{}\n\nКлиент:\n{}\n\nОжидаемая сумма:\n{} {}\n\nФактическая сумма:\n{} {}\n\n' \
                      'Должны были перевести:\n{} {}\n\nПерерасчет: 🧮\n{} {}\n\nНа кошелёк/карту:\n{}\n\nКурс обмена: {}'.format(
                order.code, order.code, order.exchange_wallet, order.client_email,
                order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_from.name,
                value, tool_from.name, order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str)),
                tool_to.name, receipt_amount, tool_to.name, order.to_wallet, course
            )
            notify.send_deposit_message(message)

            order.give_amount = value
            order.receipt_amount = receipt_amount
            order.receipt_rub = receipt_rub
            order.give_rub = give_rub
            db_session.commit()
            orders.api.change_order_status(order.id, 2)
            db_session.close()

            message = f"""Мы получили ваш депозит ({order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_from.name} на {order.exchange_wallet})
    
    {order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_to.name} скоро будет отправлены Вам."""
            utils.email(order.client_email, 'StratosChange.ru: Депозит получен', message)

            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

        event_change = orders.api.Event(event='[Webhook] Поступило: {} {}'.format(
            order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_from.name), order_id=order.id)
        db_session.add(event_change)

        message = '#{} #Депозит\n\nПолучен депозит\n\nСделка:\n{}\n\n' \
                  'Кошелёк:\n{}\n\nКлиент:\n{}\n\nПолученный депозит:\n{} {}\n\n' \
                  'К получению:\n{} {}\n\nНа кошелёк/карту:\n{}\n\nКурс обмена: {}'.format(
            order.code, order.code, order.exchange_wallet, order.client_email,
            order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_from.name,
            order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_to.name, order.to_wallet, course
        )
        notify.send_deposit_message(message)

        db_session.commit()
        orders.api.change_order_status(order.id, 2)
        db_session.close()

        message = f"""Мы получили ваш депозит ({order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_from.name} на {order.exchange_wallet})
    
    {order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_to.name} скоро будет отправлены Вам."""
        utils.email(order.client_email, 'StratosChange.ru: Депозит получен', message)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


@app.route('/export.xml')
def export_file():
    setting = settings.Setting()
    if setting.prices_timer is False:
        return abort(404)
    return send_file('{}/static/export.xml'.format(utils.get_script_dir()))


@app.route('/robots.txt')
def robots_txt():
    return send_file('{}/static/robots.txt'.format(utils.get_script_dir()))


@app.route('/sitemap.xml')
def sitemap():
    return send_file('{}/static/sitemap.xml'.format(utils.get_script_dir()))


@app.route('/kuna/callback', methods=['POST'])
def kuna_callback():
    try:
        data = request.json
        session = Session()
        payment = session.query(kuna.entities.KunaPayment).filter(kuna.entities.KunaPayment.deposit_id == data['id']).first()
        payment.status = 1
        session.commit()
        session.close()
        orders.api.change_order_status(payment.order_id, 2, source='kuna')
    except:
        print(traceback.format_exc())
    return utils.get_answer('ok')


@app.route('/ccadmin', methods=['POST', 'GET'])
def ccadmin():
    user = utils.get_user(session)
    if request.method == 'GET':
        if user is not None and user.admin > 0:
            return redirect('/admin')
        return render_template('admin/auth.html')
    else:
        email = request.values.get('email', '', str)
        password = request.values.get('password', '', str)

        check = users.api.auth(session, email, password)
        if check is False:
            return utils.get_error('Неверный логин или пароль')

        user = users.api.get_user_by_email(email)
        if user.admin > 0:
            admin_log.create_log(request, user)
            return utils.get_answer('')
        else:
            session.clear()
            return utils.get_error('Access denied')


@app.route('/garantex/orders/webhook', methods=['POST', 'GET'])
def garantex_orders_webhook():
    if request.method == 'GET':
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:

        try:
            message = 'Получен вебхук Garantex:\n\n{}'.format(json.dumps(request.get_json(), ensure_ascii=False, indent=3))
            notify.send_tech_message(message)
        except:
            pass

        method = request.values.get('state', '', str)
        if method != 'accepted':
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

        wallet = request.values.get('address', '', str)
        amount = request.values.get('amount', '', str)
        ticker = request.values.get('currency', '', str)

        value = decimal.Decimal(amount)

        # d_tag_str = d_tag
        # if len(d_tag) == 0:
        #     d_tag = None

        db_session = Session()
        order = db_session.query(orders.api.Order).filter(orders.api.Order.exchange_wallet == wallet).first()

        if order is None:
            message = '#Сделка_не_найдена #Депозит\n\nПолучен депозит:\n{} {}\n\nКошелёк:\n{}'.format(value, ticker,
                                                                                                      wallet)
            notify.send_deposit_message(message)
            db_session.close()
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

        tool_from = tools.api.get_tool_by_name(order.tool_from, order.tool_from_network)
        tool_to = tools.api.get_tool_by_name(order.tool_to, order.tool_to_network)
        value = value.quantize(decimal.Decimal(tool_from.rounded_str))

        from_from = tool_from.name if len(tool_from.cost_link) == 0 else tool_from.cost_link
        from_to = tool_to.name if len(tool_to.cost_link) == 0 else tool_to.cost_link

        if tool_from.network is not None:
            from_from += tool_from.network

        if tool_to.network is not None:
            from_to += tool_to.network

        course = '1 {} к {} {}'.format(from_from, order.current_cost, from_to) if len(
            tool_from.cost_link) == 0 else '1 {} к {} {}'.format(from_to, order.current_cost, from_from)

        if order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)) != value:
            receipt_amount = value * order.current_cost
            receipt_amount = receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str))
            receipt_rub = receipt_amount
            give_rub = receipt_amount
            event_change = orders.api.Event(
                event='[Webhook Garantex] Поступила сумма, отличная от необходимой. Заявка пересчита. '
                      'Должно быть поступить: {} {}  Поступило: {} {}  Должны были отправить: {} {}'
                      ' Пересчитано: {} {}'.format(order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)),
                                                   tool_from.name, value, tool_from.name,
                                                   order.receipt_amount.quantize(decimal.Decimal(tool_to.rounded_str)),
                                                   tool_to.name, receipt_amount, tool_to.name),
                order_id=order.id)
            db_session.add(event_change)

            message = '#Garantex #{} #Депозит\n\nПолучен депозит\n\nДепозит не соответствует сумме заявки\n\nСделка:\n{}\n\n' \
                      'Кошелёк:\n{}\n\nКлиент:\n{}\n\nОжидаемая сумма:\n{} {}\n\nФактическая сумма:\n{} {}\n\n' \
                      'Должны были перевести:\n{} {}\n\nПерерасчет: 🧮\n{} {}\n\nНа кошелёк/карту:\n{}\n\nКурс обмена: {}'.format(
                order.code, order.code, order.exchange_wallet, order.client_email,
                order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_from.name,
                value, tool_from.name, order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str)),
                tool_to.name, receipt_amount, tool_to.name, order.to_wallet, course
            )
            notify.send_deposit_message(message)

            order.give_amount = value
            order.receipt_amount = receipt_amount
            order.receipt_rub = receipt_rub
            order.give_rub = give_rub
            db_session.commit()
            orders.api.change_order_status(order.id, 2)
            db_session.close()

            message = f"""Мы получили ваш депозит ({order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_from.name} на {order.exchange_wallet})

    {order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_to.name} скоро будет отправлены Вам."""
            utils.email(order.client_email, 'StratosChange.ru: Депозит получен', message)

            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

        event_change = orders.api.Event(event='[Webhook] Поступило: {} {}'.format(
            order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_from.name), order_id=order.id)
        db_session.add(event_change)

        message = '#Garantex #{} #Депозит\n\nПолучен депозит\n\nСделка:\n{}\n\n' \
                  'Кошелёк:\n{}\n\nКлиент:\n{}\n\nПолученный депозит:\n{} {}\n\n' \
                  'К получению:\n{} {}\n\nНа кошелёк/карту:\n{}\n\nКурс обмена: {}'.format(
            order.code, order.code, order.exchange_wallet, order.client_email,
            order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_from.name,
            order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str)), tool_to.name, order.to_wallet, course
        )
        notify.send_deposit_message(message)

        db_session.commit()
        orders.api.change_order_status(order.id, 2)
        db_session.close()

        message = f"""Мы получили ваш депозит ({order.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_from.name} на {order.exchange_wallet})

    {order.receipt_amount.quantize(decimal.Decimal(tool_from.rounded_str))} {order.t_to.name} скоро будет отправлены Вам."""
        utils.email(order.client_email, 'StratosChange.ru: Депозит получен', message)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/add_ip')
def add_ip():
    user = utils.get_user(session)
    if user.admin < 3:
        return abort(404)
    ip = request.values.get('ip', '', str)
    if len(ip) > 0:
        bad_ip.append(ip)

    ips = ''
    for i in bad_ip:
        ips += '{}<br>'.format(i)
    return ips


@app.route('/my_ip')
def my_ip():
    return utils.get_addr()


@app.route('/whiteBIT-verification')
def whiteBIT_verification():
    return app.response_class(
        response=json.dumps(['9a9f470721d18598e1a1f2a762cd12ae']),
        mimetype='application/json',
        status=200
    )


@app.route('/whiteBIT-verification.txt')
def whiteBIT_verification_txt():
    return send_file('9a9f470721d18598e1a1f2a762cd12ae.txt')


@app.before_request
def before_request():
    address = utils.get_addr()
    if address in bad_ip:
        notify.send_message('Запрос с заблокированного IP {}'.format(address))
        return abort(401)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009)
