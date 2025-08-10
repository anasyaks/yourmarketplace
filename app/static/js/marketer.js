// app/static/js/marketer.js
// This file contains JavaScript specific to the marketer-facing routes and functionalities.

document.addEventListener('DOMContentLoaded', function() {
    console.log('Marketer-specific JavaScript loaded.');

    // Get references to the main product form's shop and category selects
    const shopSelect = document.getElementById('shop_id'); // For create_product.html and edit_product.html
    const categorySelectProductForm = document.getElementById('category_id'); // For create_product.html and edit_product.html
    const categorySelectShopProducts = document.getElementById('category_id_product_form'); // For shop_products.html

    // Function to fetch and populate category choices for a given shop and target select element
    function fetchAndPopulateCategoryChoices(shopId, targetCategorySelect, initialSelectedValue = null) {
        if (!shopId) {
            targetCategorySelect.innerHTML = '<option value="">Select a shop first</option>';
            return;
        }

        // Use the new dedicated endpoint for fetching categories
        fetch(`/marketer/categories_by_shop/${shopId}`, {
            method: 'GET', // Use GET for fetching data
            headers: {
                'X-Requested-With': 'XMLHttpRequest', // Identify as AJAX request
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            targetCategorySelect.innerHTML = ''; // Clear existing options
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a category';
            targetCategorySelect.appendChild(defaultOption);

            if (data.categories && data.categories.length > 0) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    targetCategorySelect.appendChild(option);
                });
            } else {
                const noCategoriesOption = document.createElement('option');
                noCategoriesOption.value = '';
                noCategoriesOption.textContent = 'No categories found for this shop';
                targetCategorySelect.appendChild(noCategoriesOption);
            }

            // Attempt to set initial selected value if provided
            if (initialSelectedValue) {
                targetCategorySelect.value = initialSelectedValue;
            } else if (targetCategorySelect.options.length > 1) {
                // If no initial value, select the first actual category (not the "Select a category" placeholder)
                targetCategorySelect.value = targetCategorySelect.options[1].value;
            }
        })
        .catch(error => {
            console.error('Error fetching categories:', error);
            targetCategorySelect.innerHTML = '<option value="">Error loading categories</option>';
        });
    }

    // --- Initial population and change listener for ProductForm's shop select (create_product.html & edit_product.html) ---
    if (shopSelect && categorySelectProductForm) {
        // Store the initial category value if it exists (for edit product case)
        const initialCategoryValue = categorySelectProductForm.value;

        shopSelect.addEventListener('change', function() {
            // When shop changes, clear category selection and fetch new categories
            categorySelectProductForm.value = '';
            fetchAndPopulateCategoryChoices(this.value, categorySelectProductForm);
        });

        // Trigger initial population on page load
        if (shopSelect.value) {
            fetchAndPopulateCategoryChoices(shopSelect.value, categorySelectProductForm, initialCategoryValue);
        }
    }

    // --- Initial population for shop_products.html (shop_id is fixed) ---
    if (categorySelectShopProducts) {
        const currentShopId = document.querySelector('input[name="shop_id"][type="hidden"]').value;
        const initialCategoryValue = categorySelectShopProducts.value; // Get current value for edit case
        if (currentShopId) {
            fetchAndPopulateCategoryChoices(currentShopId, categorySelectShopProducts, initialCategoryValue);
        }
    }
});
