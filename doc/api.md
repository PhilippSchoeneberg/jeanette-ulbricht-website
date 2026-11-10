# API

The backend has one endpoint. Interactive docs are at `/api/docs` when the app runs with
`APP_ENV=development`; in production they are switched off.

## `POST /api/contact`

Sends a contact form message by e-mail to `CONTACT_RECIPIENT`.

Request body (JSON):

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | required, 1–100 characters, single line |
| `email` | string | required, valid e-mail address, max. 254 characters |
| `subject` | string | optional, max. 150 characters, single line |
| `message` | string | required, 10–5000 characters |
| `website` | string | honeypot, must be empty (hidden in the form) |

Leading and trailing whitespace is trimmed. Unknown fields are rejected.

Responses:

| Status | Body | Meaning |
| --- | --- | --- |
| 200 | `{"status": "sent"}` | Sent. Also returned when the honeypot is filled (nothing is sent). |
| 422 | FastAPI validation error, `detail[].loc` ends with the field name | Invalid input |
| 429 | `{"detail": "rate_limited"}` | More than 5 messages from this IP within 15 minutes |
| 413 | `{"detail": "request_too_large"}` | Request body over 64 KB (rejected before it is read) |
| 502 | `{"detail": "mail_error"}` | The mail server could not be reached or refused the message |

All responses, including the 429 and 502 error bodies, are declared as Pydantic models, so
`/api/docs` shows their exact shape. Every response carries the security headers described in
[Architecture](architecture.md#security).

The e-mail goes from `CONTACT_SENDER` to `CONTACT_RECIPIENT`, with the visitor's name and
address as `Reply-To`, so replying in the mail program answers the visitor directly.
