"""Run Nova and the Web API."""

import sys
from config.web import HOST, PORT, DEBUG
from web import app

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
