from web.mod_dbaccess import routes
from web.mod_dbaccess import views


class DBAccess(object):
    def __init__(self, app):
        self._views = views.Views()
        self._routes = routes.Routes(app, self._views)
