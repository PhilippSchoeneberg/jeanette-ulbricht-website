"""Accessibility checks (WCAG 2.2 AA) for issues found in the a11y review.

Contrast is measured on the real computed colours in light and dark mode; focus handling and
ARIA state are checked by driving the page with the keyboard.
"""

import re

import pytest
from playwright.sync_api import Page, expect


def _luminance(rgb):
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _parse(color):
    """Parses rgb(...) / rgba(...) / #rrggbb as returned by getComputedStyle or custom properties."""
    color = color.strip()
    if color.startswith("#"):
        return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
    return tuple(int(float(v)) for v in re.findall(r"[\d.]+", color)[:3])


def contrast(a, b):
    high, low = sorted((_luminance(_parse(a)), _luminance(_parse(b))), reverse=True)
    return (high + 0.05) / (low + 0.05)


def css(page: Page, selector, prop):
    return page.eval_on_selector(selector, f"el => getComputedStyle(el).getPropertyValue('{prop}')")


def token(page: Page, name):
    return page.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('{name}')")


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_form_colours_have_enough_contrast(page: Page, scheme):
    page.emulate_media(color_scheme=scheme)
    page.goto("/contact.html")
    # The form sits in the grey (alt) section.
    section_bg = css(page, ".section--alt", "background-color")
    field = "#contact-name"

    # Field outline: 3:1 against the field and the section around it (WCAG 1.4.11).
    border = css(page, field, "border-top-color")
    assert contrast(border, css(page, field, "background-color")) >= 3
    assert contrast(border, section_bg) >= 3

    # Status and error texts: 4.5:1 (WCAG 1.4.3).
    assert contrast(token(page, "--color-success"), section_bg) >= 4.5
    assert contrast(token(page, "--color-error"), section_bg) >= 4.5


def test_inline_links_are_underlined(page: Page):
    # Links in running text must not rely on colour alone (WCAG 1.4.1).
    page.goto("/contact.html")
    assert "underline" in css(page, ".contact-form__privacy a", "text-decoration-line")


def test_form_fields_show_an_outline_on_focus(page: Page):
    # A real outline survives forced-colors / high-contrast mode, unlike a box-shadow.
    page.goto("/contact.html")
    page.locator("#contact-name").focus()
    assert css(page, "#contact-name", "outline-style") == "solid"
    assert css(page, "#contact-name", "outline-width") == "2px"


def force_focus_visible(page: Page, selector):
    """Puts an element into the :focus-visible state via the DevTools protocol (Chromium).

    Whether a browser treats focus as "visible" is a heuristic (keyboard vs. mouse, window focus)
    that differs between machines; forcing the state tests the CSS rule itself.
    """
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    node = cdp.send("DOM.querySelector", {"nodeId": root, "selector": selector})["nodeId"]
    cdp.send("CSS.forcePseudoState", {"nodeId": node, "forcedPseudoClasses": ["focus", "focus-visible"]})
    return cdp


def test_focus_ring_in_the_navigation_is_light(page: Page):
    page.goto("/index.html")
    force_focus_visible(page, ".global-nav__brand")
    assert css(page, ".global-nav__brand", "outline-style") == "solid"
    assert _parse(css(page, ".global-nav__brand", "outline-color")) == (255, 255, 255)

    # Outside the navigation the ring stays accent blue.
    force_focus_visible(page, ".tile--hero .button")
    assert _parse(css(page, ".tile--hero .button", "outline-color")) == _parse(token(page, "--color-accent"))


@pytest.mark.parametrize("motion", ["reduce", "no-preference"])
def test_open_mobile_menu_keeps_focus_inside(page: Page, motion):
    page.emulate_media(reduced_motion=motion)
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("/index.html")
    toggle = page.locator("[data-nav-toggle]")

    toggle.click()
    # Focus moves into the menu ...
    expect(page.locator("#nav-menu a").first).to_be_focused()
    # ... and the page behind it can't be reached.
    for selector in ("main", ".global-footer", ".skip-link"):
        assert page.eval_on_selector(selector, "el => el.inert"), selector
    # Tab cycles through the navigation (and out to the browser's own UI), never into the hidden
    # page behind the menu.
    for _ in range(8):
        page.keyboard.press("Tab")
        behind_menu = page.evaluate("document.activeElement.closest('main, .global-footer, .skip-link') !== null")
        assert not behind_menu, "focus moved to the page behind the open menu"

    page.keyboard.press("Escape")
    expect(toggle).to_be_focused()
    assert not page.eval_on_selector("main", "el => el.inert")


def test_gallery_buttons_stay_focusable_at_the_end(page: Page):
    page.goto("/index.html")
    next_button = page.locator("[data-gallery-next]")
    next_button.scroll_into_view_if_needed()
    next_button.focus()

    for _ in range(20):
        if next_button.get_attribute("aria-disabled") == "true":
            break
        page.keyboard.press("Enter")

    expect(next_button).to_have_attribute("aria-disabled", "true")
    expect(next_button).to_be_focused()
    expect(page.locator("[data-gallery-prev]")).to_have_attribute("aria-disabled", "false")


def test_language_toggle_name_starts_with_its_visible_text(page: Page, de, en):
    # WCAG 2.5.3 Label in Name: voice control users say what they see ("EN").
    page.goto("/index.html")
    toggle = page.locator("[data-language-toggle]")

    # Switching loads the translation asynchronously: wait for each state with expect() instead
    # of reading text and label at two different moments.
    for strings in (de, en):
        assert strings["language_switch_label"].startswith(strings["language_switch_code"])
        expect(toggle).to_have_text(strings["language_switch_code"])
        expect(toggle).to_have_attribute("aria-label", strings["language_switch_label"])
        toggle.click()


def test_unstyled_lists_keep_list_semantics(page: Page):
    # Safari/VoiceOver drops list semantics for lists styled without bullets unless role="list".
    for path in ("/index.html", "/biography.html", "/contact.html"):
        page.goto(path)
        missing = page.evaluate(
            """() => [...document.querySelectorAll("ul, ol")]
                .filter(list => getComputedStyle(list).listStyleType === "none")
                .filter(list => list.getAttribute("role") !== "list")
                .map(list => list.className || list.parentElement.className)"""
        )
        assert missing == [], f"{path}: {missing}"
