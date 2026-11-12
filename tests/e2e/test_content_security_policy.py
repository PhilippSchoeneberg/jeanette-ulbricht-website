"""The pages work under the Content Security Policy (src/backend/security.py): using them triggers
no CSP violations, which Chromium reports as console errors."""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def csp_violations(page: Page):
    violations = []
    page.on(
        "console",
        lambda message: violations.append(message.text) if "Content Security Policy" in message.text else None,
    )
    return violations


PAGES = ["/index.html", "/biography.html", "/contact.html", "/impressum.html", "/datenschutz.html"]


@pytest.mark.parametrize("path", PAGES)
def test_pages_load_without_csp_violations(page: Page, csp_violations, path):
    response = page.goto(path)

    assert "content-security-policy" in response.headers
    # The head script, deferred scripts and translations all ran.
    expect(page.locator("html")).to_have_class("js")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    page.locator("[data-theme-toggle]").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.locator("[data-language-toggle]").click()
    expect(page.locator("html")).to_have_attribute("lang", "en")
    assert csp_violations == []


def test_gallery_and_contact_form_work_without_csp_violations(page: Page, csp_violations, mailer, de):
    page.goto("/index.html")
    viewport = page.locator("[data-gallery-viewport]")
    viewport.scroll_into_view_if_needed()
    viewport.focus()
    viewport.press("End")
    expect(page.locator("[data-gallery-next]")).to_have_attribute("aria-disabled", "true")

    page.goto("/contact.html")
    form = page.locator("[data-contact-form]")
    form.locator("[name=name]").fill("Erika Mustermann")
    form.locator("[name=email]").fill("erika@example.com")
    form.locator("[name=message]").fill("Hallo, ich hätte gern ein Angebot.")
    form.locator("[type=submit]").click()
    expect(form.locator("[data-form-status]")).to_have_text(de["form_status_sent"])

    assert csp_violations == []
