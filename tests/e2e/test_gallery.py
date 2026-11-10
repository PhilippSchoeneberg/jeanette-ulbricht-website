"""Portfolio gallery (js/gallery.js): dragging, keyboard and the previous/next buttons."""

import time

import pytest
from playwright.sync_api import Browser, Page, expect


# Current shift of the track in px (positive = moved to the left).
TRACK_POSITION = """() => {
    const track = document.querySelector("[data-gallery-track]");
    return -new DOMMatrix(getComputedStyle(track).transform).m41;
}"""

MAX_POSITION = """() => {
    const track = document.querySelector("[data-gallery-track]");
    const viewport = document.querySelector("[data-gallery-viewport]");
    return Math.max(track.offsetWidth - viewport.clientWidth, 0);
}"""


@pytest.fixture
def gallery(page: Page):
    page.goto("/index.html")
    viewport = page.locator("[data-gallery-viewport]")
    viewport.scroll_into_view_if_needed()
    assert page.evaluate(MAX_POSITION) > 0, "gallery must be wider than the viewport"
    return viewport


def position(page: Page):
    return page.evaluate(TRACK_POSITION)


def test_gallery_starts_at_the_beginning(page: Page, gallery):
    assert position(page) == 0
    expect(page.locator("[data-gallery-prev]")).to_be_disabled()
    expect(page.locator("[data-gallery-next]")).to_be_enabled()


def test_drag_moves_the_track(page: Page, gallery):
    box = gallery.bounding_box()
    y = box["y"] + box["height"] / 2
    start_x = box["x"] + box["width"] * 0.75

    page.mouse.move(start_x, y)
    page.mouse.down()
    page.mouse.move(start_x - 100, y, steps=10)
    page.mouse.up()

    # Dragging 100px to the left moves the track 1.5 × 100px (DRAG_SPEED).
    assert position(page) == pytest.approx(150, abs=2)
    expect(page.locator("[data-gallery-prev]")).to_be_enabled()

    # Dragging back to the right returns to the start (clamped at 0).
    page.mouse.move(start_x - 100, y)
    page.mouse.down()
    page.mouse.move(start_x + 200, y, steps=10)
    page.mouse.up()
    assert position(page) == 0


def test_small_pointer_movement_is_not_a_drag(page: Page, gallery):
    box = gallery.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - 3, y)
    page.mouse.up()
    assert position(page) == 0


def test_keyboard_navigation(page: Page, gallery):
    step = page.evaluate("""() => {
        const track = document.querySelector("[data-gallery-track]");
        return track.firstElementChild.offsetWidth + (parseFloat(getComputedStyle(track).columnGap) || 0);
    }""")
    maximum = page.evaluate(MAX_POSITION)

    gallery.focus()
    gallery.press("ArrowRight")
    assert position(page) == pytest.approx(min(step, maximum), abs=1)

    gallery.press("ArrowLeft")
    assert position(page) == 0

    gallery.press("End")
    assert position(page) == pytest.approx(maximum, abs=1)
    expect(page.locator("[data-gallery-next]")).to_be_disabled()

    gallery.press("Home")
    assert position(page) == 0
    expect(page.locator("[data-gallery-prev]")).to_be_disabled()


def test_buttons_move_and_disable_at_the_ends(page: Page, gallery):
    prev_button = page.locator("[data-gallery-prev]")
    next_button = page.locator("[data-gallery-next]")

    next_button.click()
    assert position(page) > 0
    expect(prev_button).to_be_enabled()

    # Click "next" until the end is reached (bounded, in case it never disables).
    for _ in range(20):
        if next_button.is_disabled():
            break
        next_button.click()
    expect(next_button).to_be_disabled()
    assert position(page) == pytest.approx(page.evaluate(MAX_POSITION), abs=1)

    for _ in range(20):
        if prev_button.is_disabled():
            break
        prev_button.click()
    expect(prev_button).to_be_disabled()
    assert position(page) == 0


def test_parallax_moves_images_with_the_track(browser: Browser, base_url, browser_context_args):
    # The other tests run with reduced motion (no parallax); this one needs the animation.
    context = browser.new_context(**{**browser_context_args, "reduced_motion": "no-preference"})
    try:
        page = context.new_page()
        page.goto(f"{base_url}/index.html")
        viewport = page.locator("[data-gallery-viewport]")
        viewport.scroll_into_view_if_needed()

        object_position = "getComputedStyle(document.querySelector('[data-gallery-track] img')).objectPosition"
        assert page.evaluate(object_position).startswith("100%")

        viewport.focus()
        viewport.press("End")
        # The animation takes 1200ms; wait until the images reach the other side.
        wait_until(lambda: page.evaluate(object_position).startswith("0%"))
        wait_until(lambda: abs(page.evaluate(TRACK_POSITION) - page.evaluate(MAX_POSITION)) < 1)
    finally:
        context.close()


def wait_until(condition, timeout=5.0, interval=0.05):
    """Polls `condition` from Python.

    Not page.wait_for_function: it evaluates its expression with eval() inside the page, which
    the site's Content Security Policy (no 'unsafe-eval') rightly blocks.
    """
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise AssertionError(f"condition not met within {timeout:.1f}s")
        time.sleep(interval)
