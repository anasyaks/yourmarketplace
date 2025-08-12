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

        fetch(`/marketer/categories_by_shop/${shopId}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received category data:', data);

            targetCategorySelect.innerHTML = '';
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

            if (initialSelectedValue) {
                targetCategorySelect.value = initialSelectedValue;
            } else if (targetCategorySelect.options.length > 1) {
                targetCategorySelect.value = targetCategorySelect.options[1].value;
            }
        })
        .catch(error => {
            console.error('Error fetching categories:', error);
            targetCategorySelect.innerHTML = '<option value="">Error loading categories</option>';
        });
    }

    if (shopSelect && categorySelectProductForm) {
        const initialCategoryValue = categorySelectProductForm.value;

        shopSelect.addEventListener('change', function() {
            categorySelectProductForm.value = '';
            fetchAndPopulateCategoryChoices(this.value, categorySelectProductForm);
        });

        if (shopSelect.value) {
            fetchAndPopulateCategoryChoices(shopSelect.value, categorySelectProductForm, initialCategoryValue);
        }
    }

    if (categorySelectShopProducts) {
        const currentShopId = document.querySelector('input[name="shop_id"][type="hidden"]').value;
        const initialCategoryValue = categorySelectShopProducts.value;
        if (currentShopId) {
            fetchAndPopulateCategoryChoices(currentShopId, categorySelectShopProducts, initialCategoryValue);
        }
    }
});
