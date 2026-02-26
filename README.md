# 💎 Jewelry Store — Full-Stack Flask Application

A complete, production-ready e-commerce store for a jewelry business.
Built with Flask, SQLAlchemy, Bootstrap 5, and Quill.js.

---

## Project Structure

```
jewelry_store/
├── run.py                    ← Application entry point
├── create_admin.py           ← One-time admin user creation script
├── requirements.txt          ← Python dependencies
├── .env                      ← Environment variables (edit before launch)
└── app/
    ├── __init__.py           ← App factory, extension init, DB seeding
    ├── models.py             ← All database models
    ├── forms.py              ← All WTForms form classes
    ├── utils.py              ← Slugify, image save, cart helpers
    ├── main.py               ← Public store blueprint (routes)
    ├── admin.py              ← Admin portal blueprint (routes)
    ├── static/
    │   ├── css/
    │   │   ├── style.css     ← Public store styles (gold/dark theme)
    │   │   └── admin.css     ← Admin panel styles
    │   ├── js/
    │   │   └── main.js       ← Public JS (cart, scroll effects)
    │   └── uploads/          ← User-uploaded images (auto-created)
    │       ├── products/
    │       └── site/
    └── templates/
        ├── base.html         ← Public base layout
        ├── index.html        ← Homepage (hero, deals, featured, grid)
        ├── _product_card.html ← Reusable product card partial
        ├── product_detail.html ← Product page
        ├── cart.html         ← Shopping cart
        ├── checkout.html     ← Checkout form
        ├── order_confirmation.html ← Thank you page
        └── admin/
            ├── base_admin.html     ← Admin sidebar layout
            ├── login.html          ← Admin login
            ├── dashboard.html      ← Stats + recent orders
            ├── products.html       ← Product list with toggles
            ├── product_form.html   ← Add/edit product (Quill editor)
            ├── orders.html         ← Orders list + filter
            ├── order_detail.html   ← Order view + status update
            ├── categories.html     ← Category management
            ├── settings.html       ← Site settings, logo, background
            └── change_password.html
```

---

## Quick Start

### 1. Install dependencies

```bash
cd jewelry_store
pip install -r requirements.txt
```

> **Python 3.14 note:** All packages use `>=` version constraints.
> If any install fails, try: `pip install --pre <package>`.

### 2. Configure environment

Edit `.env`:
```env
SECRET_KEY=your-long-random-secret-key
DATABASE_URL=sqlite:///jewelry_store.db
FLASK_ENV=development
```

For production, use a PostgreSQL URL:
```env
DATABASE_URL=postgresql://user:password@host:5432/jewelry_db
```

### 3. Create the database and first admin

```bash
python run.py          # This auto-creates all tables on first run
python create_admin.py # Interactive admin user creation
```

### 4. Run the development server

```bash
python run.py
```

- **Store**: http://localhost:5000/
- **Admin**: http://localhost:5000/admin/login

---

## Features

### Public Store
| Feature | Details |
|---------|---------|
| Hero section | Full-bleed background image set via admin |
| Product grid | Pagination, category filter, search |
| Product detail | Gallery, all price tiers, qty stepper, related products |
| Deals section | Auto-populated from products marked `is_deal` |
| Featured section | Products marked `is_featured` |
| Cart | Session-based, quantity update, remove |
| Checkout | Full customer details form, delivery calculation |
| Order confirmation | Order summary with all details |
| Responsive | Mobile-first Bootstrap 5 layout |

### Admin Portal
| Feature | Details |
|---------|---------|
| Secure login | bcrypt passwords, CSRF protection, remember me |
| Dashboard | Live stats, recent orders, low-stock alerts |
| Products | Add, edit, delete, toggle active/deal/featured per row |
| Rich descriptions | Quill WYSIWYG editor for main description |
| Extra content | Unlimited additional content sections per product |
| Pricing | 3 price tiers: Original, Discounted, Deal |
| Categories | Add/delete with product count, auto-slug |
| Orders | Status filter, search, full detail view, status updates |
| Order tracking | Add tracking numbers, internal admin notes |
| Site settings | Site name, tagline, currency symbol |
| Logo upload | Upload/replace logo image |
| Background image | Upload/replace hero background image |
| Delivery pricing | Set flat fee and free delivery threshold |
| Announcement bar | Scrolling banner text |
| Social links | Instagram + Facebook footer links |
| Change password | Secure password change for logged-in admin |

### Product Pricing Model
```
original_price    → RRP / "was" price (shown with strikethrough)
discounted_price  → Current selling price
deal_price        → Flash deal price (overrides discounted when set;
                    product appears in Deals section)
```

---

## Database Models

| Model | Purpose |
|-------|---------|
| `Admin` | Admin users (multiple supported) |
| `Category` | Product categories with slugs |
| `Product` | Products with all 3 price tiers + rich content |
| `Order` | Customer orders with full shipping details |
| `OrderItem` | Line items (snapshot prices for history) |
| `SiteSettings` | Key-value store for all configuration |

---

## Adding Your Background Image

1. Log in to `/admin`
2. Go to **Site Settings**
3. Upload your image under **Hero Background Image**
4. Save — it appears immediately on the homepage hero

---

## Production Deployment

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

Set in `.env`:
```env
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
```
