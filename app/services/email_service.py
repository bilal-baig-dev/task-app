from app.inntegrations.mailgun import MailgunClient


class EmailService:

    @staticmethod
    async def send_password_reset_email(
        *,
        email: str,
        reset_link: str,
    ) -> None:

        subject = "Reset your password"

        text = f"""
    A request was received to reset your password.

    Reset your password:

    {reset_link}

    This link expires in 15 minutes.

    If you didn't request this, you can safely ignore this email.
    """

        html = f"""
    <h2>Password Reset</h2>

    <p>A request was received to reset your password.</p>

    <p>
    <a href="{reset_link}">
    Reset Password
    </a>
    </p>

    <p>This link expires in <b>15 minutes</b>.</p>

    <p>If you didn't request this you can safely ignore this email.</p>
    """

        await MailgunClient.send_email(
            to=email,
            subject=subject,
            text=text,
            html=html,
        )
