from threading import Timer
from uuid import uuid4

import garantex
from db import Session
import requests
import notify
import traceback
import time
import json
import base64
import hmac
import hashlib
import orders
import whitebit
import datetime
from garantex import get_cost as garantex_get_cost
from garantex import get_additional_address as garantex_get_add_address

v4_public_url = 'https://whitebit.com/api/v4/public/'
costs = {}
euro = 0


# public_key = '9a9f470721d18598e1a1f2a762cd12ae'
# private_key = '989f09b0f69edcfb658fe18bb00b0216'

public_key = '90e5dc9324e7224dd960192e265b59e3'
private_key = 'fbb734f3c58ae247e417413a67b1677b'


def check_payments():
    try:
        payments_list = get_deposit_history()
        db_session = Session()
        payments = db_session.query(whitebit.entities.WhitebitPayment).filter(
            whitebit.entities.WhitebitPayment.status == 0).all()

        for payment in payments:
            check_payment(payment, payments_list)
    except:
        print(traceback.format_exc())
    finally:
        Timer(1800, check_payments).start()


def check_payment(payment, payments_list=None):
    if payments_list is None:
        payments_list = get_deposit_history()

    for pay in payments_list:
        if pay['uniqueId'] == payment.deposit_id:
            if pay['status'] in [3, 7]:
                order = orders.api.get_order_by_code(payment.order_code)
                orders.api.change_order_status(order.id, 2, source='WhiteBit')
                db_session = Session()
                db_payment = db_session.query(whitebit.entities.WhitebitPayment).filter(whitebit.entities.WhitebitPayment.id == payment.id).first()
                db_payment.status = 1
                db_session.commit()
                db_session.close()
            else:
                if datetime.datetime.now().timestamp() - pay['createdAt'] > 86400:
                    db_session = Session()
                    db_payment = db_session.query(whitebit.entities.WhitebitPayment).filter(
                        whitebit.entities.WhitebitPayment.id == payment.id).first()
                    db_payment.status = False
                    db_session.commit()
                    db_session.close()



def get_deposit_history():
    api_key = public_key  # put here your public key
    secret_key = private_key  # put here your secret key
    requestpath = '/api/v4/main-account/history'
    baseUrl = 'https://whitebit.com'
    nonce = str(int(time.time()))

    data = {
        'transactionMethod': 1,
        'limit': 100,
        'offset': 0,
        'request': requestpath,
        'nonce': nonce
    }

    completeUrl = baseUrl + requestpath

    data_json = json.dumps(data, separators=(',', ':'))  # use separators param for deleting spaces
    payload = base64.b64encode(data_json.encode('ascii'))
    signature = hmac.new(secret_key.encode('ascii'), payload, hashlib.sha512).hexdigest()

    headers = {
        'Content-type': 'application/json',
        'X-TXC-APIKEY': api_key,
        'X-TXC-PAYLOAD': payload,
        'X-TXC-SIGNATURE': signature,
    }

    resp = requests.post(completeUrl, headers=headers, data=data_json)

    response = resp.json()
    return response['records']


def get_payment(order):
    api_key = public_key  # put here your public key
    secret_key = private_key  # put here your secret key
    requestpath = '/api/v4/main-account/fiat-deposit-url'
    baseUrl = 'https://whitebit.com'
    nonce = str(int(time.time()))

    unique_id = str(uuid4())
    data = {
        'ticker': 'RUB',
        'provider': 'ADVCASH',
        'amount': 5000,
        'uniqueId': unique_id,
        'request': requestpath,
        'nonce': nonce,
        'successLink': "https://StratosChange.ru/order/{}".format(order.secret_key),
        'failureLink': "https://StratosChange.ru/order/{}".format(order.secret_key),
    }

    completeUrl = baseUrl + requestpath

    data_json = json.dumps(data, separators=(',', ':'))  # use separators param for deleting spaces
    payload = base64.b64encode(data_json.encode('ascii'))
    signature = hmac.new(secret_key.encode('ascii'), payload, hashlib.sha512).hexdigest()

    headers = {
        'Content-type': 'application/json',
        'X-TXC-APIKEY': api_key,
        'X-TXC-PAYLOAD': payload,
        'X-TXC-SIGNATURE': signature,
    }

    resp = requests.post(completeUrl, headers=headers, data=data_json)

    response = resp.json()

    payment_url = response['url']

    session = Session()
    payment = whitebit.entities.WhitebitPayment(order_code=order.code, order_secret=order.secret_key,
                                                payment_link=payment_url, deposit_id=unique_id)
    order = session.query(orders.api.Order).get(order.id)
    order.payment_url = payment_url
    session.add(payment)
    session.commit()
    session.close()
    return response


def get_payment_by_order_code(order_code):
    with Session() as session:
        payment = session.query(whitebit.entities.WhitebitPayment).filter(whitebit.entities.WhitebitPayment.order_code == order_code).first()
    return payment


def get_payment_by_deposit_id(deposit_id):
    with Session() as session:
        payment = session.query(whitebit.entities.WhitebitPayment).filter(whitebit.entities.WhitebitPayment.deposit_id == deposit_id).first()
    return payment


