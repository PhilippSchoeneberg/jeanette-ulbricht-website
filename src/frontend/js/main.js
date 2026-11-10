// Shared behaviour for every page: colour theme toggle, mobile navigation and
// scroll reveal.

// Colour theme. The inline script in each page's <head> sets the initial
// data-theme (saved choice, otherwise the system preference) before first paint.
(() => {
    const root = document.documentElement;
    const button = document.querySelector("[data-theme-toggle]");
    const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
    const STORAGE_KEY = "theme";

    function savedTheme() {
        try {
            const theme = localStorage.getItem(STORAGE_KEY);
            return theme === "light" || theme === "dark" ? theme : null;
        } catch {
            return null;
        }
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;
        button?.setAttribute("aria-label", theme === "dark" ? "Helles Design aktivieren" : "Dunkles Design aktivieren");
    }

    applyTheme(root.dataset.theme === "dark" ? "dark" : "light");

    button?.addEventListener("click", () => {
        const next = root.dataset.theme === "dark" ? "light" : "dark";
        applyTheme(next);
        try {
            localStorage.setItem(STORAGE_KEY, next);
        } catch {
            // Storage unavailable (e.g. blocked): the choice lasts for this page only.
        }
    });

    // Follow system changes as long as the visitor hasn't chosen a theme.
    systemDark.addEventListener("change", event => {
        if (!savedTheme()) applyTheme(event.matches ? "dark" : "light");
    });

    // Keep other open tabs of the site in sync.
    window.addEventListener("storage", event => {
        if (event.key === STORAGE_KEY && savedTheme()) applyTheme(savedTheme());
    });
})();

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
