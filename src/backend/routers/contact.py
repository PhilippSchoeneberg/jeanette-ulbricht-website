import logging
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from fastapi import APIRouter, HTTPException, Request, status

from ..mailer import MailError
from ..schemas import ContactRequest, ContactResponse, ErrorResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["contact"])


def build_message(form: ContactRequest, recipient: str, sender: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = f"Kontaktformular: {form.subject or 'Neue Nachricht'}"
    message["From"] = Address("Website Jeanette Ulbricht", addr_spec=sender)
    message["To"] = recipient
    message["Reply-To"] = Address(form.name, addr_spec=form.email)
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=sender.rpartition("@")[2] or None)
    message.set_content(
        "Neue Nachricht über das Kontaktformular der Website.\n\n"
        f"Name:    {form.name}\n"
        f"E-Mail:  {form.email}\n"
        f"Betreff: {form.subject or '–'}\n\n"
        f"{form.message}\n"
    )
    return message


# Plain `def`: FastAPI runs it in a thread pool, so the blocking SMTP call doesn't stall the server.
@router.post(
    "/contact",
    response_model=ContactResponse,
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Too many messages from this IP address (`rate_limited`)",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "The mail server could not be reached or refused the message (`mail_error`)",
        },
    },
)
def send_contact_message(form: ContactRequest, request: Request):
    if form.website:
        # Honeypot filled in: most likely a bot. Pretend success so it doesn't retry.
        logger.info("Contact form honeypot triggered; message dropped.")
        return ContactResponse(status="sent")

    client_ip = request.client.host if request.client else "unknown"
    if not request.app.state.rate_limiter.allow(client_ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limited")

    settings = request.app.state.settings
    message = build_message(form, settings.contact_recipient, settings.contact_sender)
    try:
        request.app.state.mailer.send(message)
    except MailError:
        # Already logged by the mailer; the client only needs the error code.
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="mail_error") from None

    return ContactResponse(status="sent")
