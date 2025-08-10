// app/static/js/customer.js
// This file will contain JavaScript specific to the customer-facing routes.

document.addEventListener('DOMContentLoaded', function() {
    console.log('Customer-specific JavaScript loaded.');

    // Example: Logic for filtering products, dynamic search, etc.
    // This could involve AJAX calls if you want more dynamic filtering without full page reloads.

    // If you have a product rating form, you might add event listeners here:
    const ratingForm = document.querySelector('#product-rating-form');
    if (ratingForm) {
        ratingForm.addEventListener('submit', function(event) {
            // Client-side validation for rating, or display loading state
            console.log('Submitting rating...');
        });
    }
});
