from flask import Response, request
from sqlalchemy.ext.declarative import DeclarativeMeta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import users
import random
import string
import inspect
import sys
import os
import json
import datetime
import decimal
import notify
import traceback
import smtplib
import settings
import re


def email(to, subject, text):
    # return requests.post("https://api.eu.mailgun.net/v3/cryptolavka.com/messages",
    #     auth=("api", "6b58cebc124989c7e0a446f99750453e-71b35d7e-3f0b73dd"),
    #     data={"from": "StratosChange <noreply@cryptolavka.com>",
    #         "to": [to],
    #         "subject": subject,
    #         "text": text})StratosChange.ru/test?header=Проверка!&text=Содержимое письма&to=j.kennedy@internet.ru
    # try:
    #     msg = MIMEMultipart()
    #     from_address = 'noreply@StratosChange.ru'
    #     msg['From'] = from_address
    #     msg['To'] = to
    #     msg['Subject'] = subject
    #
    #     body = text
    #     msg.attach(MIMEText(body, 'plain', 'utf-8'))
    #
    #     server = smtplib.SMTP('localhost')
    #     server.send_message(msg)
    #     server.quit()
    # except:
    #     print(traceback.format_exc())
    #     pass
    try:
        msg = MIMEMultipart()
        from_address = 'noreply@StratosChange.ru'
        msg['From'] = from_address  # Адресат
        msg['To'] = to  # Получатель
        msg['Subject'] = subject  # Тема сообщения

        body = text
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.mail.ru')
        server.starttls()
        server.login(from_address, '9MHPAgesHKb8XmmELFpG')
        server.send_message(msg)
        server.quit()
    except:
        print(traceback.format_exc())
        pass


def get_user(session):
    if session.get('user_id') is None:
        return None
    return users.api.get_user_by_id(session.get('user_id'))


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            return fields

        return json.JSONEncoder.default(self, obj)


def json_serial(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%d.%m.%Y %H:%M.%S')
    elif isinstance(obj.__class__, DeclarativeMeta):
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            if field in ['query', 'registry']:
                continue
            try:
                data = obj.__getattribute__(field)
                json.dumps(data, default=json_serial)
                fields[field] = data
            except:
                fields[field] = None
        return fields
    raise TypeError("Type %s not serializable" % type(obj))


def get_random_code(code_length, prefix=''):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=int(code_length)))
    if len(prefix) > 0:
        code = '{}_{}'.format(prefix, code)
    return code


def get_deal_code():
    setting = settings.Setting()

    order_id = setting.order_id
    order_id += 1

    setting.order_id = order_id
    setting.save()
    return 'C{}'.format(order_id)


def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False):
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


def get_error(error_text, status=200):
    print(error_text)
    res = {
        'status': 'error',
        'message': error_text
    }
    return Response(
        response=json.dumps(res, ensure_ascii=False),
        mimetype='application/json',
        status=status
    )


def get_answer(text, info=None):
    if info is None:
        info = {}
    res = {
        'status': 'ok',
        'message': text
    }
    answer = {**res, **info}
    return Response(
        response=json.dumps(answer, ensure_ascii=False, default=json_serial),
        mimetype='application/json',
        status=200
    )


def compare_days(one: datetime.datetime, two: datetime.datetime):
    if one.year == two.year and one.month == two.month and one.day == two.day:
        return True
    return False


def compare_date(one: datetime.datetime, two: datetime.datetime):
    if one.year == two.year and one.month == two.month and one.day == two.day and one.hour == two.hour and one.minute == two.minute:
        return True
    return False


def email_validate(email):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    if re.fullmatch(regex, email):
        return True
    else:
        return False


def get_addr():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        ips = str(request.environ['HTTP_X_FORWARDED_FOR'])
        if ',' in ips:
            ips = ips.split(',')[0]
        return ips