from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer')  # 'admin', 'marketer', 'customer'
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shops = db.relationship('Shop', backref='owner', lazy='dynamic')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='customer', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic') # New: User can have notifications

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def create_default_admin(cls, username, email, password):
        admin = cls.query.filter_by(username=username).first()
        if not admin:
            admin = cls(username=username, email=email, role='admin', is_approved=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    whatsapp_number = db.Column(db.String(20))
    logo = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='shop', lazy='dynamic')
    ratings = db.relationship('Rating', backref='shop', lazy='dynamic')

    order_items = db.relationship('OrderItem', backref='shop_ordered', lazy='dynamic')


    def formatted_whatsapp(self):
        if self.whatsapp_number:
            number = ''.join(filter(str.isdigit, self.whatsapp_number))
            if not number.startswith('234') and len(number) == 10:
                return '234' + number[1:]
            return number
        return ''

    def average_rating(self):
        ratings = [rating.value for rating in self.ratings]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0

    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='unique_shop_per_user'),
    )

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=True)
    products = db.relationship('Product', backref='category', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('name', 'shop_id', name='unique_category_per_shop'),
    )

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ratings = db.relationship('Rating', backref='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='product_ordered', lazy='dynamic')

    def formatted_price(self):
        return f"₦{self.price:,.2f}" if self.price else "₦0.00"

    def average_rating(self):
        ratings = [rating.value for rating in self.ratings]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')

    def formatted_total_price(self):
        return f"₦{self.total_price:,.2f}"

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)

    def subtotal(self):
        return self.quantity * self.price_at_purchase

    def formatted_subtotal(self):
        return f"₦{self.subtotal():,.2f}"

# NEW MODEL: Notification
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # The user who receives the notification
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Optional: link to a specific order or product if needed
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
