"""Setup Flask Web APP."""

import flask

from web.mod_auth import auth
from web.mod_dbaccess import dbaccess
from web.utils import allowed_gai_family

import requests.packages.urllib3.util.connection as urllib3_cn

urllib3_cn.allowed_gai_family = allowed_gai_family

app = flask.Flask(__name__)

auth.Auth(app)
dbaccess.DBAccess(app)
