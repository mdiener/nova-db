import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import nova.exceptions
from config.nova import VERIFY_EMAIL_ADDRESS, VERIFY_EMAIL_TEXT, VERIFY_EMAIL_HTML, VERIFY_EMAIL_SUBJECT, EMAIL_SMTP_HOST


class Email(object):
    def __init__(self, to, cc=None, bcc=None):
        self.container = MIMEMultipart('alternative')
        self.sender = VERIFY_EMAIL_ADDRESS
        self.to = self._make_list(to)
        self.cc = self._make_list(cc)
        self.bcc = self._make_list(bcc)

    def _make_list(self, address):
        if isinstance(address, str):
            return address.replace(' ', '').split(',')
        elif isinstance(address, list):
            return address
        else:
            return []

    def send_verification_email(self, verification_link):
        text = VERIFY_EMAIL_TEXT.format(verification_link=verification_link)
        html = VERIFY_EMAIL_HTML.format(verification_link=verification_link)

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        self.container.attach(part1)
        self.container.attach(part2)

        self.container['Subject'] = VERIFY_EMAIL_SUBJECT

        self._send()

    def _send(self):
        self.container['To'] = ','.join(self.to)
        if len(self.cc) > 0:
            self.container['Cc'] = ','.join(self.cc)

        rcpts = self.to + self.cc + self.bcc

        print('recipients', rcpts)
        print('emailtext', self.container.as_string())

        try:
            s = smtplib.SMTP(EMAIL_SMTP_HOST)
        except ConnectionRefusedError as e:
            raise nova.exceptions.EmailConnectionFailed('Could not connect to email host.')

        s.sendmail(self.sender, rcpts, self.container.as_string())
        s.quit()
