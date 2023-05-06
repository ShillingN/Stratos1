from threading import Timer
import base64
import time
import datetime
import random
import requests
import jwt
import traceback
import notify


costs = {}
euro = 0


def get_token():
    private_key = 'LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBNkNWcmUxVTcweUw3YStIeGhHNWExM2VkQ2pydm1yZ2huN0FLM3FVQk1aNzNsRTR3Ck91cjBaeWdEV0RnOEJrVGFoaEhFdjVKT0FqRHRsN2ZpQ3ppbGgycDk3YS9tbmwzMFYxVTUrYUxYSWlCYlJsSUwKWDlQcGVPVXBITXpSWjRLamJhMmgxejlWZUdsbVVzcjdGUjYwQ3VQczlndHpPT0syQVNHcFRaVnFITnphZGhCZgpNU3F0N25xbVR2bUVHRUhJUWVsWVE3dWtqRDhVNmNEYXhqMGNvRFp2N3lXVWZVV0M4aWoyS21BVkFYOXpvKytuCm1zd2pCQmx2VEhoclpsdXR2S3JOcWtCYXFxbURPTVBMSzdnMFJhSi9zZDVNYitpQm5KZGJJVm1QM3A2Y05tNUkKV2xjT3E1OGFRYU1zc1lVMjBBV2hiYmNKQ2p0VWViSWtna0tLblFJREFRQUJBb0lCQVFDdW44ZFVCTzkxaVRENwpIQURqRDJnQ0FKWCtwZ3FxcGF1VlJZVkhxWE5XY2kvbVBWS0dYMHJ0ZGVuZUtKN3VVRWpZNVBETThpNy84dkltCldFb1BDdE5wSTdBS1pYRGkyK1g2ODc4aWkxMnM3QTM4dmFhVXRRRkEwWkMxZTFSaHVxRlkxVzJTVHEvcVhjNTgKcFBkdUVhUjVOSzZBL21meitJWFVJQkFNcmtJZDVvemw0bDZRaHErRmlXUUIyOEtrWmJtblI5K254UGJ1Wi9UMwo5Vm1mZ05hZVFCWGo1Wlo4OEtlcEp1S2ZaNTdBYlFES0JsMEl5V0VUN3kybDE2eGFwOTdjRS90NDJZdEwzM09PCjgraVd1a0g1Sy93MHhJbE92Z1NuOWFWZmlrSThhNHlJbTV2ZFRKT1RkdlV4dTQ5dnYzNi84L3lrMFF1WXVjSEwKYnVtVm5LZ0JBb0dCQVB6WDlRSXRnVUhPSlA5TEUwbitXSytKOERGZUxQc0lraUZ6RjdpSXdTM1ViS21lN3ZWcAoraVlSRERYMy9JL0owK2hLRWR5YzdmNW1FQzRGWDNEVzk4ZTM5SWhyQ2NWdkgrclhESTBYenlFOWg3T0tYWFZ6Clg2TnI0Ni94RE1JTFJtZE9ZOGFRa0taNy9lQkdUbWxrNk1pSjBSYVhTVTNjUXJ0WDQ1WkVEMnVkQW9HQkFPc0wKVVV0bjI1Q1pvdHpwUUNKbVk4aXcwZU9CUjJ3VjVKU3BoMXg2dWhTMWdjZUorTHIxWXo4LzVweFZSZ0RKcE43TwpYbFVyUXhLM094YWJoRnRRQzhSWkRRUGllUlVqRGVIaFNaeTRiWUs1UkNMaDRoK1RvWW1SRktVQXdYTENXcjhKCmRqeVNoOVB3VGdCamlkbGZhamtmVzhRM0QxVVQ2cHNVRXJrTTh1c0JBb0dBTXVFeVNKSG5wTnBhejVUSCtPZloKNk5rVklKb1c2eDA2YXNqQ1NUd2J3NkV2aktLUzY0ZTc4dFVUWS9qWE5nZ2pRR2RIV09HcmNyb1BIM090VlFPdApNTjl2c2RQNFQyYWhRWnlzeGVlNG9yUEREdm9VL0lHUENVKzRyYnNRR2l3eXFxODNuTW1Ta2kzNVZKeFJReHd2ClM4dVA2Ny9kM0hFcWJKQ3ZGNW55a0hFQ2dZRUFva2R1R1dIYmRqcWM5MmtUbnF5U3VEMWNySGJWbVFxRWh4K0YKRlpTbVpTWHNOSmhONHNjSmZ1SGZscEJKaE1HejB5RW9nQ1VlYWcyWC9rUGhYaW9sOWFxR0VlaUxNTXpEQ1BGQwpvYkd6NmsxL2ZaWDNTVlhrY2RaNUtuTWJIT0NUUnRLQmo5Q2Jkdml5NGhIWFd2MUZtYXJNOE93UzZlcVdUL3ZMCjhYZS9RQUVDZ1lBblVpK1lXWkRhRjFpUnFMcjBDVDdzRHA2aVJHNlM0YjJsaG1idC9Ud0tac2xVZ3JQSVBpUEkKa0MwZjZ1NE1TdkRzM2ZSVXFOUUxoUTNtMEI5RitsUlBqOFROdjgyOE5MdThMV1ZMMU50QVVxUnRzaVhKTUdwbwpVNVY1MExYdHFDbkRyVG9teDc1VzFLQTFrVDhVY0pqTU9MKzRZYU1IRHYwN0xsUnN6ZnVYY3c9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo=='
    uid = '0fe4d519-678a-4276-9c44-1b47c4a639c4'
    host = 'garantex.io' # для тестового сервера используйте stage.garantex.biz

    key = base64.b64decode(private_key)
    iat = int(time.mktime(datetime.datetime.now().timetuple()))

    claims = {
        "exp": iat + 1*60*60,
        "jti": hex(random.getrandbits(12)).upper()
    }

    jwt_token = jwt.encode(claims, key, algorithm="RS256")

    ret = requests.post('https://dauth.' + host + '/api/v1/sessions/generate_jwt',
                        json={'kid': uid, 'jwt_token': jwt_token})

    token = ret.json().get('token')
    return token


