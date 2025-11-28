import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail_gmail(to_email, subject, plain_text, html_text=None):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # Email gửi đi
    SMTP_USER = "nxk02032004@gmail.com"

    # App Password 16 ký tự từ Google (không phải mật khẩu Gmail)
    SMTP_PASS = "tpnw zvbi yggw scwa"

    # Tạo nội dung mail
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    # Nội dung dạng text
    part1 = MIMEText(plain_text, "plain")
    msg.attach(part1)

    # Nếu có HTML
    if html_text:
        part2 = MIMEText(html_text, "html")
        msg.attach(part2)

    # Gửi mail qua SMTP của Gmail
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    server.starttls()      # bật TLS
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, to_email, msg.as_string())
    server.quit()
