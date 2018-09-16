"""
Settings for Nova Web Access.

All settings in this file are used for accessing and configuring the web API used
by Nove.
"""


# The following three are only used when spinning up the built-in flask server
HOST = '0.0.0.0'
PORT = 8080
DEBUG = True

# Specify which authentication method you want to use.
# BE AWARE THAT SWITCHING AFTER YOU HAVE LAUNCHED YOUR APPLICATION IS NOT POSSIBLE. (without some significant modifications)
#
# "basic" is currently the only option. More might follow!
#
# basic
# Uses the basic auth method, however, passwords need to be submitted as SHA512 encrypted
# strings using a unique salt retrieved from the server for each user.
# This means a user's actual password should never leave the user's device.
# However, it also means that the hashed and salted password needs to be
# provided for every request (that is not public).
AUTH_METHOD = 'basic'

# Make sure to keep these secret!
OAUTH_CLIENTS = [
    ('swup-website', 'ab2eb858c08d45d388bdb7021a4a9d15'),
    ('swup-iphone', 'f15696643d4d4084888f084e42ebc049')
]

ACCESS_TOKEN_EXPIRY_TIME = 3600

REFRESH_TOKEN_EXPIRY_TIME = 86400
