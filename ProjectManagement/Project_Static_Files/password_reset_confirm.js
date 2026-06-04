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

// Function to validate if an input field is not empty
function validateNotEmpty(id) {
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input || !feedback) return false;
    if (input.value.length === 0) {
        feedback.textContent = 'Cannot be empty!';
        return false;
    }
    return true;
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
    const hasSpecialChar = /[!@#£$%^&*()_+{}:;<>,.?~='/-]/.test(password);

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

function validatePassword() {
    const id = 'id_new_password1';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input || !feedback) return false;
    
    changeValidity(input, feedback, false);

    if (validateNotEmpty(id)) {
        const result = checkPasswordStrength();
        if (result.strength === 'Very Strong') {
            changeValidity(input, feedback, true);
            feedback.textContent = '';
            return true;
        } else if (input.value.length > 0 && input.value.length >= 8 && input.value.length <= 32) {
            feedback.textContent = 'Password is missing: ' + result.missing.join(', ');
        } else if(input.value.length > 0) {
            feedback.textContent = 'Password must be ' + result.length.join(', ');
        }
    } else {
        updatePasswordMeter('Empty');
    }
    return false;
}

function validateConfirmPassword() {
    const id = 'id_new_password2';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input || !feedback) return false;

    changeValidity(input, feedback, false);
    if (validateNotEmpty(id)) {
        if (document.querySelector('#id_new_password1').value !== input.value) {
            feedback.textContent = 'Passwords must be the same!'
        } else {
            changeValidity(input, feedback, true);
            feedback.textContent = '';
            return true;
        }
    }
    return false;
}

let submitted = false;

function validateForm(submit = false) {
    const p1 = validatePassword();
    const p2 = validateConfirmPassword();
    
    const isValid = p1 && p2;
    const submitBtn = document.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        if (isValid) {
            submitBtn.disabled = false;
            if (submit && !submitted) {
                submitted = true;
                document.querySelector('form').submit();
            }
        } else {
            submitBtn.disabled = true;
        }
    }
    
    return isValid;
}

$(document).ready(function() {
    'use strict'
    
    const p1 = $('#id_new_password1');
    const p2 = $('#id_new_password2');
    
    if (p1.length) {
        p1.on('input', function() {
            validateForm(false);
        });
    }
    if (p2.length) {
        p2.on('input', function() {
            validateForm(false);
        });
    }

    // Run once on load to ensure button state is correct if fields are pre-filled (unlikely but safe)
    if (p1.length || p2.length) {
        validateForm(false);
    }

    $('form').on('submit', function(event) {
        if (!submitted) {
            event.preventDefault();
            event.stopPropagation();
            validateForm(true);
        }
    });
});
