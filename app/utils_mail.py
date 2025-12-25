import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail_gmail(to_email, subject, plain_text, html_text=None):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    SMTP_USER = "nxk02032004@gmail.com"

    SMTP_PASS = "tpnw zvbi yggw scwa"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    part1 = MIMEText(plain_text, "plain")
    msg.attach(part1)

    if html_text:
        part2 = MIMEText(html_text, "html")
        msg.attach(part2)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, to_email, msg.as_string())
    server.quit()
