"""Theme toggle (js/main.js) and language switch (js/i18n.js)."""

from playwright.sync_api import Page, expect


def test_theme_toggle_switches_and_persists(page: Page):
    page.goto("/index.html")
    root = page.locator("html")
    toggle = page.locator("[data-theme-toggle]")
    expect(root).to_have_attribute("data-theme", "light")

    toggle.click()
    expect(root).to_have_attribute("data-theme", "dark")
    assert page.evaluate("localStorage.getItem('theme')") == "dark"

    page.reload()
    expect(root).to_have_attribute("data-theme", "dark")

    # The saved choice applies to other pages too.
    page.goto("/biography.html")
    expect(root).to_have_attribute("data-theme", "dark")

    page.locator("[data-theme-toggle]").click()
    expect(root).to_have_attribute("data-theme", "light")
    page.reload()
    expect(root).to_have_attribute("data-theme", "light")


def test_language_switch_translates_and_persists(page: Page, de, en):
    page.goto("/index.html")
    root = page.locator("html")
    toggle = page.locator("[data-language-toggle]")
    biography_link = page.locator(".global-nav__menu a[href='biography.html']")

    expect(root).to_have_attribute("lang", "de")
    expect(page).to_have_title(de["title_home"])
    expect(biography_link).to_have_text(de["nav_biography"])

    toggle.click()
    expect(root).to_have_attribute("lang", "en")
    expect(page).to_have_title(en["title_home"])
    expect(biography_link).to_have_text(en["nav_biography"])
    expect(toggle).to_have_text(en["language_switch_code"])

    # The choice is saved and applies on the next page.
    page.goto("/contact.html")
    expect(root).to_have_attribute("lang", "en")
    expect(page).to_have_title(en["title_contact"])

    page.locator("[data-language-toggle]").click()
    expect(root).to_have_attribute("lang", "de")
    expect(page).to_have_title(de["title_contact"])

    page.reload()
    expect(root).to_have_attribute("lang", "de")
    expect(page).to_have_title(de["title_contact"])


def test_mobile_nav_opens_and_closes(page: Page, de):
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("/index.html")
    nav = page.locator("[data-nav]")
    toggle = page.locator("[data-nav-toggle]")
    contact_link = page.locator(".global-nav__menu a[href='contact.html']")

    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(contact_link).to_be_hidden()

    toggle.click()
    expect(nav).to_have_class("global-nav is-open")
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(toggle).to_have_attribute("aria-label", de["menu_close"])
    expect(contact_link).to_be_visible()

    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(contact_link).to_be_hidden()

    # Escape closes the menu and moves focus back to the toggle.
    toggle.click()
    expect(contact_link).to_be_visible()
    page.keyboard.press("Escape")
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(contact_link).to_be_hidden()
    expect(toggle).to_be_focused()

    # A link in the open menu navigates.
    toggle.click()
    contact_link.click()
    expect(page).to_have_url(f"{page.url.rsplit('/', 1)[0]}/contact.html")
