from threading import Timer
from db import Session
from .entities import Pair
from errors import *
import whitebit
import tools
import decimal
import utils
import traceback
import settings
import notify
from .bestchange import get_cost


def auto_update():
    session = Session()
    pairs = session.query(Pair).filter(Pair.best_position > 0).all()
    try:
        for pair in pairs:
            tool_from, tool_to = tools.api.get_tools_by_pair(pair)
            if len(tool_from.cost_link) > 0 and len(tool_to.cost_link) > 0:
                cost = 1
            else:
                cost = get_cost(tool_from, tool_to, pair.best_position)
            percent = 100 + float(pair.best_percent)
            new_cost = cost * percent / 100

            cost = pair.get_stock_cost()
            new_fee = (new_cost * 100 / cost) - 100
            new_fee = round(new_fee, 2)
            pair.fee = new_fee
            if len(tool_from.cost_link) > 0:
                pair.fee = -new_fee
            #print('{}_{} = {}%'.format(tool_from.name, tool_to.name, new_fee))
        session.commit()
    except:
        print(traceback.format_exc())
        notify.send_message('Ошибка автоматического обновления цены\n\n{}'.format(
            traceback.format_exc()
        ))
    finally:
        session.close()
        setting = settings.Setting()
        Timer(60 * setting.best_minutes, auto_update).start()


def get_pair_by_tools(t_from, t_to):
    with Session() as db_session:
        pair = db_session.query(Pair).filter(Pair.tool_from == t_from, Pair.tool_to == t_to).first()
    return pair


def get_pair_by_id(pair_id):
    with Session() as db_session:
        pair = db_session.query(Pair).get(pair_id)
    return pair


def get_pairs(costs=False):
    with Session() as db_session:
        pairs = db_session.query(Pair).all()

        tools_list = tools.api.get_tools()

        for pair in pairs:
            pair.t_from = tools.api.get_tool_by_id(pair.tool_from, tools_list)
            pair.t_to = tools.api.get_tool_by_id(pair.tool_to, tools_list)

            pair.stock_cost = decimal.Decimal(pair.t_from.rounded_str)
            pair.cost = decimal.Decimal(pair.t_from.rounded_str)

            if costs is False:
                continue

            fee = -pair.fee

            if len(pair.t_from.cost_link) > 0:
                cost_link = pair.t_from.cost_link
                t_from = pair.t_to.name
                fee = -pair.fee
            else:
                cost_link = pair.t_to.cost_link
                t_from = pair.t_from.name
                fee = pair.fee

            if len(pair.t_from.cost_link) > 0 and len(pair.t_to.cost_link) > 0:
                cost = 1
                fee = pair.fee

                print('111111111111111 {} {}'.format(pair.stock_cost, fee))
            else:
                cost = whitebit.api.get_cost(t_from, cost_link)
            if cost is None or cost == 0:
                #print(t_from)
                cost_btc = whitebit.api.get_cost(t_from, 'USDT')
                if cost_btc is None or cost_btc == 0:
                    pair.status = False
                cost = cost_btc * whitebit.api.get_cost('USDT', cost_link)
            pair.stock_cost = decimal.Decimal(cost)
            pair.cost = pair.stock_cost + ((pair.stock_cost * fee) / 100)

        return pairs


def create_pair(tool_from, tool_to, fee):
    check = get_pair_by_tools(tool_from, tool_to)
    if check is not None:
        raise IncorrectDataValue('Такая пара уже существует')

    t_from = tools.api.get_tool_by_id(tool_from)
    t_to = tools.api.get_tool_by_id(tool_to)

    if t_from.is_cash:
        raise IncorrectDataValue('Пользователь не может отдавать Наличные')

    # if len(t_from.cost_link) == 0 and len(t_to.cost_link) == 0:
    #     raise IncorrectDataValue('В обмене должны присутствовать как крипта, так и фиат')
    # if len(t_from.cost_link) != 0 and len(t_to.cost_link) != 0:
    #     raise IncorrectDataValue('В обмене должны присутствовать как крипта, так и фиат')

    if fee < -100:
        raise IncorrectDataValue('Комиссия не может быть меньше 100%')
    if fee > 100:
        raise IncorrectDataValue('Комиссия не может быть больше 100%')

    with Session() as db_session:
        pair = Pair(tool_from=tool_from, tool_to=tool_to, fee=fee)
        db_session.add(pair)
        db_session.commit()

    pair = get_pair_by_tools(tool_from, tool_to)
    return pair


