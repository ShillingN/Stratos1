from bs4 import BeautifulSoup
from errors import *
import requests
import re
import decimal


def get_cost(tool_from, tool_to, position):
    if position < 1:
        raise IncorrectDataValue('Позиция не может быть меньше 1')

    url = 'https://www.bestchange.ru/{}-to-{}.html'.format(tool_from.best_code, tool_to.best_code)
    print(url)

    site = requests.get(url).text
    soup = BeautifulSoup(site, 'lxml')

    rates_block = soup.find('div', {'id': 'rates_block'})
    t_body = rates_block.find('tbody')
    rows = t_body.find_all('tr', recursive=False)

    cnt = 0

    cost = None
    pattern = '[0-9.]{1,}'

    for tr in rows:
        if cnt == (position - 1):
            if len(tool_from.cost_link) > 0:
                fs = tr.find('div', {'class': 'fs'})
            else:
                fs_list = tr.find_all('td', {'class': 'bi'})
                fs = fs_list[-1]
            cost_str = str(fs.text).replace(' ', '')
            cost = float(re.findall(pattern, cost_str)[0])
            break
        cnt += 1
    return float(cost)