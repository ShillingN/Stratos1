from db import Session
from .entities import AdminLog


def create_log(request, user):
    params = {}
    if request.method == 'GET':
        for param_name in request.values:
            params[param_name] = request.values.get(param_name)
    else:
        params = request.json
        if params is None:
            params = {}
            for param_name in request.values:
                params[param_name] = request.values.get(param_name)

    headers = {}
    for header_row in request.headers:
        headers[header_row[0]] = header_row[1]

    log = AdminLog(method=request.method, url=request.path, params=params, headers=headers, email=user.email, level=user.admin)
    session = Session()
    session.add(log)
    session.commit()