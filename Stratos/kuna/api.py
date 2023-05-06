from db import Session
from errors import *
import requests
import hmac
import datetime
import hashlib
import json
import base64
import kuna.entities
import orders


API_KEY = '3gZEFx5jIWc7uU6UZynIEaz6T2Qk6K4svbqXHgNs'
API_SECRET = 'Qd0t91Ki8a89rD1D6jbYAUa3wZxyTFaomibkIhAc'


def get_sign(nonce, path, data):
    path = path[19:]
    body = '{}{}{}'.format(
        path, nonce, data if len(data) > 0 else ''
    )
    print(body)
    payload = body.encode('ascii')
    sign = hmac.new(API_SECRET.encode('ascii'), payload, hashlib.sha384).hexdigest()
    return sign


def get_payment(order):
    url_path = 'https://api.kuna.io/v3/auth/merchant/deposit'
    data = {
        "currency": "rub",
        "amount": round(float(order.give_rub), 2),
        "payment_service": "payment_card_rub_hpp",
        "return_url": "https://StratosChange.ru/order/{}".format(order.secret_key),
        "callback_url": "https://StratosChange.ru/kuna/callback",
        "fields": {"card_number": "4276130011112222"}
    }
    nonce = int(datetime.datetime.now().timestamp()) * 1000

    data = json.dumps(data)

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'kun-nonce': str(nonce),
        'kun-apikey': API_KEY,
        'kun-signature': get_sign(nonce, url_path, data),
    }

    response = requests.post(url_path, headers=headers, data=data)

    print(response.status_code, response.text)
    print(json.dumps(response.json(), ensure_ascii=False, indent=4))
    if response.status_code != 200:
        raise IncorrectDataValue('Merchant is down')

    result = response.json()
    payment_url = 'https://paygate.kuna.io/hpp?cpi=' + result['payment_invoice_id']
    session = Session()
    payment = kuna.entities.KunaPayment(order_code=order.code, order_secret=order.secret_key,
                                        payment_link=payment_url, deposit_id=result['deposit_id'])
    order = session.query(orders.api.Order).get(order.id)
    order.payment_url = payment_url
    session.add(payment)
    session.commit()
    session.close()


def get_payment_methods():
    url_path = 'https://api.kuna.io/v3/auth/merchant/payment_services'
    data = {
        "currency": "rub",
    }
    nonce = int(datetime.datetime.now().timestamp()) * 1000

    data = json.dumps(data)

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'kun-nonce': str(nonce),
        'kun-apikey': API_KEY,
        'kun-signature': get_sign(nonce, url_path, data),
    }

    response = requests.post(url_path, headers=headers, data=data)

    print(json.dumps(response.json(), ensure_ascii=False, indent=4))


def get_payment_by_order_code(order_code):
    with Session() as session:
        payment = session.query(kuna.entities.KunaPayment).filter(kuna.entities.KunaPayment.order_code == order_code).first()
    return payment


def get_payment_by_deposit_id(deposit_id):
    with Session() as session:
        payment = session.query(kuna.entities.KunaPayment).filter(kuna.entities.KunaPayment.deposit_id == deposit_id).first()
    return payment