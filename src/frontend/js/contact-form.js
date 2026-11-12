// Contact form: client-side validation and sending to the backend
// (POST /api/contact, see doc/api.md). Texts come from js/i18n.js (locales/*.json).

(() => {
    const form = document.querySelector("[data-contact-form]");
    if (!form) return;

    const submitButton = form.querySelector("[type=submit]");
    const statusOutput = form.querySelector("[data-form-status]");

    // Translation keys of the error message per field.
    const FIELD_ERRORS = {
        name: "form_error_name",
        email: "form_error_email",
        subject: "form_error_subject",
        message: "form_error_message",
    };

    const t = key => window.i18n?.t(key) ?? key;

    // Remember what is shown as keys, so it can be re-rendered when the language changes.
    const shownFieldErrors = {};
    let shownStatus = { type: "", key: "" };
    let sending = false;

    function setFieldError(name, key) {
        const field = form.elements[name];
        const errorOutput = form.querySelector(`[data-error-for="${name}"]`);
        if (!field || !errorOutput) return;
        shownFieldErrors[name] = key || "";
        field.setAttribute("aria-invalid", key ? "true" : "false");
        errorOutput.textContent = key ? t(key) : "";
    }

    function setStatus(type, key) {
        shownStatus = { type, key };
        statusOutput.className = "form-status" + (type ? ` form-status--${type}` : "");
        statusOutput.textContent = key ? t(key) : "";
    }

    function fieldIsValid(field) {
        // minlength is only checked by browsers after user edits, so check it explicitly.
        const tooShort = field.minLength > 0 && field.value.trim().length < field.minLength;
        const blank = field.required && field.value.trim() === "";
        return field.checkValidity() && !tooShort && !blank;
    }

    // Returns true if all fields are valid; otherwise marks them and focuses the first one.
    function validate() {
        let firstInvalid = null;
        for (const [name, key] of Object.entries(FIELD_ERRORS)) {
            const field = form.elements[name];
            const valid = fieldIsValid(field);
            setFieldError(name, valid ? "" : key);
            if (!valid && !firstInvalid) firstInvalid = field;
        }
        firstInvalid?.focus();
        return !firstInvalid;
    }

    // Clear a field's error as soon as it becomes valid.
    form.addEventListener("input", event => {
        const name = event.target.name;
        if (name in FIELD_ERRORS && shownFieldErrors[name] && fieldIsValid(event.target)) {
            setFieldError(name, "");
        }
    });

    function setSending(value) {
        sending = value;
        submitButton.disabled = value;
        submitButton.textContent = t(value ? "form_sending" : "form_submit");
    }

    // Re-render visible messages in the new language.
    document.addEventListener("languagechange", () => {
        for (const [name, key] of Object.entries(shownFieldErrors)) setFieldError(name, key);
        setStatus(shownStatus.type, shownStatus.key);
        if (sending) submitButton.textContent = t("form_sending");
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();
        setStatus("", "");
        if (!validate()) return;

        const data = Object.fromEntries(new FormData(form));
        setSending(true);
        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                form.reset();
                setStatus("success", "form_status_sent");
            } else if (response.status === 422) {
                // Map server-side validation errors to the fields.
                const body = await response.json().catch(() => ({}));
                for (const error of Array.isArray(body.detail) ? body.detail : []) {
                    const name = error.loc?.[error.loc.length - 1];
                    if (name in FIELD_ERRORS) setFieldError(name, FIELD_ERRORS[name]);
                }
                setStatus("error", "form_status_invalid");
            } else if (response.status === 429) {
                setStatus("error", "form_status_rate_limited");
            } else {
                setStatus("error", "form_status_failed");
            }
        } catch {
            setStatus("error", "form_status_failed");
        } finally {
            setSending(false);
        }
    });
})();
