let submitted = false;

// Function to change the validity of an input field based on a boolean flag
function changeValidity(input, feedback, validity) {
    if (!input) return;
    if (validity) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
        if (feedback) feedback.style.display = 'none';
    } else {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        if (feedback) feedback.style.display = 'block';
    }
}

// Function to validate if an input field is not empty
function validateNotEmpty(id) {
    const input = document.getElementById(id);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;
    if (input.value.trim().length === 0) {
        if (feedback) feedback.textContent = 'Cannot be empty!';
        return false;
    }
    return true;
}

// Login Form Validation
function validateUsername() {
    const id = "username-email";
    const input = document.getElementById(id);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    const valid = validateNotEmpty(id);
    changeValidity(input, feedback, valid);
    return valid;
}

function validatePassword() {
    const id = "password";
    const input = document.getElementById(id);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    const valid = validateNotEmpty(id);
    changeValidity(input, feedback, valid);
    return valid;
}

function validateAllLogin() {
    const u = validateUsername();
    const p = validatePassword();
    return u && p;
}

// Password Reset Modal Validation
function validateResetEmail(submit = false) {
    const id = 'resetEmail';
    const input = document.getElementById(id);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    const submitBtn = document.querySelector("#modalForm button[type='submit']");
    
    if (!input) return;

    if (!validateNotEmpty(id)) {
        changeValidity(input, feedback, false);
        if (feedback) feedback.textContent = 'Email cannot be empty!';
        if (submitBtn) submitBtn.disabled = true;
        return;
    }

    const emailPattern = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
    if (!emailPattern.test(input.value)) {
        changeValidity(input, feedback, false);
        if (feedback) feedback.textContent = 'Must be a valid email address!';
        if (submitBtn) submitBtn.disabled = true;
        return;
    }

    $.ajax({
        url: '/checkResetEmail/',
        type: 'GET',
        data: { resetEmail: input.value },
        success: function(data) {
            if (data.emailExists) {
                changeValidity(input, feedback, true);
                if (feedback) feedback.textContent = '';
                if (submitBtn) submitBtn.disabled = false;
                
                if (submit && !submitted) {
                    submitted = true;
                    document.getElementById("modalForm").submit();
                }
            } else {
                changeValidity(input, feedback, false);
                if (feedback) feedback.textContent = 'Email is not registered!';
                if (submitBtn) submitBtn.disabled = true;
            }
        },
        error: function() {
            if (feedback) {
                feedback.style.display = 'block';
                feedback.textContent = 'Server error. Please try again later.';
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // Login Form Initialization
    const loginForm = document.querySelector("form:not(#modalForm)");
    if (loginForm) {
        document.querySelectorAll("form:not(#modalForm) input.form-control").forEach(input => {
            input.addEventListener("input", () => {
                if (input.id === "username-email") validateUsername();
                if (input.id === "password") validatePassword();
            });
        });

        loginForm.addEventListener("submit", (event) => {
            const valid = validateAllLogin();
            if (!valid) {
                event.preventDefault();
                event.stopPropagation();
                return;
            }
            if (submitted) {
                event.preventDefault();
                return;
            }
            submitted = true;
        });
    }

    const resetInput = document.getElementById("resetEmail");
    if (resetInput) {
        resetInput.addEventListener("input", () => {
            validateResetEmail(false);
        });
    }

    const modalForm = document.getElementById("modalForm");
    if (modalForm) {
        modalForm.addEventListener("submit", (event) => {
            event.preventDefault();
            validateResetEmail(true);
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.getElementById("password");
    const toggleBtn = document.getElementById("pwToggle");
    const icon = document.getElementById("pwIcon");

    toggleBtn.addEventListener("click", function () {
        const isPassword = passwordInput.type === "password";

        // Toggle input type
        passwordInput.type = isPassword ? "text" : "password";

        // Toggle icon
        icon.classList.toggle("bi-eye");
        icon.classList.toggle("bi-eye-slash");
    });
});