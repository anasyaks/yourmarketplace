// app/static/js/main.js
// This file can contain global JavaScript functions or event listeners
// that apply across the entire application.

document.addEventListener('DOMContentLoaded', function() {
    console.log('Main JavaScript loaded.');
    // Example: Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Handle flash message dismissal (optional)
    document.querySelectorAll('.flash-message').forEach(message => {
        message.addEventListener('click', function() {
            this.style.display = 'none';
        });
    });
});
