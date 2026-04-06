# DirtDesk

Shop management system for Red Dirt UTV Performance — Waller, TX.

Manages customers, machines, repair orders, inventory, and produces shop documents (intake forms, repair orders, parts waivers, vehicle release forms).

---

## Tech Stack

- **Python 3.12+** / Flask
- **SQLite** (dev & production via persistent volume)
- **Flask-SQLAlchemy** + **Flask-Migrate** for ORM and schema migrations
- **Flask-Login** for single-user authentication
- **WeasyPrint** for PDF generation
- **Gunicorn** as the production WSGI server

---

## Local Development Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/brthurr/red-dirt-utv-crm.git
cd red-dirt-utv-crm
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements-dev.txt
```

WeasyPrint requires system libraries. On Ubuntu/Debian:

```bash
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Long random string — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SHOP_PASSWORD` | Login password for the shop |
| `DATABASE_URL` | SQLite path (default: `sqlite:///red_dirt_utv.db`) |
| `SHOP_PHONE` | Shop phone number (appears on PDFs) |
| `SHOP_EMAIL` | Shop email (appears on PDFs) |
| `UPLOAD_FOLDER` | Path for intake photo storage (default: `uploads/` in project root) |

### 4. Initialize the database

```bash
flask db init        # only needed once — creates the migrations/ folder
flask db migrate -m "initial schema"
flask db upgrade
```

### 5. Run the dev server

```bash
python run.py
```

App is available at `http://localhost:5000`. Log in with the password set in `SHOP_PASSWORD`.

---

## Schema Changes

Any time a model is changed, generate and apply a migration:

```bash
flask db migrate -m "describe what changed"
flask db upgrade
```

On the production LXC, `startup.py` runs `upgrade()` automatically on every deploy so migrations apply without manual intervention.

---

## Running Tests

```bash
pytest
```

Tests use an in-memory SQLite database — no setup required beyond installing dev dependencies.

To run a specific file or test:

```bash
pytest tests/test_models.py
pytest tests/test_routes.py::TestInventory::test_create_part
```

---

## Project Structure

```
red-dirt-utv-crm/
├── app/
│   ├── __init__.py          # App factory, extension init
│   ├── models.py            # SQLAlchemy models
│   ├── pdf_utils.py         # WeasyPrint PDF generation
│   ├── routes/
│   │   ├── auth.py          # Login / logout
│   │   ├── customers.py     # Customer CRUD
│   │   ├── inventory.py     # Parts catalog and stock management
│   │   ├── machines.py      # Machine CRUD
│   │   ├── main.py          # Dashboard
│   │   └── repair_orders.py # Repair order CRUD, photos, authorizations, sign-off
│   ├── static/
│   │   └── css/main.css     # All styles
│   └── templates/
│       ├── base.html
│       ├── auth/
│       ├── customers/
│       ├── inventory/
│       ├── machines/
│       ├── pdf/             # WeasyPrint PDF templates
│       └── repair_orders/
├── migrations/              # Flask-Migrate migration scripts
├── tests/
│   ├── conftest.py          # Fixtures (app, db, client, sample data)
│   ├── test_models.py       # Model unit tests
│   └── test_routes.py       # Route integration tests
├── uploads/                 # Intake photo storage (gitignored)
├── config.py                # Config class (reads from environment)
├── run.py                   # Dev server entry point
├── startup.py               # Production entry point (runs migrations)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Dev/test dependencies
└── pytest.ini
```

---

## Production Deployment (LXC on Proxmox)

The app runs on an LXC container behind Nginx Proxy Manager with Cloudflare DNS.

### LXC Setup (Ubuntu 22.04)

```bash
apt update && apt install -y python3-pip python3-venv git \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2

git clone https://github.com/brthurr/red-dirt-utv-crm.git /opt/dirtdesk
cd /opt/dirtdesk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment

Create `/opt/dirtdesk/.env` with production values (see table above).
Set `DATABASE_URL=sqlite:////home/dirtdesk/data/red_dirt_utv.db` to keep the DB on persistent storage outside the app directory.

### Systemd Service

Create `/etc/systemd/system/dirtdesk.service`:

```ini
[Unit]
Description=DirtDesk Shop Management
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/dirtdesk
EnvironmentFile=/opt/dirtdesk/.env
ExecStart=/opt/dirtdesk/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 startup:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now dirtdesk
```

### Nginx Proxy Manager

Point a proxy host to `http://<LXC-IP>:8000`. Enable SSL via Let's Encrypt for `dirtdesk.reddirtutv.com`.

### GitHub Actions Deployment

The workflow (`.github/workflows/deploy.yml`) SSHes into the LXC on push to the deploy branch, pulls the latest code, and restarts the service. Required GitHub secrets:

| Secret | Value |
|--------|-------|
| `SSH_HOST` | LXC IP or hostname |
| `SSH_USER` | Deploy user |
| `SSH_KEY` | Private key for deploy user |

---

## Key Features

- **Customers** — full contact info, notes, machine history
- **Machines** — VIN, year/make/model, engine, odometer/hours
- **Repair Orders** — complaint, intake condition, work performed, parts, labor, tax
- **Intake Photos** — attach multiple photos per RO at intake
- **Customer Authorizations** — log discovered issues, track approve/decline with method and timestamp
- **Completion Sign-Off** — record who accepted the completed work
- **Inventory** — parts catalog with cost/sell pricing, stock tracking, low-stock alerts
- **Parts Catalog Lookup** — search inventory while building an RO to auto-fill line items
- **PDF Documents** — intake form, repair order, customer parts waiver, vehicle release form
