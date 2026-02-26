"""
Jewelry Store — Public (Main) Blueprint
=========================================
All customer-facing routes: homepage, product detail, cart, checkout,
order confirmation.
"""

from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, \
    request, flash, abort, session
from app.models import Product, Category, Order, OrderItem, SiteSettings
from app.forms import CheckoutForm
from app.utils import (
    get_cart, add_to_cart, update_cart, remove_from_cart,
    clear_cart, cart_totals, get_settings,
)
from app import db

main_bp = Blueprint("main_bp", __name__)


# ---------------------------------------------------------------------------
# Context processor — injects settings + cart count into every template
# ---------------------------------------------------------------------------

@main_bp.context_processor
def inject_globals():
    settings = get_settings()
    cart = get_cart()
    cart_count = sum(v["qty"] for v in cart.values())
    return {"settings": settings, "cart_count": cart_count}


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------

@main_bp.route("/")
def index():
    settings   = get_settings()
    categories = Category.query.order_by(Category.sort_order).all()

    # Featured products
    featured = (Product.query
                .filter_by(is_active=True, is_featured=True)
                .order_by(Product.created_at.desc())
                .limit(8).all())

    # Current deals
    deals = (Product.query
             .filter_by(is_active=True, is_deal=True)
             .order_by(Product.created_at.desc())
             .limit(8).all())

    # All active products for the grid (paginated)
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category", "")
    search_query  = request.args.get("q", "").strip()

    products_query = Product.query.filter_by(is_active=True)

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            products_query = products_query.filter_by(category_id=cat.id)

    if search_query:
        products_query = products_query.filter(
            Product.name.ilike(f"%{search_query}%")
        )

    products = products_query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    return render_template(
        "index.html",
        settings=settings,
        categories=categories,
        featured=featured,
        deals=deals,
        products=products,
        active_category=category_slug,
        search_query=search_query,
    )


# ---------------------------------------------------------------------------
# Product Detail
# ---------------------------------------------------------------------------

@main_bp.route("/product/<slug>")
def product_detail(slug):
    product  = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    settings = get_settings()

    # Related products — same category, exclude current
    related = []
    if product.category_id:
        related = (Product.query
                   .filter_by(category_id=product.category_id, is_active=True)
                   .filter(Product.id != product.id)
                   .limit(4).all())

    return render_template(
        "product_detail.html",
        product=product,
        related=related,
        settings=settings,
    )


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

@main_bp.route("/cart")
def cart():
    settings = get_settings()
    cart_data = get_cart()
    totals = cart_totals(
        settings.get("delivery_cost", "5.00"),
        settings.get("free_delivery_threshold", "50.00"),
    )
    return render_template("cart.html", cart=cart_data,
                           totals=totals, settings=settings)


@main_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    product = Product.query.get_or_404(product_id)
    qty = int(request.form.get("qty", 1))
    add_to_cart(product.id, product.name,
                product.active_price, product.image or "", qty)
    flash(f'"{product.name}" added to your cart.', "success")
    return redirect(request.referrer or url_for("main_bp.index"))


@main_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def cart_update(product_id):
    qty = int(request.form.get("qty", 0))
    update_cart(product_id, qty)
    flash("Cart updated.", "info")
    return redirect(url_for("main_bp.cart"))


@main_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def cart_remove(product_id):
    remove_from_cart(product_id)
    flash("Item removed from cart.", "info")
    return redirect(url_for("main_bp.cart"))


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

@main_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    settings  = get_settings()
    cart_data = get_cart()

    if not cart_data:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main_bp.index"))

    totals = cart_totals(
        settings.get("delivery_cost", "5.00"),
        settings.get("free_delivery_threshold", "50.00"),
    )
    form = CheckoutForm()

    if form.validate_on_submit():
        # Build order
        order = Order(
            order_number     = Order.generate_order_number(),
            customer_name    = form.customer_name.data,
            customer_email   = form.customer_email.data,
            customer_phone   = form.customer_phone.data,
            shipping_address = form.shipping_address.data,
            city             = form.city.data,
            postal_code      = form.postal_code.data,
            country          = form.country.data,
            notes            = form.notes.data,
            subtotal         = totals["subtotal"],
            delivery_cost    = totals["delivery"],
            total_amount     = totals["total"],
        )
        db.session.add(order)
        db.session.flush()  # get order.id before adding items

        for pid_str, item in cart_data.items():
            product = db.session.get(Product, int(pid_str))
            oi = OrderItem(
                order_id     = order.id,
                product_id   = product.id if product else None,
                product_name = item["name"],
                product_sku  = product.sku if product else None,
                unit_price   = Decimal(item["price"]),
                quantity     = item["qty"],
                line_total   = Decimal(item["price"]) * item["qty"],
            )
            db.session.add(oi)

            # Decrement stock if tracked
            if product and product.stock > 0:
                product.stock = max(0, product.stock - item["qty"])

        db.session.commit()
        clear_cart()

        return redirect(url_for("main_bp.order_confirmation",
                                order_number=order.order_number))

    return render_template(
        "checkout.html",
        form=form,
        cart=cart_data,
        totals=totals,
        settings=settings,
    )


# ---------------------------------------------------------------------------
# Order Confirmation
# ---------------------------------------------------------------------------

@main_bp.route("/order-confirmation/<order_number>")
def order_confirmation(order_number):
    order    = Order.query.filter_by(order_number=order_number).first_or_404()
    settings = get_settings()
    return render_template("order_confirmation.html",
                           order=order, settings=settings)
