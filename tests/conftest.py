"""Pytest configuration and fixtures."""
import pytest
from app import create_app
from app.models import db, Product, Order


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # Zamyka wszystkie połączenia z bazą


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture
def sample_product(app):
    """Create a sample product for testing."""
    with app.app_context():
        product = Product(name='Test Product', price=99.99, stock=10)
        db.session.add(product)
        db.session.commit()
        product_id = product.id
    return product_id


@pytest.fixture
def sample_products(app):
    """Create multiple sample products for testing."""
    with app.app_context():
        products = [
            Product(name='Laptop', price=2500.00, stock=5),
            Product(name='Mouse', price=50.00, stock=20),
            Product(name='Keyboard', price=150.00, stock=0),  # Out of stock
        ]
        for p in products:
            db.session.add(p)
        db.session.commit()
        return [p.id for p in products]


@pytest.fixture
def sample_order(app, sample_product):
    """Create a sample order for testing."""
    with app.app_context():
        product = Product.query.get(sample_product)
        order = Order(
            customer_name='Jan Kowalski',
            customer_email='jan@example.com',
            status=Order.STATUS_PENDING
        )
        db.session.add(order)
        db.session.commit()
        return order.id
