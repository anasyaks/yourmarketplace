// app/static/js/admin.js
// This file contains JavaScript specific to the administrator-facing routes and functionalities.

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin-specific JavaScript loaded.');

    // Example: Confirm before deleting a user/shop/product
    // This is a more user-friendly alternative to Flask's flash messages for confirmation
    document.querySelectorAll('.confirm-delete').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent immediate form submission

            const form = this.closest('form');
            const itemName = this.dataset.itemName || 'item'; // Get name from data-item-name attribute

            // Display a custom confirmation modal or dialog here instead of alert/confirm
            // For now, using confirm() for illustrative purposes, but replace this with a custom modal UI.
            if (confirm(`Are you sure you want to delete this ${itemName}? This action cannot be undone.`)) {
                form.submit();
            }
        });
    });

    // Example: Select/Deselect all for bulk actions (e.g., pending users)
    const selectAllCheckbox = document.getElementById('select-all-users');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            document.querySelectorAll('input[name="user_ids"]').forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // Example: Filter/Search functionality that can be enhanced with client-side JS or AJAX
    const adminSearchInput = document.getElementById('admin-search-input');
    if (adminSearchInput) {
        adminSearchInput.addEventListener('keyup', function() {
            // Implement client-side filtering of tables or trigger AJAX search
            console.log('Admin search query:', this.value);
        });
    }

    // You might also have JS for charts, interactive tables, etc.
});
