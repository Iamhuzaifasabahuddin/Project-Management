/**
 * HEXZ CONNECT - Registration Validation
 * Refactored to support silent background validation and strict button control.
 */

// Helper to check if an email is valid (simplified version of global engine)
const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

// Function to change the validity of an input field based on a boolean flag
function changeValidity(input, feedback, validity, message = '') {
    if (!input || !feedback) return;
    if (validity) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
        feedback.style.display = 'none';
        feedback.textContent = '';
    } else {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        feedback.textContent = message;
        feedback.style.display = 'block';
    }
}

// Validation Primitives
function checkNotEmpty(val) { return val.trim().length > 0; }
function checkNoSpaces(val) { return !val.includes(' '); }
function checkLength(val, min, max) { return val.length >= min && val.length <= max; }
function checkAlphabetic(val) { return /^[a-zA-Z]+$/.test(val); }

/*
Modular Validation Functions
Supports 'silent' mode for background button state checks.
*/

function validateFirstname(silent = false) {
    const id = 'id_first_name';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;

    const val = input.value;
    let valid = true;
    let msg = '';

    if (!checkNotEmpty(val)) { valid = false; msg = 'Cannot be empty!'; }
    else if (!checkNoSpaces(val)) { valid = false; msg = 'Cannot contain spaces!'; }
    else if (!checkLength(val, 2, 30)) { valid = false; msg = 'Must be 2-30 characters long!'; }
    else if (!checkAlphabetic(val)) { valid = false; msg = 'Must contain letters only!'; }

    if (!silent) changeValidity(input, feedback, valid, msg);
    return valid;
}

function validateLastname(silent = false) {
    const id = 'id_last_name';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;

    const val = input.value;
    let valid = true;
    let msg = '';

    if (!checkNotEmpty(val)) { valid = false; msg = 'Cannot be empty!'; }
    else if (!checkNoSpaces(val)) { valid = false; msg = 'Cannot contain spaces!'; }
    else if (!checkLength(val, 2, 30)) { valid = false; msg = 'Must be 2-30 characters long!'; }
    else if (!checkAlphabetic(val)) { valid = false; msg = 'Must contain letters only!'; }

    if (!silent) changeValidity(input, feedback, valid, msg);
    return valid;
}

function updatePasswordMeter(strength) {
    const meterSections = document.querySelectorAll('.meter-section');
    if (meterSections.length === 0) return;

    meterSections.forEach(section => section.classList.remove('active', 'weak', 'medium', 'strong', 'very-strong'));
    switch (strength) {
        case 'Weak':
            meterSections[0].classList.add('active', 'weak');
            break;
        case 'Medium':
            meterSections[0].classList.add('active', 'weak');
            meterSections[1].classList.add('active', 'medium');
            break;
        case 'Strong':
            meterSections[0].classList.add('active', 'weak');
            meterSections[1].classList.add('active', 'medium');
            meterSections[2].classList.add('active', 'strong');
            break;
        case 'Very Strong':
            meterSections[0].classList.add('active', 'weak');
            meterSections[1].classList.add('active', 'medium');
            meterSections[2].classList.add('active', 'strong');
            meterSections[3].classList.add('active', 'very-strong');
            break;
    }
}

