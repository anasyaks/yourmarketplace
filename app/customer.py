from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app.models import Shop, Product, Category, Rating, Order, OrderItem, Notification
from app.forms import RatingForm, ProfileForm, ChangePasswordForm
from app import db
from sqlalchemy import desc

bp = Blueprint('customer', __name__)

@bp.route('/')
def index():
    categories = Category.query.all()
    featured_shops = Shop.query.order_by(Shop.created_at.desc()).limit(8).all()
    featured_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template('customer/index.html',
                         categories=categories,
                         featured_shops=featured_shops,
                         featured_products=featured_products)

# NEW ROUTE: Customer Dashboard
@bp.route('/dashboard')
@login_required
def customer_dashboard(): # Renamed from 'dashboard' to 'customer_dashboard' for clarity
    # Ensure only customers can access this specific dashboard
    if current_user.role != 'customer':
        flash('Access denied. This dashboard is for customers.', 'danger')
        # Redirect marketers/admins to their respective dashboards
        if current_user.role == 'marketer':
            return redirect(url_for('marketer.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer.index')) # Fallback for unhandled roles

    # Fetch recent orders for the customer
    recent_orders = current_user.orders.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('customer/dashboard.html', recent_orders=recent_orders)


@bp.route('/shops')
def shop_list():
    category_id = request.args.get('category_id')
    location = request.args.get('location')
    query = request.args.get('q')

    shops_query = Shop.query

    if category_id:
        shops_query = shops_query.join(Product).filter(Product.category_id == category_id, Product.is_active==True)

    if location:
        shops_query = shops_query.filter(Shop.location.ilike(f'%{location}%'))

    if query:
        shops_query = shops_query.filter(Shop.name.ilike(f'%{query}%'))

    shops = shops_query.distinct().all()
    categories = Category.query.all()
    return render_template('customer/shop_list.html', shops=shops, categories=categories)

@bp.route('/shops/<int:shop_id>')
def shop_detail(shop_id):
    shop = Shop.query.get_or_404(shop_id)

    categories = Category.query.filter_by(shop_id=shop.id).all()

    products_by_category = {}
    for category in categories:
        products = Product.query.filter_by(shop_id=shop.id, category_id=category.id, is_active=True).all()
        if products:
            products_by_category[category.name] = products

    uncategorized = Product.query.filter_by(shop_id=shop.id, category_id=None, is_active=True).all()
    if uncategorized:
        products_by_category['Uncategorized'] = uncategorized

    avg_rating = shop.average_rating()
    rating_count = shop.ratings.count()

    return render_template('customer/shop_detail.html',
                         shop=shop,
                         products_by_category=products_by_category,
                         products_count=Product.query.filter_by(shop_id=shop.id, is_active=True).count(),
                         avg_rating=avg_rating,
                         rating_count=rating_count)

@bp.route('/product/<int:product_id>/rate', methods=['POST'])
@login_required
def rate_product(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_active:
        flash('Cannot rate an inactive product.', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))

    rating_value = request.form.get('rating', type=int)
    comment_text = request.form.get('comment', '').strip()

    if rating_value is None or not (1 <= rating_value <= 5):
        flash('Invalid rating value. Please select a rating between 1 and 5 stars.', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))

    existing_rating = Rating.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()

    if existing_rating:
        existing_rating.value = rating_value
        existing_rating.comment = comment_text if comment_text else None
    else:
        rating = Rating(
            value=rating_value,
            comment=comment_text if comment_text else None,
            product_id=product_id,
            user_id=current_user.id,
            shop_id=product.shop_id
        )
        db.session.add(rating)

    db.session.commit()
    flash('Thank you for rating this product!', 'success')
    return redirect(url_for('customer.product_detail', product_id=product_id))

@bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_active and (not current_user.is_authenticated or current_user.role != 'admin'):
        flash('This product is currently unavailable.', 'warning')
        return redirect(url_for('customer.index'))

    avg_rating = product.average_rating()
    rating_count = product.ratings.count()
    form = RatingForm()
    return render_template('customer/product_detail.html',
                         product=product,
                         avg_rating=avg_rating,
                         rating_count=rating_count,
                         form=form,
                         RatingModel=Rating)

