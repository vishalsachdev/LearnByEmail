// Form validation functions with improved mobile experience

document.addEventListener('DOMContentLoaded', function() {
    // Helper function for showing inline validation messages
    function showValidationMessage(input, message, isError = true) {
        // Remove any existing validation message
        const existingMessage = input.parentNode.querySelector('.validation-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Add validation styles to the input
        input.classList.remove('is-valid', 'is-invalid');
        input.classList.add(isError ? 'is-invalid' : 'is-valid');
        
        // Create and append validation message
        const validationMessage = document.createElement('div');
        validationMessage.className = isError ? 'invalid-feedback validation-message' : 'valid-feedback validation-message';
        validationMessage.textContent = message;
        input.parentNode.appendChild(validationMessage);
        
        // Make sure it's visible on mobile
        validationMessage.style.display = 'block';
    }
    
    // Registration form validation
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        
        // Live validation for password
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                if (this.value.length < 8) {
                    showValidationMessage(this, 'Password must be at least 8 characters long');
                } else {
                    showValidationMessage(this, 'Password length is good', false);
                }
            });
        }
        
        // Live validation for confirm password
        if (confirmPasswordInput && passwordInput) {
            confirmPasswordInput.addEventListener('input', function() {
                if (this.value !== passwordInput.value) {
                    showValidationMessage(this, 'Passwords do not match');
                } else {
                    showValidationMessage(this, 'Passwords match', false);
                }
            });
        }
        
        // Form submission validation
        registerForm.addEventListener('submit', function(event) {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            let isValid = true;
            
            if (password !== confirmPassword) {
                showValidationMessage(confirmPasswordInput, 'Passwords do not match');
                isValid = false;
            }
            
            if (password.length < 8) {
                showValidationMessage(passwordInput, 'Password must be at least 8 characters long');
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
                // Scroll to the first error for mobile visibility
                const firstError = document.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });
    }
    
    // Subscription form validation
    const subscriptionForm = document.getElementById('subscriptionForm');
    if (subscriptionForm) {
        const topicInput = document.getElementById('topic');
        
        // Live validation for topic
        if (topicInput) {
            topicInput.addEventListener('input', function() {
                const topic = this.value.trim();
                if (!topic) {
                    showValidationMessage(this, 'Please enter a topic');
                } else if (topic.length < 3) {
                    showValidationMessage(this, 'Topic is too short (minimum 3 characters)');
                } else if (topic.length > 50) {
                    showValidationMessage(this, 'Topic is too long (maximum 50 characters)');
                } else if (!topic.match(/^[A-Za-z0-9\s\-_,.&+\'()]+$/)) {
                    showValidationMessage(this, 'Topic contains invalid characters. Please use only letters, numbers, spaces, and common punctuation.');
                } else {
                    showValidationMessage(this, 'Topic looks good', false);
                }
            });
        }
        
        // Form submission validation
        subscriptionForm.addEventListener('submit', function(event) {
            const topic = topicInput.value.trim();
            let isValid = true;
            
            if (!topic) {
                showValidationMessage(topicInput, 'Please enter a topic');
                isValid = false;
            } else if (topic.length < 3) {
                showValidationMessage(topicInput, 'Topic is too short (minimum 3 characters)');
                isValid = false;
            } else if (topic.length > 50) {
                showValidationMessage(topicInput, 'Topic is too long (maximum 50 characters)');
                isValid = false;
            } else if (!topic.match(/^[A-Za-z0-9\s\-_,.&+\'()]+$/)) {
                showValidationMessage(topicInput, 'Topic contains invalid characters. Please use only letters, numbers, spaces, and common punctuation.');
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
                // Scroll to the first error for mobile visibility
                const firstError = document.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });
    }
});