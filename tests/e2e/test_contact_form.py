"""Contact form (js/contact-form.js) against the real backend with a fake mailer."""

import json

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def form(page: Page):
    page.goto("/contact.html")
    return page.locator("[data-contact-form]")


def fill_valid(form):
    form.locator("[name=name]").fill("Erika Mustermann")
    form.locator("[name=email]").fill("erika@example.com")
    form.locator("[name=subject]").fill("Anfrage")
    form.locator("[name=message]").fill("Hallo, ich hätte gern ein Angebot.")


def error_for(form, name):
    return form.locator(f"[data-error-for={name}]")


def test_empty_submit_shows_field_errors(page: Page, form, mailer, de):
    form.locator("[type=submit]").click()

    expect(error_for(form, "name")).to_have_text(de["form_error_name"])
    expect(error_for(form, "email")).to_have_text(de["form_error_email"])
    expect(error_for(form, "message")).to_have_text(de["form_error_message"])
    expect(error_for(form, "subject")).to_have_text("")
    expect(form.locator("[name=name]")).to_have_attribute("aria-invalid", "true")
    expect(form.locator("[name=name]")).to_be_focused()
    assert mailer.sent == []

    # An error disappears as soon as its field becomes valid.
    form.locator("[name=name]").fill("Erika Mustermann")
    expect(error_for(form, "name")).to_have_text("")
    expect(form.locator("[name=name]")).to_have_attribute("aria-invalid", "false")


def test_valid_submit_sends_message(page: Page, form, mailer, de):
    fill_valid(form)
    form.locator("[type=submit]").click()

    status = form.locator("[data-form-status]")
    expect(status).to_have_text(de["form_status_sent"])
    expect(status).to_have_class("form-status form-status--success")
    expect(form.locator("[name=name]")).to_have_value("")
    expect(form.locator("[type=submit]")).to_be_enabled()

    assert len(mailer.sent) == 1
    message = mailer.sent[0]
    assert message["Subject"] == "Kontaktformular: Anfrage"
    assert "erika@example.com" in message["Reply-To"]


def test_rate_limited_submit_shows_message(page: Page, form, mailer, de):
    page.route(
        "**/api/contact",
        lambda route: route.fulfill(
            status=429,
            content_type="application/json",
            body=json.dumps({"detail": "rate_limited"}),
        ),
    )
    fill_valid(form)
    form.locator("[type=submit]").click()

    status = form.locator("[data-form-status]")
    expect(status).to_have_text(de["form_status_rate_limited"])
    expect(status).to_have_class("form-status form-status--error")
    # The input is kept so the visitor can try again later.
    expect(form.locator("[name=name]")).to_have_value("Erika Mustermann")
    assert mailer.sent == []


def test_mail_error_shows_failure_message(page: Page, form, mailer, de):
    mailer.fail = True
    fill_valid(form)
    form.locator("[type=submit]").click()

    expect(form.locator("[data-form-status]")).to_have_text(de["form_status_failed"])


def test_status_follows_language_switch(page: Page, form, mailer, en):
    fill_valid(form)
    form.locator("[type=submit]").click()
    expect(form.locator("[data-form-status]")).to_have_class("form-status form-status--success")

    page.locator("[data-language-toggle]").click()
    expect(form.locator("[data-form-status]")).to_have_text(en["form_status_sent"])
