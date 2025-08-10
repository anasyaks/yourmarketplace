from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Shop, Product, Category, Rating
from app.forms import RatingForm
from app import db

bp = Blueprint('customer', __name__)

@bp.route('/')
def index():
    categories = Category.query.all()
    featured_shops = Shop.query.order_by(Shop.created_at.desc()).limit(8).all()
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    return render_template('customer/index.html',
                         categories=categories,
                         featured_shops=featured_shops,
                         featured_products=featured_products)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'marketer':
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.index'))

    shops = current_user.shops.order_by(Shop.created_at.desc()).all()
    return render_template('marketer/dashboard.html', shops=shops)

@bp.route('/shops')
def shop_list():
    category_id = request.args.get('category_id')
    location = request.args.get('location')
    query = request.args.get('q')

    shops_query = Shop.query

    if category_id:
        shops_query = shops_query.join(Product).filter(Product.category_id == category_id)

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
        products = Product.query.filter_by(shop_id=shop.id, category_id=category.id).all()
        if products:
            products_by_category[category.name] = products

    uncategorized = Product.query.filter_by(shop_id=shop.id, category_id=None).all()
    if uncategorized:
        products_by_category['Uncategorized'] = uncategorized

    avg_rating = shop.average_rating()
    rating_count = shop.ratings.count()

    return render_template('customer/shop_detail.html',
                         shop=shop,
                         products_by_category=products_by_category,
                         products_count=len(Product.query.filter_by(shop_id=shop.id).all()),
                         avg_rating=avg_rating,
                         rating_count=rating_count)

@bp.route('/product/<int:product_id>/rate', methods=['POST'])
@login_required
def rate_product(product_id):
    product = Product.query.get_or_404(product_id)
    rating_value = request.form.get('rating', type=int)
    comment_text = request.form.get('comment', '').strip() # Get the comment text

    if rating_value is None or not (1 <= rating_value <= 5):
        flash('Invalid rating value. Please select a rating between 1 and 5 stars.', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))

    existing_rating = Rating.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()

    if existing_rating:
        existing_rating.value = rating_value
        existing_rating.comment = comment_text if comment_text else None # Update comment
    else:
        rating = Rating(
            value=rating_value,
            comment=comment_text if comment_text else None, # Save the comment
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
    query = request.args.get('q')
    if not query:
        return redirect(url_for('customer.index'))

    products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    shops = Shop.query.filter(Shop.name.ilike(f'%{query}%')).all()
    return render_template('customer/search_results.html',
                         query=query,
                         products=products,
                         shops=shops)
