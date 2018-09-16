"""Auth Web Module."""

from web.mod_auth import routes
from web.mod_auth import views


class Auth(object):
    def __init__(self, app):
        self._views = views.Views()
        self._routes = routes.Routes(app, self._views)
