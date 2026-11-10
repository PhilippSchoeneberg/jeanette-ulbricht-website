from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
        # These end up in e-mail headers; control characters (line breaks) are not allowed.
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("must be a single line without control characters")
        return value


class ContactResponse(BaseModel):
    status: str
