"""
Jewelry Store — Utility Helpers
=================================
Shared functions used by both blueprints:
  - slugify()         : Convert a name to a URL-safe slug
  - save_image()      : Validate, resize, and save an uploaded image file
  - cart helpers      : Read / write the session-based shopping cart
  - get_settings()    : Fetch all SiteSettings as a plain dict for templates
"""

import os
import re
import uuid
from decimal import Decimal

from flask import session, current_app
from PIL import Image


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Return a URL-safe, lowercase, hyphenated slug from arbitrary text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "svg"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file_storage, subfolder: str = "products",
               max_width: int = 1200, max_height: int = 1200) -> str | None:
    """
    Save an uploaded FileStorage object.

    - Generates a UUID filename to prevent collisions.
    - Resizes images larger than max_width × max_height (preserves aspect ratio).
    - Returns the relative path from /static (e.g. 'uploads/products/abc.jpg')
      or None if file_storage is empty.
    """
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    if ext in {"svg"}:
        # SVGs are XML — just save without Pillow processing
        file_storage.save(filepath)
    else:
        img = Image.open(file_storage.stream)
        img = img.convert("RGBA") if ext == "png" else img.convert("RGB")
        img.thumbnail((max_width, max_height), Image.LANCZOS)
        img.save(filepath, optimize=True, quality=88)

    return f"uploads/{subfolder}/{filename}"


def delete_image(relative_path: str) -> None:
    """Delete a previously saved image from disk (silently ignores missing files)."""
    if not relative_path:
        return
    full_path = os.path.join(current_app.root_path, "static", relative_path)
    if os.path.isfile(full_path):
        os.remove(full_path)


# ---------------------------------------------------------------------------
# Shopping cart (session-based)
# ---------------------------------------------------------------------------

CART_SESSION_KEY = "cart"


def get_cart() -> dict:
    """Return the cart dict from the session, creating it if absent.
    Structure: { "product_id_str": { "name", "price", "qty", "image" } }
    """
    return session.setdefault(CART_SESSION_KEY, {})


def add_to_cart(product_id: int, name: str, price: Decimal,
                image: str, qty: int = 1) -> None:
    """Add or increase quantity of a product in the session cart."""
    cart = get_cart()
    key = str(product_id)
    if key in cart:
        cart[key]["qty"] += qty
    else:
        cart[key] = {
            "name":  name,
            "price": str(price),   # Decimal → str for JSON serialisation
            "image": image or "",
            "qty":   qty,
        }
    session.modified = True


def update_cart(product_id: int, qty: int) -> None:
    """Set exact quantity; removes item if qty <= 0."""
    cart = get_cart()
    key = str(product_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        if key in cart:
            cart[key]["qty"] = qty
    session.modified = True


def remove_from_cart(product_id: int) -> None:
    """Remove an item from the cart."""
    cart = get_cart()
    cart.pop(str(product_id), None)
    session.modified = True


def clear_cart() -> None:
    """Empty the cart."""
    session[CART_SESSION_KEY] = {}
    session.modified = True


def cart_totals(delivery_cost_str: str, free_threshold_str: str) -> dict:
    """
    Compute subtotal, delivery, and grand total for the current cart.
    Returns a dict with: subtotal, delivery, total, item_count.
    """
    cart = get_cart()
    subtotal = sum(Decimal(v["price"]) * v["qty"] for v in cart.values())
    delivery = Decimal(delivery_cost_str or "0")
    threshold = Decimal(free_threshold_str or "0")
    if threshold > 0 and subtotal >= threshold:
        delivery = Decimal("0")
    item_count = sum(v["qty"] for v in cart.values())
    return {
        "subtotal":   subtotal,
        "delivery":   delivery,
        "total":      subtotal + delivery,
        "item_count": item_count,
    }


# ---------------------------------------------------------------------------
# Site settings convenience loader
# ---------------------------------------------------------------------------

def get_settings() -> dict:
    """Return all SiteSettings as a plain dict (used in template context)."""
    from app.models import SiteSettings
    return {row.key: row.value for row in SiteSettings.query.all()}