def remove_pair(tool_from, tool_to):

    pair = get_pair_by_tools(tool_from, tool_to)
    if pair is  None:
        raise IncorrectDataValue('Такая пара не существует')

    with Session() as db_session:
        db_session.delete(pair)
        db_session.commit()
    return True


def remove_pair_by_id(pair_id):

    pair = get_pair_by_id(pair_id)
    if pair is None:
        raise IncorrectDataValue('Такая пара не существует')

    with Session() as db_session:
        db_session.delete(pair)
        db_session.commit()
    return True


def generate_export_xml():
    try:
        print('123')
        pairs = get_pairs(True)
        content = '<rates>'

        for pair in pairs:
            if pair.t_from.showed is False:
                continue
            if pair.t_to.showed is False:
                continue
            if pair.status is False:
                continue

            if len(pair.t_from.cost_link) > 0:
                pair.rounded_str = pair.t_to.rounded_str

                if pair.min_payment == 0:
                    min_payment = pair.t_from.min_payment
                else:
                    min_payment = pair.min_payment

                if pair.max_payment == 0:
                    max_payment = pair.t_from.max_payment
                else:
                    max_payment = pair.max_payment

                pair.min_from = min_payment
                pair.max_from = max_payment

                pair.min_from_local = decimal.Decimal(1 / pair.cost * min_payment).quantize(
                    decimal.Decimal(pair.rounded_str)
                )
            else:
                pair.rounded_str = pair.t_from.rounded_str

                if pair.min_payment == 0:
                    min_payment = pair.t_from.min_payment
                else:
                    min_payment = pair.min_payment

                if pair.max_payment == 0:
                    max_payment = pair.t_from.max_payment
                else:
                    max_payment = pair.max_payment

                pair.min_from_local = min_payment
                pair.min_from = decimal.Decimal(1 / pair.cost * min_payment).quantize(
                    decimal.Decimal(pair.rounded_str)
                )
                pair.max_from = decimal.Decimal(1 / pair.cost * max_payment).quantize(
                    decimal.Decimal(pair.rounded_str)
                )

            city_name = pair.t_to.best_city if len(pair.t_to.best_city) > 0 else pair.t_from.best_city
            if pair.city is not None:
                city_name = pair.city
            city_row = '\n<city>{}</city>'.format(city_name)
            if len(pair.t_from.cost_link) == 0 or (len(pair.t_from.cost_link) != 0 and len(pair.t_to.cost_link) != 0):
                content += f"""\n<item>\n<from>{pair.t_from.xml_code}</from>
        <to>{pair.t_to.xml_code}</to>
        <in>1</in>
        <out>{decimal.Decimal(pair.cost)}</out>
        <minamount>{pair.min_from} {pair.t_from.xml_code}</minamount>
        <amount>{pair.t_to.reserve}</amount>
        <maxamount>{pair.max_from} {pair.t_from.xml_code}</maxamount>
        <param>manual</param>{'' if pair.t_to.is_cash is False and pair.t_from.is_cash is False else city_row}\n</item>"""
            else:
                content += f"""\n<item>\n<from>{pair.t_from.xml_code}</from>
        <to>{pair.t_to.xml_code}</to>
        <in>{decimal.Decimal(pair.cost)}</in>
        <out>1</out>
        <minamount>{pair.min_from} {pair.t_from.cost_link}</minamount>
        <amount>{pair.t_to.reserve}</amount>
        <maxamount>{pair.max_from} {pair.t_from.cost_link}</maxamount>
        <param>manual</param>{'' if pair.t_to.is_cash is False and pair.t_from.is_cash is False else city_row}\n</item>"""


        content += '\n</rates>'

        with open('{}/static/export.xml'.format(utils.get_script_dir()), 'w') as f:
            f.write(content)
    except:
        print(traceback.format_exc())
    finally:
        setting = settings.Setting()
        Timer(setting.prices_delay, generate_export_xml).start()