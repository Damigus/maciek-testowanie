"""
Unit tests - testują izolowaną logikę biznesową modeli.

Te testy weryfikują poprawność metod modeli bez zależności od bazy danych.
Są najszybsze i najbardziej stabilne.
"""
import pytest
from app import create_app
from app.models import db, Product, Order, OrderItem


class TestProductModel:
    """Testy jednostkowe modelu Product."""
    
    def test_product_is_available_with_sufficient_stock(self, app):
        """
        TEST 1: Sprawdzenie dostępności produktu gdy jest wystarczający stan magazynowy.
        
        UZASADNIENIE BIZNESOWE:
        System musi poprawnie weryfikować czy produkt może być zamówiony.
        Gdy klient chce kupić 3 sztuki a mamy 10, produkt powinien być dostępny.
        """
        with app.app_context():
            product = Product(name='Test', price=10.0, stock=10)
            
            assert product.is_available(3) is True
            assert product.is_available(10) is True
    
    def test_product_is_not_available_with_insufficient_stock(self, app):
        """
        TEST 2: Sprawdzenie niedostępności produktu gdy brak towaru.
        
        UZASADNIENIE BIZNESOWE:
        System musi zapobiegać zamówieniom produktów, których nie ma na stanie.
        Chroni to przed overselling i niezadowoleniem klientów.
        """
        with app.app_context():
            product = Product(name='Test', price=10.0, stock=5)
            
            assert product.is_available(6) is False
            assert product.is_available(100) is False


class TestOrderModel:
    """Testy jednostkowe modelu Order."""
    
    def test_order_can_be_cancelled_when_pending(self, app):
        """
        TEST 3: Zamówienie w statusie 'pending' może być anulowane.
        
        UZASADNIENIE BIZNESOWE:
        Klient powinien móc anulować zamówienie dopóki nie zostało potwierdzone.
        Zapewnia to elastyczność i dobre doświadczenie klienta.
        """
        with app.app_context():
            order = Order(customer_name='Test', customer_email='t@t.com')
            order.status = Order.STATUS_PENDING
            
            assert order.can_be_cancelled() is True
    
    def test_order_cannot_be_cancelled_when_confirmed(self, app):
        """
        TEST 4: Zamówienie potwierdzone nie może być anulowane.
        
        UZASADNIENIE BIZNESOWE:
        Po potwierdzeniu zamówienia firma rozpoczyna realizację (pakowanie, wysyłka).
        Anulowanie na tym etapie generowałoby straty operacyjne.
        """
        with app.app_context():
            order = Order(customer_name='Test', customer_email='t@t.com')
            order.status = Order.STATUS_CONFIRMED
            
            assert order.can_be_cancelled() is False
    
    def test_order_can_be_completed_only_when_confirmed(self, app):
        """
        TEST 5: Tylko potwierdzone zamówienie może być zakończone.
        
        UZASADNIENIE BIZNESOWE:
        Przepływ zamówienia: pending -> confirmed -> completed.
        Nie można pominąć kroku potwierdzenia - zapewnia to kontrolę jakości procesu.
        """
        with app.app_context():
            order_pending = Order(customer_name='Test', customer_email='t@t.com')
            order_pending.status = Order.STATUS_PENDING
            
            order_confirmed = Order(customer_name='Test', customer_email='t@t.com')
            order_confirmed.status = Order.STATUS_CONFIRMED
            
            assert order_pending.can_be_completed() is False
            assert order_confirmed.can_be_completed() is True
    
    def test_order_calculate_total(self, app):
        """
        TEST 6: Poprawne obliczanie sumy zamówienia.
        
        UZASADNIENIE BIZNESOWE:
        Suma zamówienia musi być dokładna - to podstawa rozliczeń finansowych.
        Błąd w obliczeniach = straty dla firmy lub klienta.
        """
        with app.app_context():
            product1 = Product(name='A', price=100.0, stock=10)
            product2 = Product(name='B', price=50.0, stock=10)
            db.session.add_all([product1, product2])
            db.session.flush()
            
            order = Order(customer_name='Test', customer_email='t@t.com')
            db.session.add(order)
            db.session.flush()
            
            item1 = OrderItem(order=order, product=product1, quantity=2, 
                            unit_price=100.0, subtotal=200.0)
            item2 = OrderItem(order=order, product=product2, quantity=1, 
                            unit_price=50.0, subtotal=50.0)
            db.session.add_all([item1, item2])
            
            total = order.calculate_total()
            
            assert total == 250.0
            assert order.total_amount == 250.0
