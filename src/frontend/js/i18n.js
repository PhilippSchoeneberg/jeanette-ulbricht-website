// Language switching (German / English).
//
// German is written directly in the HTML (works without JavaScript, and is what search engines
// see). Translatable elements carry data attributes with keys from locales/<code>.json:
//   data-i18n="key"             replaces the element's text
//   data-i18n-<attr>="key"      replaces an attribute, e.g. data-i18n-alt, data-i18n-aria-label
// Other scripts use window.i18n.t(key) for texts they create, and listen for the
// "languagechange" event on document to update them.
//
// The inline script in each page's <head> picks the initial language (saved choice, otherwise
// the browser language) and hides the page while a non-German translation loads.

(() => {
    const SUPPORTED = ["de", "en"];
    const DEFAULT = "de";
    const STORAGE_KEY = "language";
    const TRANSLATED_ATTRIBUTES = ["alt", "aria-label", "aria-roledescription", "content", "lang"];

    const root = document.documentElement;
    const cache = {};
    let strings = {};
    let fallback = {};
    let language = SUPPORTED.includes(root.dataset.language) ? root.dataset.language : DEFAULT;

    async function loadLocale(code) {
        if (!cache[code]) {
            const response = await fetch(`locales/${code}.json`);
            if (!response.ok) throw new Error(`Missing locale ${code}`);
            cache[code] = await response.json();
        }
        return cache[code];
    }

    function t(key) {
        return strings[key] ?? fallback[key] ?? key;
    }

    function applyTranslations() {
        for (const element of document.querySelectorAll("[data-i18n]")) {
            element.textContent = t(element.dataset.i18n);
        }
        for (const attribute of TRANSLATED_ATTRIBUTES) {
            for (const element of document.querySelectorAll(`[data-i18n-${attribute}]`)) {
                element.setAttribute(attribute, t(element.getAttribute(`data-i18n-${attribute}`)));
            }
        }
        root.lang = language;
        root.dataset.language = language;
    }

    async function setLanguage(code, { save = false } = {}) {
        if (!SUPPORTED.includes(code)) code = DEFAULT;
        try {
            fallback = await loadLocale(DEFAULT);
            strings = await loadLocale(code);
            language = code;
            applyTranslations();
            if (save) {
                try {
                    localStorage.setItem(STORAGE_KEY, code);
                } catch {
                    // Storage unavailable: the choice lasts for this page only.
                }
            }
            document.dispatchEvent(new CustomEvent("languagechange", { detail: { language } }));
        } catch (error) {
            // Translations unavailable (e.g. page opened from the file system): stay in German.
            console.warn("Translations could not be loaded:", error);
        } finally {
            root.classList.remove("i18n-loading");
        }
    }

    const ready = setLanguage(language);

    window.i18n = {
        t,
        ready,
        setLanguage,
        get language() {
            return language;
        },
    };

    document.querySelector("[data-language-toggle]")?.addEventListener("click", () => {
        setLanguage(language === "de" ? "en" : "de", { save: true });
    });
})();
