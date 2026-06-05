// Function to change the validity of an input field based on a boolean flag
function changeValidity(input, feedback, validity) {
    if (!input || !feedback) return;
    if (validity) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
        feedback.style.display = 'none';
    } else {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        feedback.style.display = 'block';
    }
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

function checkPasswordStrength() {
    const passwordInput = document.getElementById('id_new_password1');
    if (!passwordInput) return {strength: 'Weak', missing: [], length: []};
    
    const password = passwordInput.value;
    let strength = 'Weak';
    let missing = [];
    let lengthMsg = [];
    
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasDigit = /\d/.test(password);
    const hasSpecialChar = /[! @#£$%^&*()_+{}:;<>,.?~='/-]/.test(password);

    if (password.length >= 8 && password.length <= 32) {
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
    } else if (password.length > 0) {
        lengthMsg.push('between 8 and 32 characters');
    }

    updatePasswordMeter(strength);

    return {strength: strength, missing: missing, length: lengthMsg};
}

function validatePassword(silent = false) {
    const id = 'id_new_password1';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input || !feedback) return false;
    
    const result = checkPasswordStrength();
    const isNotEmpty = input.value.length > 0;
    const isVeryStrong = result.strength === 'Very Strong';

    if (!silent) {
        if (isVeryStrong) {
            changeValidity(input, feedback, true);
            feedback.textContent = '';
        } else {
            changeValidity(input, feedback, false);
            if (!isNotEmpty) {
                feedback.textContent = 'Cannot be empty!';
                updatePasswordMeter('Empty');
            } else if (input.value.length >= 8 && input.value.length <= 32) {
                feedback.textContent = 'Password is missing: ' + result.missing.join(', ');
            } else {
                feedback.textContent = 'Password must be ' + result.length.join(', ');
            }
        }
    }
    return isVeryStrong;
}

function validateConfirmPassword(silent = false) {
    const id = 'id_new_password2';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input || !feedback) return false;

    const p1Value = document.querySelector('#id_new_password1').value;
    const isNotEmpty = input.value.length > 0;
    const matches = p1Value === input.value;
    const isValid = isNotEmpty && matches;

    if (!silent) {
        if (isValid) {
            changeValidity(input, feedback, true);
            feedback.textContent = '';
        } else {
            changeValidity(input, feedback, false);
            if (!isNotEmpty) {
                feedback.textContent = 'Cannot be empty!';
            } else if (!matches) {
                feedback.textContent = 'Passwords must be the same!';
            }
        }
    }
    return isValid;
}

let submitted = false;

function validateForm(submit = false, silent = false) {
    const submitBtn = document.querySelector('button[type="submit"]');

    const p1Valid = validatePassword(silent);
    const p2Valid = validateConfirmPassword(silent);

    const isValid = p1Valid && p2Valid;

    if (submitBtn) {
        submitBtn.disabled = !isValid;

        if (isValid && submit && !submitted) {
            submitted = true;
            document.querySelector('form').submit();
        }
    }

    return isValid;
}

$(document).ready(function () {
    'use strict';

    const p1 = $('#id_new_password1');
    const p2 = $('#id_new_password2');

    function refreshFormState() {
        validateForm(false, true);
    }

    // Password 1 typing
    if (p1.length) {
        p1.on('input', function () {
            validatePassword(false);
            refreshFormState(); // 🔥 IMPORTANT
        });
    }

    // Password 2 typing
    if (p2.length) {
        p2.on('input', function () {
            validateConfirmPassword(false);
            refreshFormState(); // 🔥 IMPORTANT
        });
    }

    // blur (optional)
    if (p1.length) {
        p1.on('blur', function () {
            validatePassword(false);
            refreshFormState();
        });
    }

    if (p2.length) {
        p2.on('blur', function () {
            validateConfirmPassword(false);
            refreshFormState();
        });
    }

    // initial state
    refreshFormState();

    // submit handler
    $('form').on('submit', function (event) {
        if (!submitted) {
            event.preventDefault();
            validateForm(true, false);
        }
    });
});