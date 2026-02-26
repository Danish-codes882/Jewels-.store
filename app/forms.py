"""
Jewelry Store — Forms
======================
All WTForms form classes for both the public store and the admin portal.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, DecimalField,
    IntegerField, SelectField, BooleanField, HiddenField, EmailField
)
from wtforms.validators import (
    DataRequired, Email, Length, Optional, NumberRange, ValidationError
)
from app.models import Admin


# ---------------------------------------------------------------------------
# Admin Auth
# ---------------------------------------------------------------------------

class LoginForm(FlaskForm):
    """Admin login."""
    username = StringField("Username", validators=[DataRequired(), Length(1, 80)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


class ChangePasswordForm(FlaskForm):
    """Admin password change."""
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password     = PasswordField("New Password", validators=[DataRequired(), Length(8, 128)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired()])

    def validate_confirm_password(self, field):
        if field.data != self.new_password.data:
            raise ValidationError("Passwords do not match.")


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class CategoryForm(FlaskForm):
    """Create / edit a product category."""
    name       = StringField("Category Name", validators=[DataRequired(), Length(1, 100)])
    sort_order = IntegerField("Sort Order", validators=[Optional()], default=0)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductForm(FlaskForm):
    """Create / edit a product — all pricing fields included."""
    name             = StringField("Product Name",
                                   validators=[DataRequired(), Length(1, 200)])
    sku              = StringField("SKU / Reference",
                                   validators=[Optional(), Length(max=80)])
    category_id      = SelectField("Category", coerce=int,
                                   validators=[Optional()])
    original_price   = DecimalField("Original / RRP Price",
                                    validators=[DataRequired(), NumberRange(min=0)],
                                    places=2)
    discounted_price = DecimalField("Discounted Selling Price",
                                    validators=[Optional(), NumberRange(min=0)],
                                    places=2)
    deal_price       = DecimalField("Deal / Flash-Sale Price",
                                    validators=[Optional(), NumberRange(min=0)],
                                    places=2)
    description      = TextAreaField("Main Description (HTML supported)",
                                     validators=[DataRequired()])
    stock            = IntegerField("Stock Quantity",
                                    validators=[NumberRange(min=0)], default=0)
    is_active        = BooleanField("Active / Visible on Site", default=True)
    is_deal          = BooleanField("Mark as Deal")
    is_featured      = BooleanField("Feature on Homepage")
    image            = FileField("Main Product Image",
                                 validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "gif"],
                                                         "Images only!")])

    # Extra content blocks — passed as JSON from the JS-powered UI
    extra_content    = HiddenField("Extra Content Blocks (JSON)")


# ---------------------------------------------------------------------------
# Order (admin edit)
# ---------------------------------------------------------------------------

class OrderStatusForm(FlaskForm):
    """Admin form to update order status, tracking, and notes."""
    status          = SelectField("Order Status",
                                  choices=[
                                      ("pending",    "Pending"),
                                      ("confirmed",  "Confirmed"),
                                      ("processing", "Processing"),
                                      ("shipped",    "Shipped"),
                                      ("delivered",  "Delivered"),
                                      ("cancelled",  "Cancelled"),
                                      ("refunded",   "Refunded"),
                                  ])
    tracking_number = StringField("Tracking Number", validators=[Optional(), Length(max=100)])
    admin_notes     = TextAreaField("Internal Notes", validators=[Optional()])


# ---------------------------------------------------------------------------
# Checkout (public)
# ---------------------------------------------------------------------------

class CheckoutForm(FlaskForm):
    """Customer checkout form."""
    customer_name    = StringField("Full Name",
                                   validators=[DataRequired(), Length(1, 150)])
    customer_email   = EmailField("Email Address",
                                  validators=[DataRequired(), Email()])
    customer_phone   = StringField("Phone Number",
                                   validators=[Optional(), Length(max=30)])
    shipping_address = TextAreaField("Shipping Address",
                                     validators=[DataRequired()])
    city             = StringField("City", validators=[Optional(), Length(max=100)])
    postal_code      = StringField("Postal Code", validators=[Optional(), Length(max=20)])
    country          = StringField("Country", validators=[Optional(), Length(max=100)])
    notes            = TextAreaField("Order Notes (optional)",
                                     validators=[Optional()])


# ---------------------------------------------------------------------------
# Site Settings
# ---------------------------------------------------------------------------

class SiteSettingsForm(FlaskForm):
    """Admin site-wide settings."""
    site_name               = StringField("Site Name",
                                          validators=[DataRequired(), Length(1, 100)])
    site_tagline            = StringField("Tagline / Slogan",
                                          validators=[Optional(), Length(max=200)])
    currency_symbol         = StringField("Currency Symbol",
                                          validators=[Optional(), Length(max=5)],
                                          default="$")
    delivery_cost           = DecimalField("Standard Delivery Cost",
                                           validators=[Optional(), NumberRange(min=0)],
                                           places=2, default=5.00)
    free_delivery_threshold = DecimalField("Free Delivery Above (0 = always charged)",
                                           validators=[Optional(), NumberRange(min=0)],
                                           places=2, default=50.00)
    announcement_text       = StringField("Announcement Bar Text",
                                          validators=[Optional(), Length(max=300)])
    contact_email           = StringField("Contact Email",
                                          validators=[Optional(), Email()])
    contact_phone           = StringField("Contact Phone",
                                          validators=[Optional(), Length(max=30)])
    instagram_url           = StringField("Instagram URL",
                                          validators=[Optional(), Length(max=300)])
    facebook_url            = StringField("Facebook URL",
                                          validators=[Optional(), Length(max=300)])
    logo_image              = FileField("Upload Logo",
                                        validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "svg"],
                                                                "Images only!")])
    background_image        = FileField("Upload Hero Background Image",
                                        validators=[FileAllowed(["jpg", "jpeg", "png", "webp"],
                                                                "Images only!")])
