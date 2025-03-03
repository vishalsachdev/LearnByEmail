// Form validation functions

document.addEventListener('DOMContentLoaded', function() {
    // Registration form validation
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password !== confirmPassword) {
                event.preventDefault();
                alert('Passwords do not match!');
            }
            
            if (password.length < 8) {
                event.preventDefault();
                alert('Password must be at least 8 characters long');
            }
        });
    }
    
    // Subscription form validation
    const subscriptionForm = document.getElementById('subscriptionForm');
    if (subscriptionForm) {
        subscriptionForm.addEventListener('submit', function(event) {
            const topic = document.getElementById('topic').value;
            
            if (!topic) {
                event.preventDefault();
                alert('Please enter a topic');
            }
            
            if (topic.length < 2 || topic.length > 100) {
                event.preventDefault();
                alert('Topic must be between 2-100 characters');
            }
        });
    }
});