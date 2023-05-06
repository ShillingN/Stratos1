import utils
import json


class Setting:
    def __init__(self):
        try:
            app_path = utils.get_script_dir()
            data = {}
            with open('{}/settings.json'.format(app_path), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
            self.min_withdraw = data['min_withdraw']
            self.best_minutes = data['best_minutes']
            self.proxy = data['proxy']
            self.order_minutes = data['order_minutes']
            self.prices_timer = data['prices_timer']
            self.prices_delay = data['prices_delay']
            self.tech_stop = data['tech_stop']
            self.message = data['message']
            self.cash_text = data['cash_text']
            self.header_message = data['header_message']
            self.change_rests = data['change_rests']
            self.headers = data['headers']
            self.order_id = data['order_id']
            self.autocommit = data['autocommit']
        except:
            self.min_withdraw = 500
            self.best_minutes = 1
            self.proxy = ''
            self.prices_timer = False
            self.prices_delay = 30
            self.order_minutes = 30
            self.tech_stop = False
            self.message = ''
            self.cash_text = ''
            self.header_message = ''
            self.change_rests = False
            self.headers = ''
            self.order_id = 43200
            self.autocommit = ''


    def save(self):
        app_path = utils.get_script_dir()

        data = {
            'min_withdraw': self.min_withdraw,
            'best_minutes': self.best_minutes,
            'proxy': self.proxy,
            'order_minutes': self.order_minutes,
            'prices_timer': self.prices_timer,
            'prices_delay': self.prices_delay,
            'tech_stop': self.tech_stop,
            'message': self.message,
            'cash_text': self.cash_text,
            'header_message': self.header_message,
            'change_rests': self.change_rests,
            'headers': self.headers,
            'order_id': self.order_id,
            'autocommit': self.autocommit,
        }

        with open('{}/settings.json'.format(app_path), 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))