"""
Shared pytest fixtures for DirtDesk tests.

Uses an in-memory SQLite database with StaticPool so the test client and
the test fixtures share the same connection. The app fixture is function-
scoped so each test gets a completely fresh app instance with no shared state.
"""
import pytest
from sqlalchemy.pool import StaticPool
from app import create_app, db as _db
from app.models import Customer, Machine, RepairOrder, LineItem, Part

TEST_CONFIG = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_ENGINE_OPTIONS': {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    },
    'WTF_CSRF_ENABLED': False,
    'SECRET_KEY': 'test-secret',
    'SHOP_PASSWORD': 'testpass',
    'UPLOAD_FOLDER': '/tmp/dirtdesk_test_uploads',
}


@pytest.fixture
def app():
    """Fresh application instance for each test — no shared state between tests."""
    application = create_app()
    application.config.update(TEST_CONFIG)

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """Database handle within the current test's app context."""
    yield _db
    _db.session.rollback()
    for table in reversed(_db.metadata.sorted_tables):
        _db.session.execute(table.delete())
    _db.session.commit()


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app):
    """Authenticated test client (logged in as shop owner)."""
    c = app.test_client()
    c.post('/login', data={'password': 'testpass'}, follow_redirects=True)
    return c


@pytest.fixture
def sample_customer(db):
    """A persisted customer for use in tests."""
    customer = Customer(
        name='Jane Rider',
        phone='936-555-0101',
        email='jane@example.com',
        address='100 Trail Rd',
        city='Waller',
        state='TX',
        zip_code='77484',
    )
    db.session.add(customer)
    db.session.commit()
    return customer


@pytest.fixture
def sample_machine(db, sample_customer):
    """A persisted machine linked to sample_customer."""
    machine = Machine(
        customer_id=sample_customer.id,
        year='2022',
        make='Polaris',
        model='RZR Pro XP',
        vin='1HD1KHM10KB123456',
        engine_cc='999cc',
        color='Black',
        odometer_hours='120',
    )
    db.session.add(machine)
    db.session.commit()
    return machine


@pytest.fixture
def sample_ro(db, sample_customer, sample_machine):
    """A persisted repair order with one part and one labor line item."""
    ro = RepairOrder(
        ro_number='RO-2026-0001',
        customer_id=sample_customer.id,
        machine_id=sample_machine.id,
        complaint='Grinding noise front left',
        intake_condition='Minor scratches on left panel, full fuel',
        technician='Tech1',
        status='Open',
        tax_rate=0.0825,
    )
    db.session.add(ro)
    db.session.flush()

    part = LineItem(ro_id=ro.id, item_type='part', part_number='CV-001',
                    description='CV Boot Kit', quantity=1, unit_price=45.00)
    part.calculate_total()
    labor = LineItem(ro_id=ro.id, item_type='labor',
                     description='CV Boot Replacement', quantity=2, unit_price=95.00)
    labor.calculate_total()

    db.session.add_all([part, labor])
    db.session.flush()
    ro.recalculate_totals()
    db.session.commit()
    return ro


@pytest.fixture
def sample_part(db):
    """A persisted inventory part."""
    part = Part(
        part_number='CV-001',
        description='CV Boot Kit',
        vendor='All Balls Racing',
        cost_price=22.00,
        sell_price=45.00,
        quantity_on_hand=5,
        low_stock_threshold=2,
    )
    db.session.add(part)
    db.session.commit()
    return part
