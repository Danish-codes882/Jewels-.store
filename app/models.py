"""
Jewelry Store — Database Models
================================
All SQLAlchemy ORM models are defined here to keep the codebase minimal.

Models
------
- Admin          : Admin portal users (supports multiple admins)
- Category       : Product categories
- Product        : Store products with full pricing fields
- Order          : Customer orders
- OrderItem      : Individual line-items within an order
- SiteSettings   : Key-value store for all site-wide configuration
"""

from datetime import datetime, timezone
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# ---------------------------------------------------------------------------
# Admin user (authentication)
# ---------------------------------------------------------------------------

class Admin(UserMixin, db.Model):
    """Admin portal user — can manage all store content."""
    __tablename__ = "admins"

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active    = db.Column(db.Boolean, default=True, nullable=False)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login   = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.username}>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(Admin, int(user_id))


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class Category(db.Model):
    """Product category — e.g. Rings, Necklaces, Bracelets."""
    __tablename__ = "categories"

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), unique=True, nullable=False)
    slug     = db.Column(db.String(100), unique=True, nullable=False, index=True)
    sort_order = db.Column(db.Integer, default=0)

    products = db.relationship("Product", back_populates="category",
                               lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class Product(db.Model):
    """
    A store product.

    Pricing fields
    --------------
    original_price    : The "was" / RRP price shown with a strikethrough.
    discounted_price  : The current selling price.
    deal_price        : Optional flash-deal / limited-time price.
                        When set, it is shown as the active price and the
                        item appears in the Deals section.

    Description
    -----------
    description       : Main description (supports HTML for rich content).
    extra_content     : Additional rich content blocks stored as JSON list of
                        {"heading": str, "body": str} dicts, rendered below
                        the main description — allows unlimited extra sections.
    """
    __tablename__ = "products"

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(200), nullable=False)
    slug              = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category_id       = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    sku               = db.Column(db.String(80), unique=True, nullable=True)

    # Pricing
    original_price    = db.Column(db.Numeric(10, 2), nullable=False)
    discounted_price  = db.Column(db.Numeric(10, 2), nullable=True)
    deal_price        = db.Column(db.Numeric(10, 2), nullable=True)

    # Content
    description       = db.Column(db.Text, nullable=False, default="")
    extra_content     = db.Column(db.Text, nullable=True)  # JSON string

    # Media
    image             = db.Column(db.String(300), nullable=True)
    gallery           = db.Column(db.Text, nullable=True)  # JSON list of filenames

    # Status flags
    is_active         = db.Column(db.Boolean, default=True, nullable=False)
    is_deal           = db.Column(db.Boolean, default=False, nullable=False)
    is_featured       = db.Column(db.Boolean, default=False, nullable=False)
    stock             = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at        = db.Column(db.DateTime,
                                  default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category          = db.relationship("Category", back_populates="products")
    order_items       = db.relationship("OrderItem", back_populates="product",
                                        lazy="dynamic")

    @property
    def active_price(self):
        """Returns the best (lowest) price currently applicable."""
        if self.deal_price:
            return self.deal_price
        if self.discounted_price:
            return self.discounted_price
        return self.original_price

    @property
    def discount_percent(self):
        """Percentage saved vs original price (rounded int)."""
        if self.original_price and self.active_price < self.original_price:
            saving = (self.original_price - self.active_price) / self.original_price
            return int(saving * 100)
        return 0

    def get_extra_content(self):
        """Return extra_content parsed from JSON, or empty list."""
        import json
        if self.extra_content:
            try:
                return json.loads(self.extra_content)
            except (ValueError, TypeError):
                return []
        return []

    def __repr__(self):
        return f"<Product {self.name}>"


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

ORDER_STATUSES = [
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    "refunded",
]


class Order(db.Model):
    """A customer order."""
    __tablename__ = "orders"

    id               = db.Column(db.Integer, primary_key=True)
    order_number     = db.Column(db.String(20), unique=True, nullable=False, index=True)
    status           = db.Column(db.String(30), default="pending", nullable=False)

    # Customer details
    customer_name    = db.Column(db.String(150), nullable=False)
    customer_email   = db.Column(db.String(150), nullable=False)
    customer_phone   = db.Column(db.String(30), nullable=True)
    shipping_address = db.Column(db.Text, nullable=False)
    city             = db.Column(db.String(100), nullable=True)
    postal_code      = db.Column(db.String(20), nullable=True)
    country          = db.Column(db.String(100), nullable=True)

    # Financials
    subtotal         = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_cost    = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount_amount  = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount     = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Extra info
    notes            = db.Column(db.Text, nullable=True)
    admin_notes      = db.Column(db.Text, nullable=True)
    tracking_number  = db.Column(db.String(100), nullable=True)

    # Timestamps
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at       = db.Column(db.DateTime,
                                 default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    items            = db.relationship("OrderItem", back_populates="order",
                                       cascade="all, delete-orphan", lazy="joined")

    @staticmethod
    def generate_order_number():
        """Generate a unique order number like ORD-20240115-0042."""
        from datetime import date
        import random
        today = date.today().strftime("%Y%m%d")
        rand  = random.randint(1000, 9999)
        return f"ORD-{today}-{rand}"

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    """A single line-item inside an order."""
    __tablename__ = "order_items"

    id           = db.Column(db.Integer, primary_key=True)
    order_id     = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id   = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)

    # Snapshot — stored so history survives product edits / deletion
    product_name = db.Column(db.String(200), nullable=False)
    product_sku  = db.Column(db.String(80), nullable=True)
    unit_price   = db.Column(db.Numeric(10, 2), nullable=False)
    quantity     = db.Column(db.Integer, nullable=False, default=1)
    line_total   = db.Column(db.Numeric(10, 2), nullable=False)

    order        = db.relationship("Order", back_populates="items")
    product      = db.relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"


# ---------------------------------------------------------------------------
# Site Settings (key → value store)
# ---------------------------------------------------------------------------

class SiteSettings(db.Model):
    """
    Flexible key-value store for all site-wide configuration.
    Admin panel reads and writes rows here.  Frontend helpers read them.
    """
    __tablename__ = "site_settings"

    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default="")

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        row = cls.query.filter_by(key=key).first()
        return row.value if row else default

    @classmethod
    def set(cls, key: str, value: str) -> None:
        row = cls.query.filter_by(key=key).first()
        if row:
            row.value = value
        else:
            db.session.add(cls(key=key, value=value))
        db.session.commit()

    def __repr__(self):
        return f"<SiteSettings {self.key}={self.value[:40]}>"
