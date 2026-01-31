"""
Scenario tests - testują pełne przepływy biznesowe end-to-end.

Te testy symulują rzeczywiste scenariusze użycia systemu przez użytkowników.
Weryfikują że cały system działa poprawnie jako całość.
"""
import pytest
import json


class TestOrderLifecycleScenarios:
    """Scenariusze testowe cyklu życia zamówienia."""
    
    def test_full_order_lifecycle_happy_path(self, client, sample_product):
        """
        TEST 14: Pełny cykl życia zamówienia - scenariusz pozytywny.
        
        SCENARIUSZ BIZNESOWY:
        1. Klient składa zamówienie
        2. Pracownik potwierdza zamówienie (po weryfikacji płatności)
        3. Kurier dostarcza - zamówienie zakończone
        
        Ten test weryfikuje główny, najpopularniejszy przepływ w systemie.
        Jeśli ten test nie działa - system nie spełnia podstawowej funkcji.
        """
        # KROK 1: Klient składa zamówienie
        order_response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Maria Wiśniewska',
                'customer_email': 'maria@firma.pl',
                'items': [{'product_id': sample_product, 'quantity': 2}]
            }),
            content_type='application/json'
        )
        assert order_response.status_code == 201
        order = order_response.get_json()
        order_id = order['id']
        assert order['status'] == 'pending'
        
        # KROK 2: Pracownik potwierdza zamówienie
        confirm_response = client.post(f'/api/orders/{order_id}/confirm')
        assert confirm_response.status_code == 200
        assert confirm_response.get_json()['status'] == 'confirmed'
        
        # KROK 3: Kurier dostarczył - oznaczamy jako zakończone
        complete_response = client.post(f'/api/orders/{order_id}/complete')
        assert complete_response.status_code == 200
        final_order = complete_response.get_json()
        assert final_order['status'] == 'completed'
        
        # Weryfikacja końcowa
        get_response = client.get(f'/api/orders/{order_id}')
        assert get_response.get_json()['status'] == 'completed'
    
    def test_order_cancellation_scenario(self, client, sample_product):
        """
        TEST 15: Scenariusz anulowania zamówienia przez klienta.
        
        SCENARIUSZ BIZNESOWY:
        1. Klient składa zamówienie (produkty rezerwowane)
        2. Klient zmienia zdanie i anuluje
        3. Produkty wracają na stan magazynowy
        
        Ten scenariusz jest częsty w e-commerce (10-30% zamówień anulowanych).
        Krytyczne jest poprawne przywrócenie stanu magazynowego.
        """
        # Sprawdź początkowy stan magazynu
        initial = client.get(f'/api/products/{sample_product}').get_json()
        initial_stock = initial['stock']
        
        # KROK 1: Klient składa zamówienie
        order_response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Piotr Kowalczyk',
                'customer_email': 'piotr@email.com',
                'items': [{'product_id': sample_product, 'quantity': 5}]
            }),
            content_type='application/json'
        )
        order_id = order_response.get_json()['id']
        
        # Weryfikacja: stock zmniejszony
        mid = client.get(f'/api/products/{sample_product}').get_json()
        assert mid['stock'] == initial_stock - 5
        
        # KROK 2: Klient anuluje zamówienie
        cancel_response = client.post(f'/api/orders/{order_id}/cancel')
        assert cancel_response.status_code == 200
        assert cancel_response.get_json()['status'] == 'cancelled'
        
        # KROK 3: Weryfikacja przywrócenia stanu
        final = client.get(f'/api/products/{sample_product}').get_json()
        assert final['stock'] == initial_stock, "Stock should be restored after cancellation"