function checkPasswordStrength(val) {
    let strength = 'Weak';
    let missing = [];
    let lengthMsg = [];

    const hasUpperCase = /[A-Z]/.test(val);
    const hasLowerCase = /[a-z]/.test(val);
    const hasDigit = /\d/.test(val);
    const hasSpecialChar = /[!@#£$%^&*()_+{}:;<>,.?~='/-]/.test(val);

    if (val.length >= 8 && val.length <= 32) {
        if (hasUpperCase && hasLowerCase && hasDigit && hasSpecialChar) {
            strength = 'Very Strong';
        } else if (hasUpperCase && hasLowerCase && (hasDigit || hasSpecialChar)) {
            strength = 'Strong';
            if(!hasDigit) missing.push('a digit');
            if(!hasSpecialChar) missing.push('a special character');
        } else {
            strength = 'Medium';
            if (!hasUpperCase) missing.push('an uppercase letter');
            if (!hasLowerCase) missing.push('a lowercase letter');
            if (!hasDigit) missing.push('a digit');
            if (!hasSpecialChar) missing.push('a special character');
        }
    } else if (val.length > 0) {
        lengthMsg.push('between 8 and 32 characters');
    }

    return {strength: strength, missing: missing, length: lengthMsg};
}

function validatePassword(silent = false) {
    const id = 'id_password1';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;

    const val = input.value;
    const result = checkPasswordStrength(val);

    if (!silent) updatePasswordMeter(result.strength);

    let valid = false;
    let msg = '';

    if (!checkNotEmpty(val)) {
        msg = 'Cannot be empty!';
    } else if (result.strength === 'Very Strong') {
        valid = true;
    } else if (val.length >= 8 && val.length <= 32) {
        msg = 'Password is missing: ' + result.missing.join(', ');
    } else {
        msg = 'Password must be between 8 and 32 characters';
    }

    if (!silent) changeValidity(input, feedback, valid, msg);
    return valid;
}

function validateConfirmPassword(silent = false) {
    const id = 'id_password2';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    const p1 = document.querySelector('#id_password1');
    if (!input || !p1) return false;

    const val = input.value;
    let valid = true;
    let msg = '';

    if (!checkNotEmpty(val)) {
        valid = false;
        msg = 'Cannot be empty!';
    } else if (p1.value !== val) {
        valid = false;
        msg = 'Passwords must be the same!';
    }

    if (!silent) changeValidity(input, feedback, valid, msg);
    return valid;
}

/*
Asynchronous Validations (Username & Email)
These are handled via AJAX and update the button state.
*/

let usernameState = { valid: false, checking: false, value: '' };
let emailState = { valid: false, checking: false, value: '' };

function checkUsername(silent = false) {
    const id = 'id_username';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return;

    const val = input.value.trim();
    if (!val) {
        usernameState = { valid: false, checking: false, value: '' };
        if (!silent) changeValidity(input, feedback, false, 'Cannot be empty!');
        updateSubmitBtnState();
        return;
    }

    if (!checkNoSpaces(val) || !checkLength(val, 4, 20)) {
        usernameState = { valid: false, checking: false, value: val };
        if (!silent) changeValidity(input, feedback, false, 'Must be 4-20 characters with no spaces.');
        updateSubmitBtnState();
        return;
    }

    if (val === usernameState.value && !usernameState.checking) {
        if (!silent) changeValidity(input, feedback, usernameState.valid, usernameState.valid ? '' : 'Username already taken.');
        return;
    }

    usernameState.checking = true;
    usernameState.value = val;

    $.ajax({
        url: '/checkUsername/',
        type: 'GET',
        data: {username: val},
        success: function (data) {
            usernameState.checking = false;
            usernameState.valid = !data.usernameExists;
            if (!silent) {
                changeValidity(input, feedback, usernameState.valid, usernameState.valid ? '' : 'Username is already taken!');
            }
            updateSubmitBtnState();
        }
    });
}

function checkEmail(silent = false) {
    const id = 'id_email';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return;

    const val = input.value.trim();
    if (!val) {
        emailState = { valid: false, checking: false, value: '' };
        if (!silent) changeValidity(input, feedback, false, 'Cannot be empty!');
        updateSubmitBtnState();
        return;
    }

    if (!isValidEmail(val)) {
        emailState = { valid: false, checking: false, value: val };
        if (!silent) changeValidity(input, feedback, false, 'Please enter a valid email.');
        updateSubmitBtnState();
        return;
    }
    if (!val.endsWith('@topsoftdigitals.pk')) {
    emailState = { valid: false, checking: false, value: val };
    if (!silent) changeValidity(input, feedback, false, 'Invalid domain entered - only @topsoftdigitals.pk allowed!');
    updateSubmitBtnState();
    return;
}

    if (val === emailState.value && !emailState.checking) {
        if (!silent) changeValidity(input, feedback, emailState.valid, emailState.valid ? '' : 'Email already registered.');
        return;
    }

    emailState.checking = true;
    emailState.value = val;

    $.ajax({
        url: '/checkEmail/',
        type: 'GET',
        data: {email: val},
        success: function (data) {
            emailState.checking = false;
            emailState.valid = !data.emailExists;
            if (!silent) {
                changeValidity(input, feedback, emailState.valid, emailState.valid ? '' : 'Email is already registered!');
            }
            updateSubmitBtnState();
        }
    });
}

function updateSubmitBtnState() {
    const fn = validateFirstname(true);
    const ln = validateLastname(true);
    const p1 = validatePassword(true);
    const p2 = validateConfirmPassword(true);

    const isAllValid = fn && ln && p1 && p2 && usernameState.valid && emailState.valid;
    const submitBtn = document.querySelector('button[type="submit"]');

    if (submitBtn) {
        submitBtn.disabled = !isAllValid;
    }
}

let submitted = false;

$(document).ready(function() {
    'use strict'

    const inputs = document.querySelectorAll('input.form-control');

    inputs.forEach(input => {
    input.addEventListener('input', () => {
        // Update async checks silently
        if (input.id === 'id_username') checkUsername(false);
        else if (input.id === 'id_email') checkEmail(false);

        // Show live feedback if field already marked invalid
        if (input.classList.contains('is-invalid')) {
            if (input.id === 'id_first_name') validateFirstname();
            else if (input.id === 'id_last_name') validateLastname();
            else if (input.id === 'id_username') checkUsername();
            else if (input.id === 'id_email') checkEmail();
            else if (input.id === 'id_password1') validatePassword();
            else if (input.id === 'id_password2') validateConfirmPassword();
        } else {
            // Still run visual update for password meter etc.
            if (input.id === 'id_password1') validatePassword();
            else if (input.id === 'id_password2') validateConfirmPassword();
        }

        // Always update button state on every keystroke
        updateSubmitBtnState();
    });

        input.addEventListener('blur', () => {
            // Show full validation feedback on blur
            if (input.id === 'id_first_name') validateFirstname();
            else if (input.id === 'id_last_name') validateLastname();
            else if (input.id === 'id_username') checkUsername();
            else if (input.id === 'id_email') checkEmail();
            else if (input.id === 'id_password1') validatePassword();
            else if (input.id === 'id_password2') validateConfirmPassword();
        });
    });

    updateSubmitBtnState();

    $('form').on('submit', function(event) {
        if (submitted) {
            event.preventDefault();
            return;
        }

        // Final sanity check
        const fn = validateFirstname();
        const ln = validateLastname();
        const p1 = validatePassword();
        const p2 = validateConfirmPassword();
        checkUsername();
        checkEmail();

        if (fn && ln && p1 && p2 && usernameState.valid && emailState.valid) {
            submitted = true;
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    <span>Creating Account...</span>
                `;
            }
        } else {
            event.preventDefault();
            event.stopPropagation();
        }
    });
});
