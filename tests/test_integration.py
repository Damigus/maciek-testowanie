"""
Integration tests - testują współpracę warstwy API z serwisami i bazą danych.

Te testy weryfikują że endpointy API poprawnie komunikują się z logiką biznesową
i bazą danych. Wykrywają problemy z integracją komponentów.
"""
import pytest
import json


class TestProductAPI:
    """Testy integracyjne API produktów."""
    
    def test_create_product_success(self, client):
        """
        TEST 7: Poprawne tworzenie produktu przez API.
        
        UZASADNIENIE BIZNESOWE:
        Administrator musi móc dodawać nowe produkty do oferty.
        Test weryfikuje cały przepływ: request -> walidacja -> zapis w DB -> response.
        """
        response = client.post('/api/products', 
            data=json.dumps({
                'name': 'Nowy Laptop',
                'price': 3500.00,
                'stock': 15
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Nowy Laptop'
        assert data['price'] == 3500.00
        assert data['stock'] == 15
        assert 'id' in data
    
    def test_create_product_validation_error(self, client):
        """
        TEST 8: Walidacja przy tworzeniu produktu z błędnymi danymi.
        
        UZASADNIENIE BIZNESOWE:
        System musi odrzucać nieprawidłowe dane (ujemna cena).
        Chroni to integralność danych i zapobiega błędom księgowym.
        """
        response = client.post('/api/products',
            data=json.dumps({
                'name': 'Test',
                'price': -50.00,  # Nieprawidłowa cena
                'stock': 10
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'error' in response.get_json()
    
    def test_get_product_not_found(self, client):
        """
        TEST 9: Pobieranie nieistniejącego produktu.
        
        UZASADNIENIE BIZNESOWE:
        API musi zwracać czytelny błąd 404 gdy produkt nie istnieje.
        Pomaga to w debugowaniu i obsłudze błędów po stronie klienta.
        """
        response = client.get('/api/products/99999')
        
        assert response.status_code == 404
        assert response.get_json()['error'] == 'Product not found'


class TestOrderAPI:
    """Testy integracyjne API zamówień."""
    
    def test_create_order_success(self, client, sample_product):
        """
        TEST 10: Tworzenie zamówienia z rezerwacją stanu magazynowego.
        
        UZASADNIENIE BIZNESOWE:
        Przy składaniu zamówienia system musi:
        1. Zwalidować dostępność produktów
        2. Zarezerwować stock (zmniejszyć dostępną ilość)
        3. Obliczyć sumę zamówienia
        
        To krytyczny proces biznesowy - błędy prowadzą do overselling.
        """
        response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Anna Nowak',
                'customer_email': 'anna@example.com',
                'items': [
                    {'product_id': sample_product, 'quantity': 2}
                ]
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['customer_name'] == 'Anna Nowak'
        assert data['status'] == 'pending'
        assert len(data['items']) == 1
        assert data['total_amount'] == 199.98  # 2 * 99.99
    
    def test_create_order_insufficient_stock(self, client, sample_product):
        """
        TEST 11: Odmowa utworzenia zamówienia przy braku towaru.
        
        UZASADNIENIE BIZNESOWE:
        System musi blokować zamówienia gdy brak wystarczającego stanu.
        Zapobiega to przyjmowaniu zamówień niemożliwych do realizacji.
        """
        response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test User',
                'customer_email': 'test@test.com',
                'items': [
                    {'product_id': sample_product, 'quantity': 100}  # Za dużo
                ]
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'Insufficient stock' in response.get_json()['error']
    
    def test_confirm_order_success(self, client, app, sample_product):
        """
        TEST 12: Potwierdzanie zamówienia.
        
        UZASADNIENIE BIZNESOWE:
        Po weryfikacji płatności/danych, pracownik potwierdza zamówienie.
        Status zmienia się z 'pending' na 'confirmed', co uruchamia realizację.
        """
        # Najpierw stwórz zamówienie
        create_response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test',
                'customer_email': 'test@test.com',
                'items': [{'product_id': sample_product, 'quantity': 1}]
            }),
            content_type='application/json'
        )
        order_id = create_response.get_json()['id']
        
        # Potwierdź zamówienie
        response = client.post(f'/api/orders/{order_id}/confirm')
        
        assert response.status_code == 200
        assert response.get_json()['status'] == 'confirmed'
    
    def test_cancel_order_restores_stock(self, client, app, sample_product):
        """
        TEST 13: Anulowanie zamówienia przywraca stan magazynowy.
        
        UZASADNIENIE BIZNESOWE:
        Gdy klient anuluje zamówienie, zarezerwowane produkty muszą wrócić na stan.
        Bez tego mechanizmu tracilibyśmy dostępność towaru.
        """
        # Sprawdź początkowy stan
        initial_stock = client.get(f'/api/products/{sample_product}').get_json()['stock']
        
        # Stwórz zamówienie (rezerwuje 3 sztuki)
        create_response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test',
                'customer_email': 'test@test.com',
                'items': [{'product_id': sample_product, 'quantity': 3}]
            }),
            content_type='application/json'
        )
        order_id = create_response.get_json()['id']
        
        # Sprawdź że stock się zmniejszył
        after_order_stock = client.get(f'/api/products/{sample_product}').get_json()['stock']
        assert after_order_stock == initial_stock - 3
        
        # Anuluj zamówienie
        client.post(f'/api/orders/{order_id}/cancel')
        
        # Sprawdź że stock wrócił
        final_stock = client.get(f'/api/products/{sample_product}').get_json()['stock']
        assert final_stock == initial_stock
