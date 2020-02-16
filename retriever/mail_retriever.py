import email
import imaplib
import time

from util import config


class MailHandler:
    def __init__(self):
        mail_settings = config.read('mail')
        self.email_user = mail_settings['address']
        self.password = mail_settings['pass']
        self.imap_server = mail_settings['imap_server']
        self.imap_port = mail_settings['imap_port']
        self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)

    def read_daily_mails(self, mail_from):
        self.mail.login(self.email_user, self.password)
        self.mail.select('inbox')
        mail_type, data = self.mail.search(None, f'(ON {time.strftime("%d-%b-%Y")} FROM {mail_from})')
        mail_ids = data[0]
        return mail_ids.split()

    def get_mail_info(self, mail_id):
        typ, data = self.mail.fetch(mail_id, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1].decode('utf-8'))
                email_subject = msg['subject']
                email_from = msg['from']
                email_date = msg['date']
                while msg.is_multipart():
                    msg = msg.get_payload(0)
                email_content = msg.get_payload(decode=False)
                info = {
                    'subject': email_subject,
                    'from': email_from,
                    'date': email_date,
                    'content': email_content
                }
                return info

    def get_mail_attachments(self, mail_id):
        typ, data = self.mail.fetch(mail_id, '(RFC822)')
        raw_email = data[0][1]
        # converts byte literal to string removing b''
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        attachments = []
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if bool(filename):
                attachments.append({
                    'filename': filename,
                    'content': part.get_payload(decode=True)
                })
        return attachments
