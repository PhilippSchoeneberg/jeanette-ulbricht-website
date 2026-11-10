import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Unicode categories that must not appear in e-mail headers: control characters (including CR, LF
# and NEL U+0085) and line/paragraph separators (U+2028, U+2029). The e-mail library treats all of
# them as line breaks.
FORBIDDEN_IN_HEADERS = {"Cc", "Zl", "Zp"}


class ContactRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=254)
    subject: str = Field(default="", max_length=150)
    message: str = Field(min_length=10, max_length=5000)
    # Honeypot: hidden from people, often filled in by spam bots. Must stay empty.
    website: str = Field(default="", max_length=500)

    @field_validator("name", "subject")
    @classmethod
    def single_line(cls, value: str) -> str:
        # These end up in e-mail headers: no line breaks or other control characters.
        if any(unicodedata.category(char) in FORBIDDEN_IN_HEADERS for char in value):
            raise ValueError("must be a single line without control characters")
        return value

    @field_validator("email")
    @classmethod
    def ascii_local_part(cls, value: str) -> str:
        # The visitor's address becomes the Reply-To header. Addresses with non-ASCII characters
        # before the @ need SMTPUTF8, which the e-mail can't be built for; international domains
        # (after the @) are fine.
        if not value.rpartition("@")[0].isascii():
            raise ValueError("the part before the @ must only contain ASCII characters")
        return value


class ContactResponse(BaseModel):
    status: Literal["sent"]


class ErrorResponse(BaseModel):
    """Body of the 429 and 502 responses (validation errors use FastAPI's default 422 body)."""

    detail: Literal["rate_limited", "mail_error"]