@bp.route('/search')
def search():
    search_query = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    category_id = request.args.get('category_id', type=int)
    sort_by = request.args.get('sort_by', 'newest')

    products_query = Product.query.filter_by(is_active=True)
    shops_query = Shop.query

    if search_query:
        products_query = products_query.filter(Product.name.ilike(f'%{search_query}%'))
        shops_query = shops_query.filter(Shop.name.ilike(f'%{search_query}%'))

    if min_price is not None:
        products_query = products_query.filter(Product.price >= min_price)

    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)

    if category_id:
        products_query = products_query.filter(Product.category_id == category_id)

    if sort_by == 'price_asc':
        products_query = products_query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        products_query = products_query.order_by(Product.price.desc())
    elif sort_by == 'rating_desc':
        products_query = products_query.order_by(Product.created_at.desc())
    else: # 'newest'
        products_query = products_query.order_by(Product.created_at.desc())

    products = products_query.all()
    shops = shops_query.all()

    all_categories = Category.query.all()

    return render_template('customer/search_results.html',
                         query=search_query,
                         products=products,
                         shops=shops,
                         categories=all_categories,
                         min_price=min_price,
                         max_price=max_price,
                         selected_category_id=category_id,
                         sort_by=sort_by)

# --- SHOPPING CART ROUTES ---

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_active:
        flash('This product is currently unavailable and cannot be added to cart.', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))

    quantity = request.form.get('quantity', 1, type=int)

    if quantity <= 0:
        flash('Quantity must be at least 1.', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))

    if 'cart' not in session:
        session['cart'] = {}

    product_id_str = str(product.id)

    if product_id_str in session['cart']:
        session['cart'][product_id_str]['quantity'] += quantity
    else:
        session['cart'][product_id_str] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image': product.image
        }
    session.modified = True

    flash(f'{quantity} x {product.name} added to cart!', 'success')
    return redirect(url_for('customer.view_cart'))

@bp.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0

    products_to_remove = []
    for product_id_str, item_data in cart.items():
        product = Product.query.get(int(product_id_str))
        if product and product.is_active:
            item_data['id'] = product.id
            item_data['subtotal'] = item_data['quantity'] * item_data['price']
            cart_items.append(item_data)
            total_price += item_data['subtotal']
        else:
            products_to_remove.append(product_id_str)

    for product_id_str in products_to_remove:
        product_name = cart[product_id_str]['name']
        del session['cart'][product_id_str]
        flash(f"Product '{product_name}' is no longer available and has been removed from your cart.", "warning")
    
    if products_to_remove:
        session.modified = True
        if not session.get('cart'):
            flash("Your cart is now empty as some items became unavailable.", "warning")
            return redirect(url_for('customer.index'))


    return render_template('customer/cart.html', cart_items=cart_items, total_price=total_price)

@bp.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_active:
        flash('This product is currently unavailable and cannot be updated in cart.', 'danger')
        return redirect(url_for('customer.view_cart'))

    quantity = request.form.get('quantity', type=int)
    product_id_str = str(product_id)

    if 'cart' in session and product_id_str in session['cart']:
        if quantity is not None and quantity > 0:
            session['cart'][product_id_str]['quantity'] = quantity
            flash(f'Quantity for {session["cart"][product_id_str]["name"]} updated to {quantity}.', 'info')
        else:
            del session['cart'][product_id_str]
            flash(f'Item removed from cart.', 'info')
        session.modified = True
    else:
        flash('Item not found in cart.', 'danger')

    return redirect(url_for('customer.view_cart'))

@bp.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    product_id_str = str(product_id)
    if 'cart' in session and product_id_str in session['cart']:
        product_name = session['cart'][product_id_str]['name']
        del session['cart'][product_id_str]
        session.modified = True
        flash(f'{product_name} removed from cart.', 'info')
    else:
        flash('Item not found in cart.', 'danger')
    return redirect(url_for('customer.view_cart'))

