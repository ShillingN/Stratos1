from .entities import File
from db import Session


def get_file(uuid, files_list=None):
    if files_list is None:
        with Session() as db_session:
            file = db_session.query(File).filter(File.uuid == uuid).first()
        return file
    else:
        result = None
        for file in files_list:
            if file.uuid == uuid:
                result = file
                break
        return result


def get_files():
    with Session() as db_session:
        files = db_session.query(File).all()
    return files