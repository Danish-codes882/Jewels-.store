"""
Jewelry Store — Admin Blueprint
=================================
Full admin portal: authentication, product management, order management,
category management, and site-wide settings (logo, background, delivery).
"""

import json
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, abort, current_app,
)
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import Admin, Product, Category, Order, SiteSettings, ORDER_STATUSES
from app.forms import (
    LoginForm, CategoryForm, ProductForm,
    OrderStatusForm, SiteSettingsForm, ChangePasswordForm,
)
from app.utils import slugify, save_image, delete_image, get_settings

admin_bp = Blueprint("admin_bp", __name__, template_folder="../templates/admin")


# ---------------------------------------------------------------------------
# Context processor — inject pending_count into every admin template
# ---------------------------------------------------------------------------

@admin_bp.context_processor
def inject_admin_globals():
    from app.models import Order as Ord
    try:
        pending = Ord.query.filter_by(status="pending").count()
    except Exception:
        pending = 0
    return {"pending_count": pending}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_back(fallback="admin_bp.dashboard"):
    return redirect(request.referrer or url_for(fallback))


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_bp.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.is_active and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember.data)
            admin.last_login = datetime.now(timezone.utc)
            db.session.commit()
            flash(f"Welcome back, {admin.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin_bp.dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_bp.login"))


@admin_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("admin_bp.dashboard"))
    return render_template("admin/change_password.html", form=form)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "total_products":  Product.query.filter_by(is_active=True).count(),
        "total_orders":    Order.query.count(),
        "pending_orders":  Order.query.filter_by(status="pending").count(),
        "total_categories": Category.query.count(),
        "recent_orders":   Order.query.order_by(Order.created_at.desc()).limit(5).all(),
        "low_stock":       Product.query.filter(Product.stock < 5,
                                                 Product.is_active == True).all(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@admin_bp.route("/categories")
@login_required
def categories():
    cats = Category.query.order_by(Category.sort_order, Category.name).all()
    form = CategoryForm()
    return render_template("admin/categories.html", categories=cats, form=form)


@admin_bp.route("/categories/add", methods=["POST"])
@login_required
def category_add():
    form = CategoryForm()
    if form.validate_on_submit():
        slug = slugify(form.name.data)
        # ensure unique slug
        if Category.query.filter_by(slug=slug).first():
            slug = f"{slug}-{Category.query.count() + 1}"
        cat = Category(name=form.name.data,
                       slug=slug,
                       sort_order=form.sort_order.data or 0)
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" created.', "success")
    else:
        for errors in form.errors.values():
            for e in errors:
                flash(e, "danger")
    return redirect(url_for("admin_bp.categories"))


@admin_bp.route("/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{cat.name}" deleted (products unassigned).', "warning")
    return redirect(url_for("admin_bp.categories"))


# ---------------------------------------------------------------------------
# Products — list
# ---------------------------------------------------------------------------

@admin_bp.route("/products")
@login_required
def products():
    q       = request.args.get("q", "").strip()
    cat_id  = request.args.get("category", 0, type=int)
    page    = request.args.get("page", 1, type=int)

    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if cat_id:
        query = query.filter_by(category_id=cat_id)

    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/products.html",
                           products=products,
                           categories=categories,
                           q=q, cat_id=cat_id)


# ---------------------------------------------------------------------------
# Products — add
# ---------------------------------------------------------------------------

@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
def product_add():
    form = ProductForm()
    # Populate category choices
    form.category_id.choices = [(0, "— No Category —")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        slug = slugify(form.name.data)
        if Product.query.filter_by(slug=slug).first():
            slug = f"{slug}-{Product.query.count() + 1}"

        image_path = save_image(form.image.data, "products") if form.image.data else None

        product = Product(
            name             = form.name.data,
            slug             = slug,
            sku              = form.sku.data or None,
            category_id      = form.category_id.data or None,
            original_price   = form.original_price.data,
            discounted_price = form.discounted_price.data or None,
            deal_price       = form.deal_price.data or None,
            description      = form.description.data,
            extra_content    = form.extra_content.data or None,
            stock            = form.stock.data or 0,
            is_active        = form.is_active.data,
            is_deal          = form.is_deal.data,
            is_featured      = form.is_featured.data,
            image            = image_path,
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" created successfully.', "success")
        return redirect(url_for("admin_bp.products"))

    return render_template("admin/product_form.html", form=form, product=None)


# ---------------------------------------------------------------------------
# Products — edit
# ---------------------------------------------------------------------------

@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    form    = ProductForm(obj=product)
    form.category_id.choices = [(0, "— No Category —")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]

    if request.method == "GET":
        form.category_id.data = product.category_id or 0

    if form.validate_on_submit():
        # Handle image replacement
        if form.image.data:
            delete_image(product.image)
            product.image = save_image(form.image.data, "products")

        product.name             = form.name.data
        product.sku              = form.sku.data or None
        product.category_id      = form.category_id.data or None
        product.original_price   = form.original_price.data
        product.discounted_price = form.discounted_price.data or None
        product.deal_price       = form.deal_price.data or None
        product.description      = form.description.data
        product.extra_content    = form.extra_content.data or None
        product.stock            = form.stock.data or 0
        product.is_active        = form.is_active.data
        product.is_deal          = form.is_deal.data
        product.is_featured      = form.is_featured.data

        db.session.commit()
        flash(f'Product "{product.name}" updated.', "success")
        return redirect(url_for("admin_bp.products"))

    return render_template("admin/product_form.html", form=form, product=product)


# ---------------------------------------------------------------------------
# Products — toggle active / deal / featured (AJAX-friendly POST)
# ---------------------------------------------------------------------------

@admin_bp.route("/products/toggle/<int:product_id>/<field>", methods=["POST"])
@login_required
def product_toggle(product_id, field):
    product = Product.query.get_or_404(product_id)
    allowed = {"is_active", "is_deal", "is_featured"}
    if field not in allowed:
        abort(400)
    setattr(product, field, not getattr(product, field))
    db.session.commit()
    return redirect(_redirect_back("admin_bp.products"))


# ---------------------------------------------------------------------------
# Products — delete
# ---------------------------------------------------------------------------

@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    delete_image(product.image)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted.', "warning")
    return redirect(url_for("admin_bp.products"))


# ---------------------------------------------------------------------------
# Orders — list
# ---------------------------------------------------------------------------

@admin_bp.route("/orders")
@login_required
def orders():
    status = request.args.get("status", "")
    page   = request.args.get("page", 1, type=int)
    q      = request.args.get("q", "").strip()

    query = Order.query
    if status and status in ORDER_STATUSES:
        query = query.filter_by(status=status)
    if q:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f"%{q}%"),
                Order.customer_name.ilike(f"%{q}%"),
                Order.customer_email.ilike(f"%{q}%"),
            )
        )

    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/orders.html",
                           orders=orders,
                           active_status=status,
                           statuses=ORDER_STATUSES,
                           q=q)


