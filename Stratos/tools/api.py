from db import Session
from .entities import Tool
from errors import *
import whitebit


def get_tools_by_order(order, tools_list=None):
    tool_from = get_tool_by_name(order.tool_from, order.tool_from_network, tools_list)
    tool_to = get_tool_by_name(order.tool_to, order.tool_to_network, tools_list)
    return tool_from, tool_to


def get_tools_by_pair(pair, tools_list=None):
    tool_from = get_tool_by_id(pair.tool_from, tools_list)
    tool_to = get_tool_by_id(pair.tool_to, tools_list)
    return tool_from, tool_to


def get_tools():
    with Session() as db_session:
        tools = db_session.query(Tool).all()
    return tools


def get_tool_by_name(name, network, tools_list=None):

    if network is None and '^' in name:
        n_arr = str(name).split('^')
        name = n_arr[0]
        network = n_arr[1]
    if network is not None and len(network) == 0:
        network = None

    if tools_list is None:
        with Session() as db_session:
            tool = db_session.query(Tool).filter(Tool.name == name, Tool.network == network).first()
        return tool
    else:
        result = None
        for tool in tools_list:
            if tool.name == name and tool.network == network:
                result = tool
                break
        return result


def get_tool_by_nickname(nickname):
    with Session() as db_session:
        tool = db_session.query(Tool).filter(Tool.nickname == nickname).first()
    return tool


def get_tool_by_best_code(best_code):
    with Session() as db_session:
        tool = db_session.query(Tool).filter(Tool.best_code == str(best_code).lower()).first()
    return tool


def get_tool_by_xml_code(xml_code):
    with Session() as db_session:
        tool = db_session.query(Tool).filter(Tool.xml_code == str(xml_code)).first()
    return tool


def get_tool_by_id(tool_id, tools_list=None):
    if tools_list is not None:
        result = None
        for tool in tools_list:
            if tool.id == tool_id:
                result = tool
                break
        return result

    with Session() as db_session:
        tool = db_session.query(Tool).filter(Tool.id == tool_id).first()
        return tool


def create_tool(name, nickname, wallet, min_payment, max_payment, reserve, sort_from, sort_to, accept_count,
                placeholder_from, placeholder_to, is_cash, rounded_str, xml_code, network, cost_link=None):

    n_network = network if len(network) > 0 else None

    db_session = Session()
    check = db_session.query(Tool).filter(Tool.name == name, Tool.network == n_network).first()
    if check is not None:
        db_session.close()
        raise IncorrectDataValue('Инструмент с таким названием уже существует')

    check = db_session.query(Tool).filter(Tool.nickname == nickname).first()
    if check is not None:
        db_session.close()
        raise IncorrectDataValue('Инструмент с таким никнеймом уже существует')

    if min_payment < 0:
        db_session.close()
        raise IncorrectDataValue('Минимальный платеж не может быть < 0')
    if max_payment < 0:
        db_session.close()
        raise IncorrectDataValue('Максимальный платеж не может быть < 0')

    if max_payment <= min_payment:
        db_session.close()
        raise IncorrectDataValue('Максимальный платеж не может быть меньше или равен минимального платежа')

    if str(rounded_str) != '0':
        if str(rounded_str).startswith('0.0') is False:
            db_session.close()
            raise IncorrectDataValue('Строка округления должна начинаться на 0.0')

        check_round_str = True
        for symbol in rounded_str:
            if symbol not in ['0', '.']:
                check_round_str = False

        if check_round_str is False:
            db_session.close()
            raise IncorrectDataValue('Строка округления должна состоять только из 0 или .')

    check_tool = whitebit.api.check_tool(name)
    if check_tool is False:
        if cost_link is None:
            db_session.close()
            raise IncorrectDataValue('Должна быть установлена привязка к курсу RUB или USDT')
        if cost_link not in ['RUB', 'USDT', 'EUR']:
            db_session.close()
            raise IncorrectDataValue('Должна быть установлена привязка к курсу RUB или USDT')

    networks = whitebit.api.get_networks(name)
    if len(networks) > 0 and str(network).upper() not in networks:
        db_session.close()
        raise IncorrectDataValue('Для данного инструмента необходимо указать одну из доступных сетей')
    if len(networks) == 0:
        network = None

    tool = Tool(name=name, nickname=nickname, wallet=wallet, min_payment=min_payment, max_payment=max_payment, reserve=reserve,
                sort_from=sort_from, sort_to=sort_to, accept_count=accept_count, placeholder_from=placeholder_from, placeholder_to=placeholder_to,
                is_cash=is_cash, rounded_str=rounded_str, xml_code=xml_code, cost_link=cost_link, network=network)

    db_session.add(tool)
    db_session.commit()
    db_session.close()

    tool = get_tool_by_name(name, network)
    return tool
