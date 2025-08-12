from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Shop, Product, Category
from app.forms import UserForm, CategoryForm, BulkApproveForm, ShopForm
from app import db
from app.utils import save_image
from sqlalchemy import or_
from werkzeug.datastructures import FileStorage

bp = Blueprint('admin', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    users = User.query.all()
    shops = Shop.query.all()
    categories = Category.query.all()
    pending_count = User.query.filter_by(is_approved=False).count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_shops = Shop.query.order_by(Shop.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                         users=users,
                         shops=shops,
                         categories=categories,
                         pending_count=pending_count,
                         recent_users=recent_users,
                         recent_shops=recent_shops)

@bp.route('/users')
@login_required
def user_list():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    users = User.query.all()
    pending_count = User.query.filter_by(is_approved=False).count()
    return render_template('admin/users.html', users=users, pending_count=pending_count)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_approved=form.is_approved.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/create_user.html', form=form)

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_approved = form.is_approved.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/edit_user.html', form=form, user=user)

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('customer.index'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.user_list'))

@bp.route('/shops')
@login_required
def shop_list():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shops = Shop.query.all()
    return render_template('admin/shops.html', shops=shops)

@bp.route('/shops/<int:shop_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shop(shop_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shop = Shop.query.get_or_404(shop_id)
    form = ShopForm(obj=shop)

    if form.validate_on_submit():
        if isinstance(form.logo.data, FileStorage) and form.logo.data.filename:
            shop.logo = save_image(form.logo.data)
        del form.logo
        form.populate_obj(shop)
        db.session.commit()
        flash('Shop updated successfully!', 'success')
        return redirect(url_for('admin.shop_list'))
    return render_template('admin/edit_shop.html', form=form, shop=shop)

@bp.route('/shops/<int:shop_id>/delete', methods=['POST'])
@login_required
def delete_shop(shop_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shop = Shop.query.get_or_404(shop_id)
    db.session.delete(shop)
    db.session.commit()
    flash('Shop deleted successfully.', 'success')
    return redirect(url_for('admin.shop_list'))

@bp.route('/products')
@login_required
def product_list():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.shop_id.choices = [(s.id, s.name) for s in Shop.query.all()]
    form.update_categories(product.shop_id)

    if form.validate_on_submit():
        if isinstance(form.image.data, FileStorage) and form.image.data.filename:
            product.image = save_image(form.image.data)
        del form.image
        form.populate_obj(product)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.product_list'))
    return render_template('admin/edit_product.html', form=form, product=product)

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin.product_list'))

@bp.route('/categories')
@login_required
def manage_categories():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    form = CategoryForm()
    form.shop_id.choices = [(0, 'Global')] + [(s.id, s.name) for s in Shop.query.all()]
    categories = Category.query.all()
    return render_template('admin/categories.html', form=form, categories=categories)

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    form.shop_id.choices = [(0, 'Global')] + [(s.id, s.name) for s in Shop.query.all()]

    if form.validate_on_submit():
        category.name = form.name.data
        category.shop_id = form.shop_id.data if form.shop_id.data != 0 else None
        db.session.commit()
        flash('Category updated successfully.', 'success')
        return redirect(url_for('admin.manage_categories'))
    return render_template('admin/edit_category.html', form=form, category=category)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin.manage_categories'))

@bp.route('/users/pending')
@login_required
def pending_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('customer.index'))

    pending_users = User.query.filter_by(is_approved=False, role='marketer').all()
    form = BulkApproveForm()
    form.user_ids.choices = [(user.id, user.username) for user in pending_users]
    return render_template('admin/pending_users.html', users=pending_users, form=form)

# CRITICAL FIX: Define the approve_user route
@bp.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('customer.index'))

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.username} approved successfully', 'success')
    return redirect(url_for('admin.pending_users'))

# CRITICAL FIX: Define the reject_user route
@bp.route('/reject_user/<int:user_id>')
@login_required
def reject_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('customer.index'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} rejected and deleted', 'success')
    return redirect(url_for('admin.pending_users'))

@bp.route('/users/bulk_action', methods=['POST'])
@login_required
def bulk_user_action():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('customer.index'))

    form = BulkApproveForm()
    pending_users = User.query.filter_by(is_approved=False, role='marketer').all()
    form.user_ids.choices = [(user.id, user.username) for user in pending_users]

    if form.validate_on_submit():
        user_ids = form.user_ids.data
        action = form.action.data

        if not user_ids:
            flash('No users selected for bulk action.', 'warning')
            return redirect(url_for('admin.pending_users'))

        users_to_process = User.query.filter(User.id.in_(user_ids)).all()

        if action == 'approve':
            for user in users_to_process:
                user.is_approved = True
            db.session.commit()
            flash(f'{len(users_to_process)} marketer(s) approved.', 'success')
        elif action == 'reject':
            for user in users_to_process:
                db.session.delete(user)
            db.session.commit()
            flash(f'{len(users_to_process)} marketer(s) rejected and deleted.', 'success')
        else:
            flash('Invalid bulk action.', 'danger')

    return redirect(url_for('admin.pending_users'))
