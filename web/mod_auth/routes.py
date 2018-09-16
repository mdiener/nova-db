class Routes(object):
    def __init__(self, app, views):
        app.add_url_rule('/auth/login', 'auth.authenticate', views.authenticate, methods=['POST'])
        app.add_url_rule('/auth/salt', 'auth.salt', views.salt, methods=['GET'])
        app.add_url_rule('/auth/create', 'auth.create', views.create, methods=['POST'])
        app.add_url_rule('/auth/verify', 'auth.verify', views.verify, methods=['GET'])
        app.add_url_rule('/auth/user', 'auth.user_by_email', views.user_by_email, methods=['GET'])
        app.add_url_rule('/auth/user/<userid>', 'auth.user_by_id', views.user_by_id, methods=['GET'])
