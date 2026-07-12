import httpx
from app.core.config import settings


class MailgunClient:

    BASE_URL = (
        f"https://api.mailgun.net/v3/"
        f"{settings.MAILGUN_DOMAIN}"
    )

    @classmethod
    async def send_email(
        cls,
        *,
        to: str,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> None:

        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{cls.BASE_URL}/messages",
                auth=(
                    "api",
                    settings.MAILGUN_API_KEY,
                ),
                data={
                    "from": settings.MAIL_FROM,
                    "to": to,
                    "subject": subject,
                    "text": text,
                    "html": html,
                },
                timeout=20,
            )

        response.raise_for_status()
