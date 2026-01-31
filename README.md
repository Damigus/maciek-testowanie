# Order Management API

Prosta aplikacja Flask API do zarządzania zamówieniami dla małej firmy. Aplikacja demonstruje dobre praktyki testowania w Pythonie z wykorzystaniem pytest.

## 📋 Spis treści

- [Opis biznesowy](#-opis-biznesowy)
- [Architektura](#-architektura)
- [Instalacja](#-instalacja)
- [Uruchomienie](#-uruchomienie)
- [API Endpoints](#-api-endpoints)
- [Testy](#-testy)
- [GitLab CI/CD](#-gitlab-cicd)

---

## 🏢 Opis biznesowy

System zarządza procesem zamówień w małym sklepie/firmie:

### Encje
- **Product** - produkty dostępne w ofercie (nazwa, cena, stan magazynowy)
- **Order** - zamówienia klientów
- **OrderItem** - pozycje w zamówieniu

### Przepływ zamówienia

```
┌─────────┐    potwierdź    ┌───────────┐    zakończ    ┌───────────┐
│ PENDING │───────────────▶│ CONFIRMED │─────────────▶│ COMPLETED │
└─────────┘                 └───────────┘               └───────────┘
     │
     │ anuluj
     ▼
┌───────────┐
│ CANCELLED │
└───────────┘
```

### Kluczowe reguły biznesowe

1. **Rezerwacja stocku** - przy składaniu zamówienia produkty są rezerwowane
2. **Zwrot stocku przy anulowaniu** - anulowanie przywraca stan magazynowy
3. **Kolejność statusów** - nie można pominąć etapu potwierdzenia
4. **Atomiczność** - zamówienie z niedostępnym produktem jest całkowicie odrzucane

---

## 🏗 Architektura

```
/
├── app/
│   ├── __init__.py      # Application factory
│   ├── config.py        # Konfiguracja (dev/test/prod)
│   ├── models.py        # Modele SQLAlchemy
│   ├── routes.py        # Endpointy API
│   └── services.py      # Logika biznesowa
├── tests/
│   ├── conftest.py      # Fixtures pytest
│   ├── test_unit.py     # Testy jednostkowe
│   ├── test_integration.py  # Testy integracyjne
│   └── test_scenarios.py    # Testy scenariuszowe
├── requirements.txt
├── run.py               # Entry point
├── .gitlab-ci.yml       # Pipeline CI/CD
└── README.md
```

### Warstwy aplikacji

| Warstwa | Plik | Odpowiedzialność |
|---------|------|------------------|
| API | `routes.py` | Obsługa HTTP, serializacja JSON |
| Serwisy | `services.py` | Logika biznesowa, walidacja |
| Modele | `models.py` | Struktura danych, proste reguły |
| Baza | SQLAlchemy | Persystencja (SQLite) |

---

## 💻 Instalacja

### Wymagania
- Python 3.9+
- pip

### Kroki

```bash
# 1. Sklonuj repozytorium
git clone <url-repo>
cd order-management-api

# 2. Utwórz virtual environment
python -m venv venv

# 3. Aktywuj venv
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Zainstaluj zależności
pip install -r requirements.txt
```

---

## 🚀 Uruchomienie

### Development

```bash
# Ustaw zmienną środowiskową
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows

# Uruchom serwer
python run.py
```

Aplikacja będzie dostępna pod `http://localhost:5000`

### Production

```bash
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@host/db
export SECRET_KEY=twój-bezpieczny-klucz

python run.py
```

---

## 📡 API Endpoints

### Health Check
```
GET /api/health
```

### Produkty

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/products` | Lista wszystkich produktów |
| GET | `/api/products/{id}` | Szczegóły produktu |
| POST | `/api/products` | Utwórz produkt |
| PATCH | `/api/products/{id}/stock` | Zmień stan magazynowy |

**Przykład - utwórz produkt:**
```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 2500.00, "stock": 10}'
```

### Zamówienia

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/orders` | Lista zamówień |
| GET | `/api/orders?status=pending` | Filtruj po statusie |
| GET | `/api/orders/{id}` | Szczegóły zamówienia |
| POST | `/api/orders` | Utwórz zamówienie |
| POST | `/api/orders/{id}/confirm` | Potwierdź zamówienie |
| POST | `/api/orders/{id}/cancel` | Anuluj zamówienie |
| POST | `/api/orders/{id}/complete` | Zakończ zamówienie |

**Przykład - utwórz zamówienie:**
```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Jan Kowalski",
    "customer_email": "jan@example.com",
    "items": [
      {"product_id": 1, "quantity": 2}
    ]
  }'
```

---

## 🧪 Testy

### Uruchomienie wszystkich testów

```bash
pytest tests/ -v
```

### Uruchomienie z pokryciem kodu

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Uruchomienie konkretnej kategorii

```bash
pytest tests/test_unit.py -v        # Tylko jednostkowe
pytest tests/test_integration.py -v  # Tylko integracyjne
pytest tests/test_scenarios.py -v    # Tylko scenariuszowe
```

---

## 📊 Opis testów

### Testy jednostkowe (`test_unit.py`)

Testują izolowaną logikę modeli - najszybsze, bez zależności zewnętrznych.

| # | Test | Cel biznesowy |
|---|------|---------------|
| 1 | `test_product_is_available_with_sufficient_stock` | Weryfikacja dostępności produktu gdy jest towar |
| 2 | `test_product_is_not_available_with_insufficient_stock` | Ochrona przed overselling |
| 3 | `test_order_can_be_cancelled_when_pending` | Elastyczność dla klienta |
| 4 | `test_order_cannot_be_cancelled_when_confirmed` | Ochrona przed stratami operacyjnymi |
| 5 | `test_order_can_be_completed_only_when_confirmed` | Kontrola przepływu zamówienia |
| 6 | `test_order_calculate_total` | Poprawność rozliczeń finansowych |

### Testy integracyjne (`test_integration.py`)

Testują współpracę API z serwisami i bazą danych.

| # | Test | Cel biznesowy |
|---|------|---------------|
| 7 | `test_create_product_success` | Administrator może dodawać produkty |
| 8 | `test_create_product_validation_error` | Ochrona integralności danych |
| 9 | `test_get_product_not_found` | Poprawna obsługa błędów |
| 10 | `test_create_order_success` | Klient może złożyć zamówienie |
| 11 | `test_create_order_insufficient_stock` | Blokada zamówień niemożliwych do realizacji |
| 12 | `test_confirm_order_success` | Pracownik może potwierdzić zamówienie |
| 13 | `test_cancel_order_restores_stock` | Przywrócenie stocku przy anulowaniu |

### Testy scenariuszowe (`test_scenarios.py`)

Testują pełne przepływy biznesowe end-to-end.

| # | Test | Scenariusz |
|---|------|------------|
| 14 | `test_full_order_lifecycle_happy_path` | Pełny cykl: zamówienie → potwierdzenie → dostawa |
| 15 | `test_order_cancellation_scenario` | Klient anuluje zamówienie, stock wraca |
| 16 | `test_cannot_complete_pending_order` | Wymuszenie kolejności statusów |
| 17 | `test_cannot_cancel_confirmed_order` | Ochrona zamówień w realizacji |
| 18 | `test_order_with_multiple_products` | Zamówienie z wieloma produktami |
| 19 | `test_order_rejected_when_one_product_unavailable` | Atomiczność transakcji |
| 20 | `test_order_rejected_with_invalid_email` | Walidacja danych kontaktowych |

---

## 🔄 GitLab CI/CD

### Konfiguracja

Pipeline jest zdefiniowany w `.gitlab-ci.yml` i uruchamia się automatycznie przy:
- Push do dowolnego brancha
- Merge Request
- Push do głównego brancha

### Struktura pipeline

```
┌───────────────────────────────────────────────────────────┐
│                        STAGE: test                         │
├─────────────┬─────────────────┬─────────────┬─────────────┤
│ unit_tests  │ integration_    │ scenario_   │ all_tests_  │
│             │ tests           │ tests       │ with_       │
│             │                 │             │ coverage    │
└─────────────┴─────────────────┴─────────────┴─────────────┘
                                                     │
                                                     ▼
                              ┌─────────────────────────────┐
                              │       STAGE: report         │
                              │           pages             │
                              │  (publikacja coverage HTML) │
                              └─────────────────────────────┘
```

### Jobs

| Job | Opis | Kiedy |
|-----|------|-------|
| `unit_tests` | Testy jednostkowe | Każdy push |
| `integration_tests` | Testy integracyjne | Każdy push |
| `scenario_tests` | Testy scenariuszowe | Każdy push |
| `all_tests_with_coverage` | Pełne testy + coverage | MR i main |
| `pages` | Publikacja raportu HTML | Tylko main |

### Konfiguracja Runnera

Upewnij się, że masz skonfigurowany GitLab Runner z tagiem `docker`:

```bash
# Rejestracja runnera
gitlab-runner register \
  --url https://gitlab.com/ \
  --registration-token YOUR_TOKEN \
  --executor docker \
  --docker-image python:3.11-slim \
  --tag-list docker
```

### Artefakty

Po uruchomieniu pipeline możesz pobrać:
- `htmlcov/` - raport HTML z pokryciem kodu
- `coverage.xml` - raport w formacie Cobertura

### Coverage Badge

Aby dodać badge z pokryciem do README, w GitLab:
1. Settings → CI/CD → General pipelines
2. Skopiuj "Coverage" badge markdown

---

## 📁 Zmienne środowiskowe

| Zmienna | Opis | Domyślnie |
|---------|------|-----------|
| `FLASK_ENV` | Tryb: development/testing/production | development |
| `DATABASE_URL` | URL bazy danych | sqlite:///orders.db |
| `SECRET_KEY` | Klucz do szyfrowania sesji | dev-secret-key |

---

## 📝 Licencja

MIT
