"""
Config For Database (Redis) Access.

Provide Host, Port and database number information here.
"""
DATABASE_HOST = '127.0.0.1'
DATABASE_PORT = 6379
DATABASE = 0

GNUPGHOME = '/var/local/gnupghome'

# Require emails of new users to be verified before they get proper access to nova
REQUIRE_VERIFY_EMAIL = True

EMAIL_SMTP_HOST = 'localhost'

VERIFY_EMAIL_SUBJECT = 'SWUP-APP Verification Code'
VERIFY_EMAIL_ADDRESS = 'verification@swup-app.com'
VERIFY_EMAIL_TEXT = 'Welcome to SWUP-APP\n\nTo activate your account, please navigate to the following address in your web browser.\n{verification_link}\n\nWe can\'t wait to have you on board!'
VERIFY_EMAIL_HTML = """\
<html>
    <head></head>
    <body>
        <h1>Welcome to SWUP-APP</h1>
        <p>To activate your account, please click on the following link or copy and paste it into your web browser.</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        <p>We can't wait to have you on board!</p>
    </body>
</html>
"""
