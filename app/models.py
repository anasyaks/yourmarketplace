from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer')
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shops = db.relationship('Shop', backref='owner', lazy='dynamic')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic')

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
    logo = db.Column(db.String(100), nullable=True) # <--- Ensure nullable=True
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='shop', lazy='dynamic')
    ratings = db.relationship('Rating', backref='shop', lazy='dynamic')

    def formatted_whatsapp(self):
        # Remove non-numeric characters and add international prefix if not present
        if self.whatsapp_number:
            number = ''.join(filter(str.isdigit, self.whatsapp_number))
            if not number.startswith('234') and len(number) == 10: # Assuming Nigerian numbers
                return '234' + number[1:] # Replace leading 0 with 234
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
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=True) # Category can be global or shop-specific
    products = db.relationship('Product', backref='category', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('name', 'shop_id', name='unique_category_per_shop'),
    )

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image = db.Column(db.String(100), nullable=True) # <--- Ensure nullable=True
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True) # Product can be uncategorized
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ratings = db.relationship('Rating', backref='product', lazy='dynamic')

    def formatted_price(self):
        """Format price as Nigerian Naira"""
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