@bp.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty. Please add items before checking out.', 'warning')
        return redirect(url_for('customer.index'))

    cart_items = []
    total_price = 0
    products_to_remove = []
    for product_id_str, item_data in cart.items():
        product = Product.query.get(int(product_id_str))
        if product and product.is_active:
            item_data['id'] = product.id
            item_data['subtotal'] = item_data['quantity'] * item_data['price']
            cart_items.append(item_data)
            total_price += item_data['subtotal']
        else:
            products_to_remove.append(product_id_str)

    for product_id_str in products_to_remove:
        product_name = cart[product_id_str]['name']
        del session['cart'][product_id_str]
        flash(f"Product '{product_name}' is no longer available and was removed from your cart during checkout.", "warning")
    
    if products_to_remove:
        session.modified = True
        if not session.get('cart'):
            flash("Your cart is now empty as some items became unavailable.", "warning")
            return redirect(url_for('customer.index'))


    return render_template('customer/checkout.html', cart_items=cart_items, total_price=total_price)

@bp.route('/confirm_order', methods=['POST'])
@login_required
def confirm_order():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty. Cannot confirm an empty order.', 'warning')
        return redirect(url_for('customer.index'))

    valid_cart_items = {}
    products_removed_during_confirm = []
    marketer_ids_to_notify = set()

    for product_id_str, item_data in cart.items():
        product = Product.query.get(int(product_id_str))
        if product and product.is_active:
            valid_cart_items[product_id_str] = item_data
            marketer_ids_to_notify.add(product.shop.owner.id)
        else:
            products_removed_during_confirm.append(item_data['name'])

    if products_removed_during_confirm:
        flash(f"Some products were removed from your order as they became unavailable: {', '.join(products_removed_during_confirm)}", 'danger')
        session['cart'] = valid_cart_items
        session.modified = True
        if not valid_cart_items:
            flash('Your cart is now empty. Please add items before checking out.', 'warning')
            return redirect(url_for('customer.index'))
        return redirect(url_for('customer.checkout'))


    total_price = sum(item['quantity'] * item['price'] for item in valid_cart_items.values())

    new_order = Order(
        user_id=current_user.id,
        total_price=total_price,
        status='Pending'
    )
    db.session.add(new_order)
    db.session.flush()

    for product_id_str, item_data in valid_cart_items.items():
        product = Product.query.get(int(product_id_str))
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            shop_id=product.shop_id,
            quantity=item_data['quantity'],
            price_at_purchase=item_data['price']
        )
        db.session.add(order_item)

    for marketer_id in marketer_ids_to_notify:
        notification_message = f"New order #{new_order.id} placed by {current_user.username} containing your products."
        notification = Notification(
            user_id=marketer_id,
            message=notification_message,
            order_id=new_order.id
        )
        db.session.add(notification)

    db.session.commit()

    session.pop('cart', None)
    session.modified = True
    flash('Your order has been placed successfully! Marketers will be in touch.', 'success')
    return redirect(url_for('customer.index'))

# --- CUSTOMER ORDER HISTORY ---
@bp.route('/my_orders')
@login_required
def my_orders():
    orders = current_user.orders.order_by(Order.created_at.desc()).all()
    return render_template('customer/order_history.html', orders=orders)

@bp.route('/my_orders/<int:order_id>')
@login_required
def customer_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Access denied. You do not have permission to view this order.', 'danger')
        return redirect(url_for('customer.my_orders'))

    return render_template('customer/order_detail.html', order=order)


# --- CUSTOMER PROFILE ROUTES ---
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def customer_profile():
    form = ProfileForm(original_username=current_user.username, original_email=current_user.email, obj=current_user)
    change_password_form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('customer.customer_profile'))

    return render_template('customer/profile.html', form=form, change_password_form=change_password_form)

@bp.route('/change_password', methods=['POST'])
@login_required
def change_customer_password():
    change_password_form = ChangePasswordForm()
    profile_form = ProfileForm(original_username=current_user.username, original_email=current_user.email, obj=current_user)

    if change_password_form.validate_on_submit():
        if not current_user.check_password(change_password_form.old_password.data):
            flash('Incorrect current password.', 'danger')
        else:
            current_user.set_password(change_password_form.new_password.data)
            db.session.commit()
            flash('Your password has been changed!', 'success')
            return redirect(url_for('customer.customer_profile'))

    return render_template('customer/profile.html', form=profile_form, change_password_form=change_password_form)
