// Runs before first paint (loaded without defer in each page's <head>): enables the JS styles,
// applies the saved or system colour theme and picks the language. A separate file instead of an
// inline script, so the Content Security Policy can forbid inline scripts (src/backend/security.py).
(function () {
    var root = document.documentElement, theme = null;
    root.classList.add("js");
    try { theme = localStorage.getItem("theme"); } catch (e) {}
    if (theme !== "light" && theme !== "dark") {
        theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    root.dataset.theme = theme;

    var language = null;
    try { language = localStorage.getItem("language"); } catch (e) {}
    if (language !== "de" && language !== "en") {
        language = "de";
        var preferred = navigator.languages || [navigator.language];
        for (var i = 0; i < preferred.length; i++) {
            var code = String(preferred[i] || "").slice(0, 2).toLowerCase();
            if (code === "de" || code === "en") { language = code; break; }
        }
    }
    root.dataset.language = language;
    if (language !== "de") {
        // Hide the German page until js/i18n.js has applied the translation.
        root.classList.add("i18n-loading");
        setTimeout(function () { root.classList.remove("i18n-loading"); }, 1500);
    }
})();
