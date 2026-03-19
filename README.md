# Aztec Ticket Microservice

FastAPI microservice do dekodowania kodów Aztec z biletów kolejowych (standard UIC 918.3) i generowania kart Apple Wallet (PKPass) oraz Google Wallet.

## Wymagania systemowe

- Python 3.10+
- **Poppler** (wymagany przez `pdf2image`)

### Instalacja Poppler (Windows)

```bash
winget install -e --id osdn.poppler
```

Lub pobierz ręcznie i dodaj folder `bin/` do zmiennej środowiskowej `PATH`.

## Instalacja

```bash
# Utwórz i aktywuj wirtualne środowisko
python -m venv .venv
.venv\Scripts\activate

# Zainstaluj zależności
pip install -r requirements.txt
```

## Uruchomienie

```bash
uvicorn app.main:app --reload
```

Serwer startuje na `http://localhost:8000`.
Dokumentacja Swagger UI dostępna pod `http://localhost:8000/docs`.

## Endpointy

| Metoda | Ścieżka           | Opis                                      |
|--------|-------------------|-------------------------------------------|
| GET    | `/health`         | Status serwisu                            |
| POST   | `/tickets/decode` | Dekoduje kod Aztec z pliku PDF lub obrazu |
