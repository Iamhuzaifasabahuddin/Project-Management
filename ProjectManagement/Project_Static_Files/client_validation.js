/**
 * HEXZ CONNECT - Client Form Specific Validation
 */

const CLIENT_VALIDATION = (function() {
    'use strict';

    const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    const changeValidity = (input, message, isValid) => {
        const fieldGroup = input.closest('.field-group') || input.closest('.mb-3') || input.parentElement;
        let feedback = fieldGroup.querySelector('.invalid-feedback');
        
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            const insertAfter = input.closest('.field-wrap') || input;
            if (insertAfter.nextSibling) {
                insertAfter.parentNode.insertBefore(feedback, insertAfter.nextSibling);
            } else {
                insertAfter.parentNode.appendChild(feedback);
            }
        }

        if (isValid) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
            feedback.style.display = 'none';
        } else {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            feedback.textContent = message;
            feedback.style.display = 'block';
        }
        
        if (input.classList.contains('django-select2') && typeof $ !== 'undefined') {
            const s2Container = $(input).next('.select2-container');
            if (s2Container.length) {
                if (isValid) {
                    s2Container.removeClass('is-invalid').addClass('is-valid');
                } else {
                    s2Container.addClass('is-invalid').removeClass('is-valid');
                }
            }
        }
    };

    const validateField = (field, silent = false) => {
        const isRequired = field.required || field.hasAttribute('required');
        const val = field.value ? field.value.trim() : '';

        // 1. Required Check
        if (isRequired && !val) {
            if (!silent) changeValidity(field, 'This field is required.', false);
            return false;
        }

        // 2. Email Check
        if (field.type === 'email' && val && !isValidEmail(val)) {
            if (!silent) changeValidity(field, 'Please enter a valid email address.', false);
            return false;
        }

        // 3. Phone Number Check
        if (field.name === 'number' && val) {
            if (val.length < 10 || val.length > 15 || !/^\d+$/.test(val)) {
                if (!silent) changeValidity(field, 'Phone number must be 10-15 digits.', false);
                return false;
            }
        }

        // 4. Amount Validation
        if (field.name === 'total_amount' || field.name === 'amount_paid') {
            const form = field.form;
            const totalField = form.querySelector('[name="total_amount"]');
            const paidField = form.querySelector('[name="amount_paid"]');
            const totalVal = parseFloat(totalField.value) || 0;
            const paidVal = parseFloat(paidField.value) || 0;

            if (val && (isNaN(parseFloat(val)) || parseFloat(val) < 0)) {
                if (!silent) changeValidity(field, 'Enter a valid non-negative number.', false);
                return false;
            }

            if (paidVal > totalVal) {
                const msg = field.name === 'total_amount' 
                    ? 'Total cannot be less than paid amount.' 
                    : 'Paid amount cannot exceed total.';
                if (!silent) changeValidity(field, msg, false);
                return false;
            }
        }

        if (!silent) {
            if (val || field.type === 'checkbox') {
                changeValidity(field, '', true);
            } else {
                field.classList.remove('is-invalid', 'is-valid');
                const fieldGroup = field.closest('.field-group') || field.closest('.mb-3') || field.parentElement;
                const feedback = fieldGroup.querySelector('.invalid-feedback');
                if (feedback) feedback.style.display = 'none';
            }
        }
        
        return true;
    };

    const init = () => {
        const forms = document.querySelectorAll('form[novalidate]');
        
        forms.forEach(form => {
            // Only apply if it's a client form (detect by fields)
            if (!form.querySelector('[name="total_amount"]') || !form.querySelector('[name="amount_paid"]')) return;

            console.log("HEXZ Client Validation active.");
            const inputs = form.querySelectorAll('input, textarea, select');
            const submitBtn = form.querySelector('[type="submit"]');

            const updateSubmitBtnState = () => {
                let isFormValid = true;
                inputs.forEach(input => {
                    if (!validateField(input, true)) isFormValid = false;
                });
                if (submitBtn) submitBtn.disabled = !isFormValid;
            };

            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    validateField(input);
                    updateSubmitBtnState();
                });
                
                input.addEventListener('input', () => {
                    updateSubmitBtnState();
                    if (input.classList.contains('is-invalid') || input.name === 'total_amount' || input.name === 'amount_paid') {
                        validateField(input);
                    }

                    // Cross-validate amounts
                    if (input.name === 'total_amount' || input.name === 'amount_paid') {
                        const otherName = input.name === 'total_amount' ? 'amount_paid' : 'total_amount';
                        const otherField = form.querySelector(`[name="${otherName}"]`);
                        if (otherField) validateField(otherField, false);
                    }
                });

                input.addEventListener('change', () => {
                    validateField(input);
                    updateSubmitBtnState();
                });
            });

            updateSubmitBtnState();
        });
    };

    return { init };
})();

document.addEventListener('DOMContentLoaded', CLIENT_VALIDATION.init);
