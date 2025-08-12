from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Shop, Product, Category, Order, OrderItem, User, Notification
from app.forms import ShopForm, ProductForm, NewCategoryForm, ProfileForm, ChangePasswordForm
from app import db
from app.utils import save_image
from werkzeug.datastructures import FileStorage

bp = Blueprint('marketer', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shops = current_user.shops.order_by(Shop.created_at.desc()).all()

    marketer_shop_ids = [shop.id for shop in current_user.shops.all()]
    total_products_count = Product.query.filter(Product.shop_id.in_(marketer_shop_ids)).count()


    marketer_shop_ids = [shop.id for shop in current_user.shops.all()]
    recent_order_items = OrderItem.query.filter(OrderItem.shop_id.in_(marketer_shop_ids))\
                                    .order_by(OrderItem.id.desc())\
                                    .limit(5).all()

    recent_orders = []
    seen_order_ids = set()
    for item in recent_order_items:
        if item.order_id not in seen_order_ids:
            recent_orders.append(item.order)
            seen_order_ids.add(item.order_id)

    pending_orders_count = OrderItem.query.filter(
        OrderItem.shop_id.in_(marketer_shop_ids),
        OrderItem.order.has(Order.status == 'Pending')
    ).count()


    return render_template('marketer/dashboard.html',
                         shops=shops,
                         total_products_count=total_products_count,
                         recent_orders=recent_orders,
                         pending_orders_count=pending_orders_count)


@bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = NewCategoryForm()
    form.shop_id.choices = [(s.id, s.name) for s in current_user.shops.all()]

    if form.validate_on_submit():
        shop_id = form.shop_id.data
        category_name = form.name.data

        if not shop_id:
            flash('Please select a shop.', 'danger')
            return redirect(url_for('marketer.create_category'))

        if Category.query.filter_by(name=category_name, shop_id=shop_id).first():
            flash('Category already exists for this shop!', 'danger')
            return redirect(url_for('marketer.create_category'))

        category = Category(name=category_name, shop_id=shop_id)
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('marketer.manage_products'))

    return render_template('marketer/create_category.html', form=form)

@bp.route('/categories_by_shop/<int:shop_id>', methods=['GET'])
@login_required
def categories_by_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner != current_user and current_user.role != 'admin':
        return jsonify({'error': 'Access denied to this shop\'s categories'}), 403

    categories = Category.query.filter_by(shop_id=shop_id).all()

    global_categories = Category.query.filter_by(shop_id=None).all()
    
    all_categories = categories + global_categories
    
    return jsonify({
        'categories': [{'id': c.id, 'name': c.name} for c in all_categories]
    })


@bp.route('/products/create', methods=['GET', 'POST'])
@login_required
def create_product():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ProductForm()
    form.shop_id.choices = [(s.id, s.name) for s in current_user.shops.all()]

    if form.shop_id.data:
        form.update_categories(form.shop_id.data)
    elif current_user.shops.first():
        form.update_categories(current_user.shops.first().id)

    if form.validate_on_submit():
        image_filename = save_image(form.image.data) if form.image.data else None
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=image_filename,
            shop_id=form.shop_id.data,
            category_id=form.category_id.data,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('marketer.manage_products'))

    return render_template('marketer/create_product.html', form=form)


@bp.route('/products', methods=['GET', 'POST'])
@login_required
def manage_products():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ProductForm()
    form.shop_id.choices = [(s.id, s.name) for s in current_user.shops.all()]

    if form.shop_id.data:
        form.update_categories(form.shop_id.data)
    elif current_user.shops.first():
        form.update_categories(current_user.shops.first().id)

    if form.validate_on_submit():
        image_filename = save_image(form.image.data) if form.image.data else None
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=image_filename,
            shop_id=form.shop_id.data,
            category_id=form.category_id.data,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('marketer.manage_products'))

    products = Product.query.join(Shop).filter(Shop.user_id == current_user.id).all()
    return render_template('marketer/products.html',
                         form=form,
                         products=products)

@bp.route('/shops/create', methods=['GET', 'POST'])
@login_required
def create_shop():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ShopForm()
    if form.validate_on_submit():
        logo_filename = save_image(form.logo.data) if form.logo.data else None
        shop = Shop(
            name=form.name.data,
            description=form.description.data,
            location=form.location.data,
            whatsapp_number=form.whatsapp_number.data,
            logo=logo_filename,
            user_id=current_user.id
        )
        db.session.add(shop)
        db.session.commit()
        flash('Shop created successfully!', 'success')
        return redirect(url_for('marketer.dashboard'))

    return render_template('marketer/create_shop.html', form=form)

@bp.route('/shops/<int:shop_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ShopForm(obj=shop)

    if form.validate_on_submit():
        if isinstance(form.logo.data, FileStorage) and form.logo.data.filename:
            shop.logo = save_image(form.logo.data)
        del form.logo
        form.populate_obj(shop)
        db.session.commit()
        flash('Shop updated successfully!', 'success')
        return redirect(url_for('marketer.dashboard'))

    return render_template('marketer/edit_shop.html', form=form, shop=shop)

@bp.route('/shops/<int:shop_id>/products', methods=['GET', 'POST'])
@login_required
def shop_products(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ProductForm()
    form.shop_id.choices = [(s.id, s.name) for s in current_user.shops.all()]
    form.shop_id.data = shop_id

    form.update_categories(shop_id)

    if form.validate_on_submit():
        image_filename = save_image(form.image.data) if form.image.data else None
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=image_filename,
            shop_id=shop_id,
            category_id=form.category_id.data,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('marketer.shop_products', shop_id=shop_id))

    products = Product.query.filter_by(shop_id=shop_id).all()
    return render_template('marketer/shop_products.html',
                         shop=shop,
                         form=form,
                         products=products)

@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.shop.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ProductForm(obj=product)
    form.shop_id.choices = [(s.id, s.name) for s in current_user.shops.all()]
    form.update_categories(product.shop_id)

    if form.validate_on_submit():
        if isinstance(form.image.data, FileStorage) and form.image.data.filename:
            product.image = save_image(form.image.data)
        del form.image
        product.is_active = form.is_active.data
        form.populate_obj(product)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('marketer.shop_products', shop_id=product.shop_id))

    return render_template('marketer/edit_product.html', form=form, product=product)

