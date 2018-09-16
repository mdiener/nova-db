class Routes(object):
    def __init__(self, app, views):
        app.add_url_rule('/db/<path:path>', 'dbaccess', views.dbaccess, methods=['GET', 'POST', 'DELETE'])
