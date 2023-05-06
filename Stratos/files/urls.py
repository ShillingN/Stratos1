from flask import blueprints, session, request, abort, redirect, render_template, send_file
from PIL import Image
import notify
from errors import *
from db import Session
from .entities import File
from uuid import uuid4
import utils
import base64
import traceback
import os

app = blueprints.Blueprint('Files API', __name__, url_prefix='/files/api')


@app.route('/upload', methods=['POST'])
def loadImage():
    try:
        data = request.json
        notify.send_me('Загрузка фото')
        file = data['file']
        filename = data['filename']
        base = file[str(file).find('64,') + 3:]

        notify.send_me('filename = {}'.format(filename))
        notify.send_me('file = {}'.format(file[:64]))

        file_array = str(filename).split('.')
        extension = file_array[-1]
        name = str(filename).replace(extension, '')
        name = name[:-1]

        new_name = str(uuid4())
        bq = base64.decodebytes(bytes(base, encoding='utf-8'))

        path_name = '{}/storage/{}.{}'.format(utils.get_script_dir(), new_name, extension)

        with open(path_name, 'wb') as f:
            f.write(bq)

        try:
            v_image = Image.open(path_name)
            result = v_image.verify()
        except:
            os.remove(path_name)
            notify.send_message('Попытка загрузить файл.\nФайл не является валидным изображением и был удалён с сервера')
            return utils.get_error('Загружено не изображение')

        with Session() as db_session:
            file = File(filename=name, uuid=new_name, extension=extension)
            db_session.add(file)
            db_session.commit()
    except:
        notify.send_me(traceback.format_exc())
        print(traceback.format_exc())
        return utils.get_error('error')

    return utils.get_answer('Файл успешно сохранен', {'uuid': new_name})


@app.route('/get')
def get():
    uuid = request.values.get('uuid', '', str)
    try:
        with Session() as db_session:
            file = db_session.query(File).filter(File.uuid == uuid).first()
            if file is None:
                return utils.get_error('Файл не найден')

            path_name = '{}/storage/{}.{}'.format(utils.get_script_dir(), file.uuid, file.extension)

        return send_file(path_name, as_attachment=True)
    except:
        return redirect('https://StratosChange.ru/files/get?uuid={}'.format(uuid))