def get_me():
    url = 'https://garantex.io/api/v2/members/me'
    headers = {
        'Authorization': 'Bearer {}'.format(get_token())
    }

    response = requests.get(url, headers=headers)
    print(response.text)


def get_accounts():
    url = 'https://garantex.io/api/v2/accounts'
    headers = {
        'Authorization': 'Bearer {}'.format(get_token())
    }

    response = requests.get(url, headers=headers)
    print(response.text)


def get_deposits():
    url = 'https://garantex.io/api/v2/deposits'
    headers = {
        'Authorization': 'Bearer {}'.format(get_token())
    }

    response = requests.get(url, headers=headers)
    print(response.text)


def get_address(tool):
    currency = str(tool.name).lower()
    if tool.network == 'TRC20':
        currency += '-tron'
    url = 'https://garantex.io/api/v2/deposit_address?currency={}'.format(currency)
    headers = {
        'Authorization': 'Bearer {}'.format(get_token())
    }
    print(url)

    response = requests.get(url, headers=headers)
    print(response.text)


def get_additional_address(tool):
    currency = str(tool.name).lower()
    if tool.network == 'TRC20':
        currency += '-tron'
    url = 'https://garantex.io/api/v2/deposit_address'.format()
    payload = {'currency': str(currency).lower()}
    headers = {
        'Authorization': 'Bearer {}'.format(get_token()),
    }

    print(payload)

    response = requests.post(url, headers=headers, data=payload)
    print(response.json())
    return response.json()['address'], None


def get_cost(tool_from, tool_to):
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
        url = 'https://garantex.io/api/v2/coingecko/tickers'

        response = requests.get(url)

        tools_dict = response.json()

        global costs
        costs.clear()

        for tool in tools_dict:
            costs[tool['ticker_id']] = tool['last_price']
    except Exception as e:
        print(traceback.format_exc())
        notify.send_message('Ошибка обновления цен:\n\n{}'.format(e.args))
    finally:
        Timer(30, update_costs).start()


update_costs()