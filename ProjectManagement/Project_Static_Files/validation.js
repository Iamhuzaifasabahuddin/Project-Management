/**
 * HEXZ CONNECT - Global Form Validation
 * Modular engine inspired by register.js.
 * Provides real-time feedback and protects the database from invalid submissions.
 */

const HEXZ_VALIDATION = (function() {
    'use strict';

    // Helper: Email Regex
    const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    /**
     * Updates the UI state of a field.
     * Toggles is-valid/is-invalid classes and manages feedback messages.
     */
    const changeValidity = (input, message, isValid) => {
        const fieldGroup = input.closest('.field-group') || input.closest('.mb-3') || input.parentElement;
        let feedback = fieldGroup.querySelector('.invalid-feedback');
        
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            // Insert after input or its wrapper
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
        
        // Handle Select2 specific UI integration
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

    /**
     * Validates an individual field based on its attributes and type.
     * @param {HTMLElement} field - The input element to validate.
     * @param {boolean} silent - If true, checks validity without updating UI.
     */
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

        // 3. Date Integrity Check (Prevent past dates for due_date)
        if ((field.id.includes('due_date') || field.name.includes('due_date')) && val) {
            const selectedDate = new Date(val);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (selectedDate < today) {
                if (!silent) changeValidity(field, 'Date cannot be in the past.', false);
                return false;
            }
        }

        // 4. File Size Safety (10MB limit)
        if (field.type === 'file' && field.files.length > 0) {
            for (let i = 0; i < field.files.length; i++) {
                if (field.files[i].size > 10 * 1024 * 1024) {
                    if (!silent) changeValidity(field, 'File exceeds 10MB limit.', false);
                    return false;
                }
            }
        }

        // If field has data and passed checks, mark as valid
        if (!silent) {
            if (val) {
                changeValidity(field, '', true);
            } else {
                // Not required and empty: clean state
                field.classList.remove('is-invalid', 'is-valid');
                const fieldGroup = field.closest('.field-group') || field.closest('.mb-3') || field.parentElement;
                const feedback = fieldGroup.querySelector('.invalid-feedback');
                if (feedback) feedback.style.display = 'none';
            }
        }
        
        return true;
    };

    /**
     * Initializes all forms marked with 'novalidate'.
     */
    const init = () => {
        console.log("HEXZ Validation Engine active.");
        const forms = document.querySelectorAll('form[novalidate]');
        
        forms.forEach(form => {
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
                // Real-time validation on loss of focus
                input.addEventListener('blur', () => {
                    validateField(input);
                    updateSubmitBtnState();
                });
                
                // Immediate correction check & Button update
                input.addEventListener('input', () => {
                    updateSubmitBtnState();
                    if (input.classList.contains('is-invalid')) {
                        validateField(input);
                    }
                });

                // Handle changes for select and file inputs
                input.addEventListener('change', () => {
                    validateField(input);
                    updateSubmitBtnState();
                });

                // Periodic check for Select2 availability
                if (input.classList.contains('django-select2')) {
                    const checkS2 = setInterval(() => {
                        if (typeof $ !== 'undefined') {
                            $(input).on('change', () => {
                                validateField(input);
                                updateSubmitBtnState();
                            });
                            clearInterval(checkS2);
                        }
                    }, 500);
                    setTimeout(() => clearInterval(checkS2), 5000);
                }
            });

            // Initial check to set button state on load
            updateSubmitBtnState();

            form.addEventListener('submit', function(e) {
                let isFormValid = true;
                
                // Final check of all fields
                inputs.forEach(input => {
                    if (!validateField(input)) isFormValid = false;
                });

                if (!isFormValid) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.warn("HEXZ: Form invalid. Submission blocked.");
                    
                    const firstErr = form.querySelector('.is-invalid');
                    if (firstErr) {
                        firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    console.log("HEXZ: Form valid. Processing...");
                    if (submitBtn) {
                        // Enter static processing state
                        submitBtn.disabled = true;
                        submitBtn.classList.add('btn-processing'); 
                        submitBtn.innerHTML = `
                            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                            <span>Processing...</span>
                        `;
                    }
                }
            });
        });
    };

    return { init };
})();

// Auto-boot
document.addEventListener('DOMContentLoaded', HEXZ_VALIDATION.init);
