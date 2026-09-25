# COSC-310-Pelmeni

## Team name: 
  Pelmeni

## Requirements:
- Python 3.12

## Setup:
Clone the repository: https://github.com/WilliamT424/COSC-310-Pelmeni.git

```bash
git clone https://github.com/WilliamT424/COSC-310-Pelmeni.git
cd COSC-310-Pelmeni
```

## Virtual Environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\Activate.ps1
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

## Dependency Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Starting the Application

Start the FastAPI application with:

```bash
python -m uvicorn app.main:app --reload
```

## API Endpoint paths

- `GET /` — Returns a welcome message.
- `GET /health` — Returns the health status of the application.
- `GET /restaurants` — Returns the list of restaurants.
- `GET /docs` — Provides API documentation.

## Representative Data

Restaurant data is stored in:

```text
data/restaurants.json
```

## Running tests

Run the test suite with pytest:

```bash
pytest
```

## Repository Structure

```text
COSC-310-Pelmeni/
├── app/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── data/
│   └── restaurants.json
├── tests/
├── .gitignore
├── pytest.ini
├── README.md
└── requirements.txt
```

