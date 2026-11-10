// Shared behaviour for every page: mobile navigation and scroll reveal.

(() => {
    const nav = document.querySelector("[data-nav]");
    const toggle = nav?.querySelector("[data-nav-toggle]");
    const desktopQuery = window.matchMedia("(min-width: 834px)");

    function setMenuOpen(open) {
        nav.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
        document.body.classList.toggle("nav-open", open);
    }

    if (nav && toggle) {
        toggle.addEventListener("click", () => {
            setMenuOpen(!nav.classList.contains("is-open"));
        });

        document.addEventListener("keydown", event => {
            if (event.key === "Escape" && nav.classList.contains("is-open")) {
                setMenuOpen(false);
                toggle.focus();
            }
        });

        desktopQuery.addEventListener("change", () => setMenuOpen(false));
    }

    // Fade elements with the class "reveal" in when they scroll into view.
    const revealItems = document.querySelectorAll(".reveal");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reducedMotion || !("IntersectionObserver" in window)) {
        revealItems.forEach(item => item.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver(entries => {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        }
    }, { rootMargin: "0px 0px -10% 0px" });

    revealItems.forEach(item => observer.observe(item));
})();
