// Contact form: client-side validation and sending to the backend
// (POST /api/contact, see doc/api.md).

(() => {
    const form = document.querySelector("[data-contact-form]");
    if (!form) return;

    const submitButton = form.querySelector("[type=submit]");
    const statusOutput = form.querySelector("[data-form-status]");
    const submitLabel = submitButton.textContent;

    const FIELD_MESSAGES = {
        name: "Bitte geben Sie Ihren Namen an.",
        email: "Bitte geben Sie eine gültige E-Mail-Adresse an.",
        subject: "Der Betreff darf höchstens 150 Zeichen lang sein.",
        message: "Bitte schreiben Sie eine Nachricht mit mindestens 10 Zeichen.",
    };
    const STATUS_MESSAGES = {
        sent: "Vielen Dank! Ihre Nachricht wurde gesendet.",
        invalid: "Bitte prüfen Sie die markierten Felder.",
        rateLimited: "Sie haben gerade mehrere Nachrichten gesendet. Bitte versuchen Sie es später erneut.",
        failed: "Die Nachricht konnte leider nicht gesendet werden. Bitte versuchen Sie es später erneut oder schreiben Sie eine E-Mail.",
    };

    function setFieldError(name, message) {
        const field = form.elements[name];
        const errorOutput = form.querySelector(`[data-error-for="${name}"]`);
        if (!field || !errorOutput) return;
        field.setAttribute("aria-invalid", message ? "true" : "false");
        errorOutput.textContent = message || "";
    }

    function setStatus(type, message) {
        statusOutput.className = "form-status" + (type ? ` form-status--${type}` : "");
        statusOutput.textContent = message || "";
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
        for (const name of Object.keys(FIELD_MESSAGES)) {
            const field = form.elements[name];
            const valid = fieldIsValid(field);
            setFieldError(name, valid ? "" : FIELD_MESSAGES[name]);
            if (!valid && !firstInvalid) firstInvalid = field;
        }
        firstInvalid?.focus();
        return !firstInvalid;
    }

    // Clear a field's error as soon as it becomes valid.
    form.addEventListener("input", event => {
        const name = event.target.name;
        if (name in FIELD_MESSAGES && event.target.getAttribute("aria-invalid") === "true" && fieldIsValid(event.target)) {
            setFieldError(name, "");
        }
    });

    function setSending(sending) {
        submitButton.disabled = sending;
        submitButton.textContent = sending ? submitButton.dataset.labelSending : submitLabel;
    }

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
                setStatus("success", STATUS_MESSAGES.sent);
            } else if (response.status === 422) {
                // Map server-side validation errors to the fields.
                const body = await response.json().catch(() => ({}));
                for (const error of Array.isArray(body.detail) ? body.detail : []) {
                    const name = error.loc?.[error.loc.length - 1];
                    if (name in FIELD_MESSAGES) setFieldError(name, FIELD_MESSAGES[name]);
                }
                setStatus("error", STATUS_MESSAGES.invalid);
            } else if (response.status === 429) {
                setStatus("error", STATUS_MESSAGES.rateLimited);
            } else {
                setStatus("error", STATUS_MESSAGES.failed);
            }
        } catch {
            setStatus("error", STATUS_MESSAGES.failed);
        } finally {
            setSending(false);
        }
    });
})();