class TestBusinessRuleEnforcement:
    """Testy egzekwowania reguł biznesowych."""
    
    def test_cannot_complete_pending_order(self, client, sample_product):
        """
        TEST 16: Nie można zakończyć zamówienia bez wcześniejszego potwierdzenia.
        
        REGUŁA BIZNESOWA:
        Przepływ statusów jest ściśle określony: pending -> confirmed -> completed.
        Nie można przeskoczyć etapu potwierdzenia.
        
        UZASADNIENIE:
        Potwierdzenie to moment weryfikacji płatności i danych.
        Pominięcie go mogłoby prowadzić do wysyłki nieopłaconych zamówień.
        """
        # Stwórz zamówienie (status: pending)
        order_response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test',
                'customer_email': 'test@test.com',
                'items': [{'product_id': sample_product, 'quantity': 1}]
            }),
            content_type='application/json'
        )
        order_id = order_response.get_json()['id']
        
        # Próba zakończenia bez potwierdzenia
        complete_response = client.post(f'/api/orders/{order_id}/complete')
        
        assert complete_response.status_code == 400
        assert 'Only confirmed orders can be completed' in complete_response.get_json()['error']
    
    def test_cannot_cancel_confirmed_order(self, client, sample_product):
        """
        TEST 17: Nie można anulować potwierdzonego zamówienia.
        
        REGUŁA BIZNESOWA:
        Po potwierdzeniu zamówienia rozpoczyna się jego realizacja.
        Anulowanie na tym etapie jest niedozwolone przez API.
        
        UZASADNIENIE:
        Firma już mogła rozpocząć pakowanie lub wysyłkę.
        Anulowanie wymagałoby ręcznej interwencji i zwrotu kosztów.
        """
        # Stwórz i potwierdź zamówienie
        order_response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test',
                'customer_email': 'test@test.com',
                'items': [{'product_id': sample_product, 'quantity': 1}]
            }),
            content_type='application/json'
        )
        order_id = order_response.get_json()['id']
        client.post(f'/api/orders/{order_id}/confirm')
        
        # Próba anulowania potwierdzonego zamówienia
        cancel_response = client.post(f'/api/orders/{order_id}/cancel')
        
        assert cancel_response.status_code == 400
        assert 'Only pending orders can be cancelled' in cancel_response.get_json()['error']


class TestMultiProductOrderScenario:
    """Scenariusze zamówień z wieloma produktami."""
    
    def test_order_with_multiple_products(self, client, sample_products):
        """
        TEST 18: Zamówienie zawierające wiele różnych produktów.
        
        SCENARIUSZ BIZNESOWY:
        Typowe zamówienie w sklepie zawiera kilka produktów.
        System musi poprawnie:
        - Zarezerwować stock każdego produktu
        - Obliczyć poprawną sumę całkowitą
        - Przechowywać szczegóły każdej pozycji
        """
        laptop_id, mouse_id, _ = sample_products
        
        response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Firma XYZ Sp. z o.o.',
                'customer_email': 'zamowienia@firmaxyz.pl',
                'items': [
                    {'product_id': laptop_id, 'quantity': 2},   # 2 x 2500 = 5000
                    {'product_id': mouse_id, 'quantity': 5},    # 5 x 50 = 250
                ]
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        order = response.get_json()
        
        # Weryfikacja sumy
        assert order['total_amount'] == 5250.00
        
        # Weryfikacja pozycji
        assert len(order['items']) == 2
        
        # Weryfikacja zmniejszenia stanów
        laptop = client.get(f'/api/products/{laptop_id}').get_json()
        mouse = client.get(f'/api/products/{mouse_id}').get_json()
        
        assert laptop['stock'] == 3  # Było 5, zamówiono 2
        assert mouse['stock'] == 15  # Było 20, zamówiono 5
    
    def test_order_rejected_when_one_product_unavailable(self, client, sample_products):
        """
        TEST 19: Zamówienie odrzucone gdy jeden z produktów niedostępny.
        
        SCENARIUSZ BIZNESOWY:
        Klient zamawia 3 produkty, ale jednego brak na stanie.
        Całe zamówienie musi zostać odrzucone (atomiczność transakcji).
        
        UZASADNIENIE:
        Częściowa realizacja zamówienia to zły UX.
        Lepiej poinformować klienta o problemie przed złożeniem.
        """
        laptop_id, mouse_id, keyboard_id = sample_products  # keyboard ma stock=0
        
        response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test',
                'customer_email': 'test@test.com',
                'items': [
                    {'product_id': laptop_id, 'quantity': 1},
                    {'product_id': keyboard_id, 'quantity': 1},  # Brak na stanie!
                ]
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'Insufficient stock' in response.get_json()['error']
        
        # Weryfikacja że nic się nie zmieniło (rollback)
        laptop = client.get(f'/api/products/{laptop_id}').get_json()
        assert laptop['stock'] == 5  # Bez zmian


class TestDataValidationScenarios:
    """Scenariusze walidacji danych wejściowych."""
    
    def test_order_rejected_with_invalid_email(self, client, sample_product):
        """
        TEST 20: Zamówienie odrzucone przy nieprawidłowym emailu.
        
        SCENARIUSZ BIZNESOWY:
        Email klienta jest niezbędny do:
        - Wysłania potwierdzenia zamówienia
        - Komunikacji o statusie dostawy
        - Fakturowania
        
        System musi wymusić podanie prawidłowego adresu email.
        """
        response = client.post('/api/orders',
            data=json.dumps({
                'customer_name': 'Test User',
                'customer_email': 'invalid-email',  # Brak @
                'items': [{'product_id': sample_product, 'quantity': 1}]
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'email' in response.get_json()['error'].lower()
