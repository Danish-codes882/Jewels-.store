"""
Jewelry Store — Application Entry Point
=========================================
Run with:  python run.py
Or:        flask --app run run --debug
"""

from app import create_app, db
from app.models import Admin, Product, Category, Order, OrderItem, SiteSettings

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Expose all models in `flask shell` for easy debugging."""
    return {
        "db":           db,
        "Admin":        Admin,
        "Product":      Product,
        "Category":     Category,
        "Order":        Order,
        "OrderItem":    OrderItem,
        "SiteSettings": SiteSettings,
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
