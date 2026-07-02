import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.core.config import RELAY_HOST, RELAY_USERNAME, RELAY_PASSWORD


class AsyncSMTPClient:
    def __init__(
            self,
            host: str,
            port: int = 587,
            username: str | None = None,
            password: str | None = None,
            use_tls: bool = False
            ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.client = aiosmtplib.SMTP(hostname=self.host, port=self.port)

    async def connect(self):
        await self.client.connect()

        if self.use_tls:
            await self.client.starttls()

        if self.username and self.password:
            await self.client.login(self.username, self.password)

    async def send_html(self, to: str, subject: str, html: str, from_addr: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to

        html_part = MIMEText(html, "html")
        msg.attach(html_part)

        await self.client.send_message(msg)

    async def close(self):
        await self.client.quit()

    def __del__(self):
        self.close()



smtp = AsyncSMTPClient(
    host=RELAY_HOST,
    port=587,
    use_tls=True,
    username=RELAY_USERNAME,
    password=RELAY_PASSWORD
)
smtp.connect()

# пример
# await smtp.send_html(
#     to="test@example.com",
#     subject="Код подтверждения",
#     html="<h1>Ваш код: <b>123456</b></h1>",
#     from_addr="noreply@example.com"
# )