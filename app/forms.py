from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField, # Import BooleanField
    SubmitField,
    TextAreaField,
    SelectField,
    FloatField,
    FileField,
    IntegerField,
    SelectMultipleField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
from flask_wtf.file import FileAllowed
from app.models import Category, User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                         validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    role = SelectField('Register As',
                       choices=[('customer', 'Customer'), ('marketer', 'Marketer')],
                       validators=[DataRequired()])
    password = PasswordField('Password',
                           validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')


class UserForm(FlaskForm):
    username = StringField('Username',
                         validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                           validators=[Length(min=6), Optional()])
    role = SelectField('Role',
                     choices=[('admin', 'Admin'), ('marketer', 'Marketer'), ('customer', 'Customer')],
                     validators=[DataRequired()])
    is_approved = BooleanField('Approved')
    submit = SubmitField('Save')

class BulkApproveForm(FlaskForm):
    user_ids = SelectMultipleField('Select Users', coerce=int)
    action = SelectField('Action',
                       choices=[('approve', 'Approve Selected'),
                               ('reject', 'Reject Selected')],
                       validators=[DataRequired()])
    submit = SubmitField('Submit')

class ShopForm(FlaskForm):
    name = StringField('Shop Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    whatsapp_number = StringField('WhatsApp Number', validators=[DataRequired(), Length(max=20)])
    logo = FileField('Shop Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Save')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Product Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    is_active = BooleanField('Product is Active (Visible to Customers)') # NEW: is_active field
    shop_id = SelectField('Shop', coerce=int, validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Product')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = []

    def update_categories(self, shop_id):
        self.category_id.choices = [(c.id, c.name) for c in
                                  Category.query.filter_by(shop_id=shop_id).all()]

class CategoryForm(FlaskForm):
    name = StringField('Category Name',
                      validators=[DataRequired(), Length(max=50)])
    shop_id = SelectField('Shop', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class NewCategoryForm(FlaskForm):
    name = StringField('New Category Name', validators=[DataRequired(), Length(max=50)])
    shop_id = SelectField('Shop', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Category')

class RatingForm(FlaskForm):
    value = IntegerField('Rating (1-5)',
                        validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment',
                          validators=[Length(max=500)])
    submit = SubmitField('Submit Review')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user:
                raise ValidationError('That email is already registered. Please choose a different one.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
