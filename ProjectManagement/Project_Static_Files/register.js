// Function to change the validity of an input field based on a boolean flag
function changeValidity(input, feedback, validity) {
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
    if (input.value.length === 0) {
        feedback.textContent = 'Cannot be empty!';
        return false;
    }
    return true;
}

// Function to validate if an input field does not contain spaces
function validateNoSpaces(id) {
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (input.value.includes(' ')) {
        feedback.textContent = 'Cannot contain spaces!';
        return false;
    }
    return true;
}

// Function to validate the length of an input field
function validateLength(id, min, max) {
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (input.value.length < min || input.value.length > max) {
        feedback.textContent = `Must be ${min}-${max} long!`;
        return false;
    }
    return true;
}

// Function to validate if an input field contains only alphabetic characters
function validateAlphabetic(id) {
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!/^[a-zA-Z]+$/.test(input.value)) {
        feedback.textContent = `Must contain letters only!`;
        return false;
    }
    return true;
}

/*
Function to validate the first name
*/
function validateFirstname() {
    const id = 'id_first_name';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;
    changeValidity(input, feedback, false);
    if (validateNotEmpty(id) && validateNoSpaces(id) &&
        validateLength(id, 2, 30) && validateAlphabetic(id)) {
        changeValidity(input, feedback, true);
        feedback.textContent = '';
        return true;
    }
    return false;
}

/*
Function to validate the last name
*/
function validateLastname() {
    const id = 'id_last_name';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;
    changeValidity(input, feedback, false);
    if (validateNotEmpty(id) && validateNoSpaces(id) &&
        validateLength(id, 2, 30) && validateAlphabetic(id)) {
        changeValidity(input, feedback, true);
        feedback.textContent = '';
        return true;
    }
    return false;
}

/*
Function to validate the username
*/
function validateUsername(submit = false) {
    const id = 'id_username';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return;

    if (validateNotEmpty(id) && validateNoSpaces(id) && validateLength(id, 4, 20)) {
        $.ajax({
            url: '/checkUsername/',
            type: 'GET',
            data: {username: input.value},
            success: function (data) {
                let usernameValid = false;
                if (data.usernameExists) {
                    changeValidity(input, feedback, false);
                    feedback.textContent = 'Username is already taken!';
                } else {
                    changeValidity(input, feedback, true);
                    feedback.textContent = '';
                    usernameValid = true;
                }
                validateEmail(submit, usernameValid);
            }
        });
    } else {
        changeValidity(input, feedback, false);
        validateEmail(submit, false);
    }
}

/*
Function to validate email
 */
function validateEmail(submit = false, usernameValid = false) {
    const id = 'id_email';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return;

    if (validateNotEmpty(id)) {
        $.ajax({
            url: '/checkEmail/',
            type: 'get',
            data: {email: input.value},
            success: function (data) {
                let emailValid = false;
                if (data.emailExists) {
                    changeValidity(input, feedback, false);
                    feedback.textContent = 'Email is already registered!';
                } else {
                    changeValidity(input, feedback, true);
                    feedback.textContent = '';
                    emailValid = true;
                }
                asyncValidate(submit, usernameValid, emailValid)
            }
        });
    } else {
        changeValidity(input, feedback, false);
        asyncValidate(submit, usernameValid, false)
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
    const password = document.getElementById('id_password1').value;
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
    const id = 'id_password1';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;
    
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
    const id = 'id_password2';
    const input = document.querySelector(`#${id}`);
    const feedback = document.querySelector(`.invalid-feedback.${id}`);
    if (!input) return false;

    changeValidity(input, feedback, false);
    if (validateNotEmpty(id)) {
        if (document.querySelector('#id_password1').value !== input.value) {
            feedback.textContent = 'Passwords must be the same!'
        } else {
            changeValidity(input, feedback, true);
            feedback.textContent = '';
            return true;
        }
    }
    return false;
}

function syncValidate() {
    const fn = validateFirstname();
    const ln = validateLastname();
    const p1 = validatePassword();
    const p2 = validateConfirmPassword();
    return fn && ln && p1 && p2;
}

let submitted = false;

function asyncValidate(submit = false, usernameValid = false, emailValid = false) {
    if (syncValidate() && usernameValid && emailValid) {
        if (submit) {
            if (!submitted) {
                submitted = true;
                document.querySelector('form').submit();
            }
        } else {
            document.querySelector('button[type="submit"]').disabled = false;
        }
    } else {
        if (submit) {
        }
        document.querySelector('button[type="submit"]').disabled = true;
    }
}

$(document).ready(function() {
    'use strict'
    $('input.form-control').on('input', function() {
        validateUsername(false);
    });
    // Toggle password visibility
    $('.toggle-password').on('click', function() {
        const input = $(this).closest('.input-group').find('input');
        const icon = $(this).find('i');
        const type = input.attr('type') === 'password' ? 'text' : 'password';
        input.attr('type', type);
        icon.toggleClass('bi-eye bi-eye-slash');
    });

    $('form').on('submit', function(event) {
        if (!submitted) {
            event.preventDefault();
            event.stopPropagation();
            validateUsername(true);
        }
    });
});