def get_balance():
    api_key = public_key  # put here your public key
    secret_key = private_key  # put here your secret key
    requestpath = '/api/v4/main-account/balance'
    baseUrl = 'https://whitebit.com'
    nonce = str(int(time.time()))

    data = {
        'request': requestpath,
        'nonce': nonce
    }

    completeUrl = baseUrl + requestpath

    data_json = json.dumps(data, separators=(',', ':'))  # use separators param for deleting spaces
    payload = base64.b64encode(data_json.encode('ascii'))
    signature = hmac.new(secret_key.encode('ascii'), payload, hashlib.sha512).hexdigest()

    headers = {
        'Content-type': 'application/json',
        'X-TXC-APIKEY': api_key,
        'X-TXC-PAYLOAD': payload,
        'X-TXC-SIGNATURE': signature,
    }

    resp = requests.post(completeUrl, headers=headers, data=data_json)

    response = resp.json()
    print(response)


def create_wallet(tool):
    # return garantex_get_add_address(tool)
    api_key = public_key  # put here your public key
    secret_key = private_key  # put here your secret key
    requestpath = '/api/v4/main-account/create-new-address'  # put here request path. For obtaining trading balance use: /api/v4/trade-account/balance
    baseUrl = 'https://whitebit.com'  # domain without last slash. Do not use https://whitebit.com/
    # If the nonce is similar to or lower than the previous request number, you will receive the 'too many requests' error message
    nonce = str(int(time.time()))  # nonce is a number that is always higher than the previous request number

    # curl --location --request POST 'https://whitebit.com/api/v4/main-account/create-new-address' \
    # --data-raw '{
    #    "ticker": "ETH"
    # }'

    data = {
        'ticker': tool.name,
        'request': requestpath,
        'nonce': nonce
    }

    if tool.network is not None:
        data['network'] = tool.network

    # preparing request URL
    completeUrl = baseUrl + requestpath

    data_json = json.dumps(data, separators=(',', ':'))  # use separators param for deleting spaces
    payload = base64.b64encode(data_json.encode('ascii'))
    signature = hmac.new(secret_key.encode('ascii'), payload, hashlib.sha512).hexdigest()

    # preparing headers
    headers = {
        'Content-type': 'application/json',
        'X-TXC-APIKEY': api_key,
        'X-TXC-PAYLOAD': payload,
        'X-TXC-SIGNATURE': signature,
    }

    print(data_json)

    # sending request
    resp = requests.post(completeUrl, headers=headers, data=data_json)

    # receiving data
    # response = json.dumps(resp.json(), sort_keys=True, indent=4)
    response = resp.json()
    print(response)
    exchange_wallet = response['account']['address']
    return exchange_wallet, response['account'].get('memo')


def get_cost(tool_from, tool_to):
    #return garantex.get_cost(tool_from, tool_to)
    # cost = costs.get('{}_{}'.format(tool_from, tool_to))
    # if cost is None:
    #     return None
    # else:
    #     return float(cost)
    fiat = ['USD', 'RUB', 'EUR']
    if tool_to in fiat and tool_from in fiat:
        print(tool_from, tool_to)
        return 1

    t_to = tool_to
    if tool_to == 'EUR':
        t_to = 'RUB'
    cost = costs.get('{}_{}'.format(tool_from, t_to))

    if tool_to == 'EUR' and cost is not None:
        global euro
        cost = float(cost) / euro
    if cost is None:
        return 0
    else:
        return float(cost)


def check_tool(name):
    url = v4_public_url + 'assets'

    response = requests.get(url)

    tools_dict = response.json()

    if tools_dict.get(str(name).upper()) is None:
        return False
    return True


def get_tool(name):
    url = v4_public_url + 'assets'

    response = requests.get(url)

    tools_dict = response.json()

    if tools_dict.get(str(name).upper()) is None:
        return None
    else:
        return tools_dict.get(str(name).upper())


def get_networks(name):
    tool = get_tool(name)
    if tool is None:
        return []
    networks_list = tool.get('networks')
    if networks_list is None:
        return []
    networks = []
    for n in tool['networks']['deposits']:
        networks.append(n)
    return networks


def get_euro():
    data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    return data['Valute']['EUR']['Value']


def update_costs():
    try:
        global euro
        euro = get_euro()
        print('euro = {}'.format(euro))
    except:
        print(traceback.format_exc())

    try:
        url = v4_public_url + 'ticker'

        response = requests.get(url)

        tools_dict = response.json()

        global costs
        costs.clear()

        for tool in tools_dict:
            qtools = str(tool).split('_')
            if qtools[1] == 'USD' and tools_dict[tool]['isFrozen']:
                costs[tool] = tools_dict['{}_USDT'.format(qtools[0])]['last_price']
            else:
                costs[tool] = tools_dict[tool]['last_price']
    except Exception as e:
        print(traceback.format_exc())
        notify.send_message('Ошибка обновления цен:\n\n{}'.format(e.args))
    finally:
        Timer(30, update_costs).start()


update_costs()