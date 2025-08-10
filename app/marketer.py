from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Shop, Product, Category
from app.forms import ShopForm, ProductForm, NewCategoryForm
from app import db
from app.utils import save_image
from werkzeug.datastructures import FileStorage # Import FileStorage to check type

bp = Blueprint('marketer', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shops = current_user.shops.order_by(Shop.created_at.desc()).all()
    
    # --- DIAGNOSTIC START ---
    # This diagnostic code is helpful, but you can remove it once confirmed working.
    # import os
    # for shop in shops:
    #     if shop.logo:
    #         static_folder = os.path.join(bp.root_path, 'static')
    #         uploads_folder = os.path.join(static_folder, 'uploads')
    #         image_filepath = os.path.join(uploads_folder, shop.logo)
    #         print(f"Shop: {shop.name}, Logo Filename in DB: '{shop.logo}'")
    #         print(f"Expected Full Path on Server: '{image_filepath}'")
    #         print(f"Does file exist at this path? {os.path.exists(image_filepath)}")
    #     else:
    #         print(f"Shop: {shop.name}, No Logo in DB.")
    # --- DIAGNOSTIC END ---

    return render_template('marketer/dashboard.html', shops=shops)

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
            category_id=form.category_id.data
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
            category_id=form.category_id.data
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
        # Check if a new logo file was provided AND is actually a file (not just an empty FileStorage)
        if isinstance(form.logo.data, FileStorage) and form.logo.data.filename:
            shop.logo = save_image(form.logo.data)
        # form.populate_obj(shop) will handle other fields, but we explicitly
        # set logo above if a new one was uploaded.
        # To prevent populate_obj from overwriting shop.logo with an empty value
        # if no new file was selected, we can delete it from form.data before populate_obj.
        del form.logo # Remove logo from form data before populating to preserve existing logo if no new file uploaded

        form.populate_obj(shop) # This will populate all other fields

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
            category_id=form.category_id.data
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
        # Check if a new image file was provided AND is actually a file
        if isinstance(form.image.data, FileStorage) and form.image.data.filename:
            product.image = save_image(form.image.data)
        # Prevent populate_obj from overwriting product.image with an empty value
        del form.image # Remove image from form data before populating to preserve existing image

        form.populate_obj(product) # This will populate all other fields

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('marketer.shop_products', shop_id=product.shop_id))

    return render_template('marketer/edit_product.html', form=form, product=product)

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
    flash('Product deleted successfully', 'success')
    return redirect(url_for('marketer.shop_products', shop_id=shop_id))
