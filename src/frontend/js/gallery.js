// Draggable image track with parallax (the site's signature interaction).
// Works with mouse, touch and pen (Pointer Events), horizontal scrolling
// (trackpad, tilt wheel, Shift + wheel), the keyboard (arrow keys, Home/End)
// and the previous/next buttons. Respects prefers-reduced-motion.

(() => {
    const gallery = document.querySelector("[data-gallery]");
    if (!gallery) return;

    const viewport = gallery.querySelector("[data-gallery-viewport]");
    const track = gallery.querySelector("[data-gallery-track]");
    const images = [...track.querySelectorAll("img")];
    const prevButton = gallery.querySelector("[data-gallery-prev]");
    const nextButton = gallery.querySelector("[data-gallery-next]");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    const ANIMATION_DURATION = 1200;
    const DRAG_THRESHOLD = 5;   // px before a press counts as a drag
    const DRAG_SPEED = 1.5;     // track movement per px of pointer movement

    let position = 0;           // px the track is shifted to the left
    let drag = null;

    const maxPosition = () => Math.max(track.offsetWidth - viewport.clientWidth, 0);

    function stepSize() {
        const firstItem = track.firstElementChild;
        const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
        return firstItem ? firstItem.offsetWidth + gap : viewport.clientWidth;
    }

    function render({ animate = true } = {}) {
        const max = maxPosition();
        position = Math.min(Math.max(position, 0), max);

        const progress = max === 0 ? 0 : position / max;
        const options = {
            duration: animate && !reducedMotion.matches ? ANIMATION_DURATION : 0,
            fill: "forwards",
        };

        track.animate({ transform: `translateX(${-position}px)` }, options);

        const objectPosition = reducedMotion.matches ? "50% center" : `${100 - progress * 100}% center`;
        for (const image of images) {
            image.animate({ objectPosition }, options);
        }

        // aria-disabled instead of disabled: the button stays focusable at the ends, so keyboard
        // focus doesn't drop to the page (browsers differ for focused, disabled buttons).
        prevButton.setAttribute("aria-disabled", String(position <= 0));
        nextButton.setAttribute("aria-disabled", String(position >= max - 1));
    }

    const isDisabled = button => button.getAttribute("aria-disabled") === "true";

    function moveBy(delta) {
        position += delta;
        render();
    }

    // Pointer dragging
    viewport.addEventListener("pointerdown", event => {
        if (event.pointerType === "mouse" && event.button !== 0) return;
        drag = { id: event.pointerId, startX: event.clientX, startPosition: position, active: false };
    });

    viewport.addEventListener("pointermove", event => {
        if (!drag || event.pointerId !== drag.id) return;

        // A mouse released outside the gallery before the drag started (no pointer capture yet)
        // never sends pointerup here: end the drag as soon as no button is pressed anymore.
        if (event.pointerType === "mouse" && event.buttons === 0) {
            endDrag(event);
            return;
        }

        const deltaX = event.clientX - drag.startX;
        if (!drag.active) {
            if (Math.abs(deltaX) < DRAG_THRESHOLD) return;
            drag.active = true;
            viewport.setPointerCapture(event.pointerId);
            viewport.classList.add("is-dragging");
        }

        position = drag.startPosition - deltaX * DRAG_SPEED;
        render();
    });

    function endDrag(event) {
        if (!drag || event.pointerId !== drag.id) return;
        drag = null;
        viewport.classList.remove("is-dragging");
    }

    viewport.addEventListener("pointerup", endDrag);
    viewport.addEventListener("pointercancel", endDrag);

    // Horizontal scrolling: trackpad side-swipes, horizontal mouse wheels and
    // Shift + mouse wheel. Mostly vertical scrolling is left to the page.
    const LINE_HEIGHT = 16;
    viewport.addEventListener("wheel", event => {
        let delta = event.deltaX;
        if (event.shiftKey && delta === 0) delta = event.deltaY;
        if (delta === 0 || Math.abs(delta) < Math.abs(event.deltaY) && !event.shiftKey) return;

        // Also stops the browser's swipe-to-go-back gesture inside the gallery.
        event.preventDefault();
        if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) delta *= LINE_HEIGHT;
        else if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) delta *= viewport.clientWidth;
        moveBy(delta);
    }, { passive: false });

    // Keyboard
    viewport.addEventListener("keydown", event => {
        const actions = {
            ArrowRight: () => moveBy(stepSize()),
            ArrowLeft: () => moveBy(-stepSize()),
            Home: () => moveBy(-Infinity),
            End: () => moveBy(Infinity),
        };
        const action = actions[event.key];
        if (action) {
            event.preventDefault();
            action();
        }
    });

    // Buttons
    prevButton.addEventListener("click", () => {
        if (!isDisabled(prevButton)) moveBy(-stepSize());
    });
    nextButton.addEventListener("click", () => {
        if (!isDisabled(nextButton)) moveBy(stepSize());
    });

    window.addEventListener("resize", () => render({ animate: false }));
    reducedMotion.addEventListener("change", () => render({ animate: false }));

    render({ animate: false });
})();
