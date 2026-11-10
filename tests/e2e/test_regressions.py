"""Regression tests for frontend bugs found in the bug review."""

from playwright.sync_api import Browser, Page, expect

from tests.e2e.test_gallery import TRACK_POSITION, wait_until


def test_gallery_drag_ends_when_the_mouse_is_released_outside(page: Page):
    # Bug: press in the gallery, move less than the 5px drag threshold, release outside it.
    # The release was never seen, so afterwards plain hovering moved the gallery.
    page.goto("/index.html")
    viewport = page.locator("[data-gallery-viewport]")
    viewport.scroll_into_view_if_needed()
    box = viewport.bounding_box()
    x, y = box["x"] + 300, box["y"] + 100

    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - 3, y)
    page.mouse.move(x - 3, box["y"] - 200)  # outside the gallery
    page.mouse.up()

    before = page.evaluate(TRACK_POSITION)
    page.mouse.move(x, y)
    page.mouse.move(x - 200, y, steps=5)  # hover only, no button pressed
    assert page.evaluate(TRACK_POSITION) == before
    expect(viewport).not_to_have_class("gallery__viewport is-dragging")


def test_printing_shows_all_content(browser: Browser, base_url, browser_context_args):
    # Bug: blocks that fade in on scroll stayed invisible in print until scrolled into view.
    context = browser.new_context(**{**browser_context_args, "reduced_motion": "no-preference"})
    try:
        page = context.new_page()
        page.goto(f"{base_url}/index.html")
        page.emulate_media(media="print")
        hidden = page.evaluate(
            """() => [...document.querySelectorAll('.reveal')]
                .filter(element => getComputedStyle(element).opacity !== '1').length"""
        )
        assert hidden == 0
    finally:
        context.close()


def test_latest_language_choice_wins_over_a_slow_translation(page: Page, de):
    # Bug: on a slow connection, switching to German while the English translation was still
    # loading ended in English (the late English result overwrote the newer choice).
    page.add_init_script(
        """
        localStorage.setItem('language', 'en');
        const realFetch = window.fetch;
        window.fetch = (url, ...args) => String(url).includes('en.json')
            ? new Promise(resolve => setTimeout(() => resolve(realFetch(url, ...args)), 3000))
            : realFetch(url, ...args);
        """
    )
    page.goto("/index.html", wait_until="domcontentloaded")
    # The page is hidden while the translation loads, but shown after at most 1.5 s even if the
    # English file is still on its way: that's when a visitor can click the language button.
    expect(page.locator("html")).not_to_have_class("js i18n-loading", timeout=2500)
    page.locator("[data-language-toggle]").click()

    # Wait until the slow English file has certainly arrived, then check the result.
    page.wait_for_timeout(3000)
    expect(page.locator("html")).to_have_attribute("lang", "de")
    expect(page).to_have_title(de["title_home"])
    assert page.evaluate("localStorage.getItem('language')") == "de"


def test_language_toggle_follows_the_pending_choice(page: Page):
    # Clicking twice quickly must end where the button said: de -> en -> de.
    page.goto("/index.html")
    toggle = page.locator("[data-language-toggle]")
    toggle.click()
    toggle.click()
    wait_until(lambda: page.evaluate("localStorage.getItem('language')") == "de")
    expect(page.locator("html")).to_have_attribute("lang", "de")
