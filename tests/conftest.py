"""
Shared pytest fixtures for DirtDesk tests.

Uses an in-memory SQLite database so tests are isolated and fast.
The test client is pre-authenticated — login logic is tested separately.
"""
import pytest
from app import create_app, db as _db
from app.models import Customer, Machine, RepairOrder, LineItem, Part


@pytest.fixture(scope='session')
def app():
    """Application instance configured for testing."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
        'SHOP_PASSWORD': 'testpass',
        'UPLOAD_FOLDER': '/tmp/dirtdesk_test_uploads',
    }
    application = create_app()
    application.config.update(test_config)

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Provide a clean database for each test function."""
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Truncate all tables between tests
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
    client = app.test_client()
    client.post('/login', data={'password': 'testpass'}, follow_redirects=True)
    return client


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
