"""Utility Functions."""

import socket
import flask
import json


def allowed_gai_family():
    """
    Return allowed GAI family to disallow IPv6.

    Found at: https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    return socket.AF_INET


def build_response(data, status, headers):
    """Return JSON response with data, status and headers added."""
    response = flask.make_response(json.dumps(data), status)

    for key, value in headers:
        response.headers[key] = value

    return response