@bp.route('/products/<int:product_id>/mark_sold_out', methods=['POST'])
@login_required
def mark_product_sold_out(product_id):
    product = Product.query.get_or_404(product_id)
    if product.shop.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    product.is_active = False
    db.session.commit()
    flash(f'Product "{product.name}" marked as sold out/inactive.', 'success')
    return redirect(url_for('marketer.shop_products', shop_id=product.shop_id))

@bp.route('/products/<int:product_id>/reactivate', methods=['POST'])
@login_required
def reactivate_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.shop.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    product.is_active = True
    db.session.commit()
    flash(f'Product "{product.name}" reactivated and available again.', 'success')
    return redirect(url_for('marketer.shop_products', shop_id=product.shop_id))

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.shop.owner != current_user:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shop_id = product.shop_id
    db.session.delete(product)
    db.session.commit()
    flash('Product permanently deleted.', 'success')
    return redirect(url_for('marketer.shop_products', shop_id=shop_id))


# --- MARKETER ORDER MANAGEMENT ROUTES ---

@bp.route('/orders')
@login_required
def marketer_orders():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    marketer_shop_ids = [shop.id for shop in current_user.shops.all()]

    if not marketer_shop_ids:
        orders = []
    else:
        relevant_order_ids = db.session.query(OrderItem.order_id).filter(
            OrderItem.shop_id.in_(marketer_shop_ids)
        ).distinct().subquery()

        orders = Order.query.filter(Order.id.in_(relevant_order_ids)).order_by(Order.created_at.desc()).all()

    return render_template('marketer/orders.html', orders=orders)

@bp.route('/orders/<int:order_id>')
@login_required
def marketer_order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    marketer_shop_ids = [shop.id for shop in current_user.shops.all()]

    is_marketer_order = False
    for item in order.items:
        if item.shop_id in marketer_shop_ids:
            is_marketer_order = True
            break

    if not is_marketer_order and current_user.role != 'admin':
        flash('Access denied. You do not have permission to view this order.', 'danger')
        return redirect(url_for('marketer.marketer_orders'))

    if current_user.role == 'marketer':
        order_items_for_marketer = [
            item for item in order.items if item.shop_id in marketer_shop_ids
        ]
    else:
        order_items_for_marketer = order.items.all()


    return render_template('marketer/order_detail.html',
                           order=order,
                           order_items_for_marketer=order_items_for_marketer)

@bp.route('/orders/<int:order_id>/update_status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    allowed_statuses = ['Pending', 'Processing', 'Completed', 'Cancelled']
    if new_status not in allowed_statuses:
        flash('Invalid status provided.', 'danger')
        return redirect(url_for('marketer.marketer_order_detail', order_id=order.id))

    marketer_shop_ids = [shop.id for shop in current_user.shops.all()]
    is_marketer_order = any(item.shop_id in marketer_shop_ids for item in order.items)

    if not is_marketer_order and current_user.role != 'admin':
        flash('Access denied. You do not have permission to update this order.', 'danger')
        return redirect(url_for('marketer.marketer_orders'))

    order.status = new_status
    db.session.commit()
    flash(f'Order {order.id} status updated to {new_status}.', 'success')
    return redirect(url_for('marketer.marketer_order_detail', order_id=order.id))

# --- MARKETER PROFILE ROUTES ---

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def marketer_profile():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = ProfileForm(original_username=current_user.username, original_email=current_user.email, obj=current_user)
    change_password_form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('marketer.marketer_profile'))

    return render_template('marketer/profile.html', form=form, change_password_form=change_password_form)

@bp.route('/change_password', methods=['POST'])
@login_required
def change_marketer_password():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    change_password_form = ChangePasswordForm()
    profile_form = ProfileForm(original_username=current_user.username, original_email=current_user.email, obj=current_user)

    if change_password_form.validate_on_submit():
        if not current_user.check_password(change_password_form.old_password.data):
            flash('Incorrect current password.', 'danger')
        else:
            current_user.set_password(change_password_form.new_password.data)
            db.session.commit()
            flash('Your password has been changed!', 'success')
            return redirect(url_for('marketer.marketer_profile'))

    return render_template('marketer/profile.html', form=profile_form, change_password_form=change_password_form)

# NEW ROUTE: Marketer Notifications
@bp.route('/notifications')
@login_required
def marketer_notifications():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    all_notifications = current_user.notifications.order_by(Notification.created_at.desc()).all()
    unread_notifications = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).all()

    return render_template('marketer/notifications.html',
                           all_notifications=all_notifications,
                           unread_notifications=unread_notifications)

# NEW ROUTE: Mark Notification as Read
@bp.route('/notifications/<int:notification_id>/mark_read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    # Ensure the notification belongs to the current user
    if notification.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('marketer.marketer_notifications'))

    notification.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'info')
    return redirect(url_for('marketer.marketer_notifications'))