# ---------------------------------------------------------------------------
# Orders — detail / edit
# ---------------------------------------------------------------------------

@admin_bp.route("/orders/<int:order_id>", methods=["GET", "POST"])
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    form  = OrderStatusForm(obj=order)

    if form.validate_on_submit():
        order.status          = form.status.data
        order.tracking_number = form.tracking_number.data
        order.admin_notes     = form.admin_notes.data
        db.session.commit()
        flash("Order updated.", "success")
        return redirect(url_for("admin_bp.order_detail", order_id=order.id))

    return render_template("admin/order_detail.html",
                           order=order, form=form, statuses=ORDER_STATUSES)


# ---------------------------------------------------------------------------
# Orders — delete
# ---------------------------------------------------------------------------

@admin_bp.route("/orders/delete/<int:order_id>", methods=["POST"])
@login_required
def order_delete(order_id):
    order = Order.query.get_or_404(order_id)
    num   = order.order_number
    db.session.delete(order)
    db.session.commit()
    flash(f"Order {num} deleted.", "warning")
    return redirect(url_for("admin_bp.orders"))


# ---------------------------------------------------------------------------
# Site Settings
# ---------------------------------------------------------------------------

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    cfg  = get_settings()
    form = SiteSettingsForm()

    if request.method == "GET":
        form.site_name.data               = cfg.get("site_name", "")
        form.site_tagline.data            = cfg.get("site_tagline", "")
        form.currency_symbol.data         = cfg.get("currency_symbol", "$")
        form.delivery_cost.data           = float(cfg.get("delivery_cost", 5))
        form.free_delivery_threshold.data = float(cfg.get("free_delivery_threshold", 50))
        form.announcement_text.data       = cfg.get("announcement_text", "")
        form.contact_email.data           = cfg.get("contact_email", "")
        form.contact_phone.data           = cfg.get("contact_phone", "")
        form.instagram_url.data           = cfg.get("instagram_url", "")
        form.facebook_url.data            = cfg.get("facebook_url", "")

    if form.validate_on_submit():
        # Text fields
        text_fields = [
            "site_name", "site_tagline", "currency_symbol",
            "announcement_text", "contact_email", "contact_phone",
            "instagram_url", "facebook_url",
        ]
        for field_name in text_fields:
            SiteSettings.set(field_name, getattr(form, field_name).data or "")

        SiteSettings.set("delivery_cost",
                         str(form.delivery_cost.data or "0"))
        SiteSettings.set("free_delivery_threshold",
                         str(form.free_delivery_threshold.data or "0"))

        # Logo upload
        if form.logo_image.data and form.logo_image.data.filename:
            old = SiteSettings.get("logo_image")
            delete_image(old)
            path = save_image(form.logo_image.data, "site", 400, 400)
            if path:
                SiteSettings.set("logo_image", path)

        # Background image upload
        if form.background_image.data and form.background_image.data.filename:
            old = SiteSettings.get("background_image")
            delete_image(old)
            path = save_image(form.background_image.data, "site", 2000, 2000)
            if path:
                SiteSettings.set("background_image", path)

        flash("Site settings saved.", "success")
        return redirect(url_for("admin_bp.settings"))

    return render_template("admin/settings.html",
                           form=form, settings=cfg)
