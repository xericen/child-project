import smtplib
from email.mime.text import MIMEText

class Mailer:
    def send(self, to, title, html):
        config = wiz.config("season")
        msg = MIMEText(html, 'html', _charset='utf8')
        msg['Subject'] = title
        msg['From'] = config.smtp_sender
        msg['To'] = to

        server = smtplib.SMTP(config.smtp_host, int(config.smtp_port))
        server.ehlo()
        server.starttls()
        server.login(config.smtp_sender, config.smtp_password)
        server.sendmail(config.smtp_sender, to, msg.as_string())
        server.quit()

Model = Mailer()
