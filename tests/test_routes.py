"""
Integration tests for DirtDesk routes.

Tests verify HTTP responses, redirects, and database side-effects.
All tests use the authenticated client unless testing auth itself.
"""
import io
import pytest
from app.models import (Customer, Machine, RepairOrder, LineItem,
                        Part, CustomerAuthorization)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    def test_login_page_accessible(self, client):
        r = client.get('/login')
        assert r.status_code == 200

    def test_login_wrong_password(self, client):
        r = client.post('/login', data={'password': 'wrong'}, follow_redirects=True)
        assert r.status_code == 200
        assert b'Incorrect password' in r.data

    def test_login_correct_password(self, client):
        r = client.post('/login', data={'password': 'testpass'}, follow_redirects=True)
        assert r.status_code == 200

    def test_protected_route_redirects_unauthenticated(self, client):
        r = client.get('/ro/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_logout(self, auth_client):
        r = auth_client.get('/logout', follow_redirects=True)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_dashboard_loads(self, auth_client):
        r = auth_client.get('/')
        assert r.status_code == 200
        assert b'DirtDesk' in r.data


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class TestCustomers:
    def test_list_customers(self, auth_client, sample_customer):
        r = auth_client.get('/customers/')
        assert r.status_code == 200
        assert b'Jane Rider' in r.data

    def test_create_customer(self, auth_client, db):
        r = auth_client.post('/customers/new', data={
            'name': 'New Customer',
            'phone': '936-555-0000',
            'email': 'new@example.com',
            'city': 'Waller',
            'state': 'TX',
            'zip_code': '77484',
            'address': '1 Test St',
            'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Customer.query.filter_by(name='New Customer').first() is not None

    def test_create_customer_requires_name(self, auth_client, db):
        r = auth_client.post('/customers/new', data={'name': ''},
                             follow_redirects=True)
        assert r.status_code == 200
        assert b'required' in r.data.lower()

    def test_view_customer(self, auth_client, sample_customer):
        r = auth_client.get(f'/customers/{sample_customer.id}')
        assert r.status_code == 200
        assert b'Jane Rider' in r.data

    def test_edit_customer(self, auth_client, db, sample_customer):
        r = auth_client.post(f'/customers/{sample_customer.id}/edit', data={
            'name': 'Jane Updated',
            'phone': '', 'email': '', 'address': '',
            'city': '', 'state': 'TX', 'zip_code': '', 'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_customer)
        assert sample_customer.name == 'Jane Updated'

    def test_delete_customer(self, auth_client, db, sample_customer):
        cid = sample_customer.id
        r = auth_client.post(f'/customers/{cid}/delete', follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(Customer, cid) is None

    def test_search_customers(self, auth_client, sample_customer):
        r = auth_client.get('/customers/?q=Jane')
        assert r.status_code == 200
        assert b'Jane Rider' in r.data

    def test_search_customers_no_match(self, auth_client, sample_customer):
        r = auth_client.get('/customers/?q=XXXXNOTFOUND')
        assert r.status_code == 200
        assert b'Jane Rider' not in r.data


# ---------------------------------------------------------------------------
# Repair Orders
# ---------------------------------------------------------------------------

class TestRepairOrders:
    def test_list_ros(self, auth_client, sample_ro):
        r = auth_client.get('/ro/')
        assert r.status_code == 200
        assert b'RO-2026-0001' in r.data

    def test_view_ro(self, auth_client, sample_ro):
        r = auth_client.get(f'/ro/{sample_ro.id}')
        assert r.status_code == 200
        assert b'RO-2026-0001' in r.data
        assert b'Grinding noise' in r.data

    def test_create_ro(self, auth_client, db, sample_customer, sample_machine):
        r = auth_client.post('/ro/new', data={
            'customer_id': sample_customer.id,
            'machine_id': sample_machine.id,
            'complaint': 'Engine knocking',
            'intake_condition': 'Good condition',
            'work_performed': '',
            'technician': 'Tech1',
            'status': 'Open',
            'tax_rate': '8.25',
            'date_in': '2026-04-06',
            'date_out': '',
            'has_customer_parts': '',
            'customer_parts_notes': '',
            'item_type[]': ['part'],
            'item_part_number[]': ['ENG-001'],
            'item_desc[]': ['Air Filter'],
            'item_qty[]': ['1'],
            'item_price[]': ['25.00'],
        }, follow_redirects=True)
        assert r.status_code == 200
        ro = RepairOrder.query.filter_by(complaint='Engine knocking').first()
        assert ro is not None
        assert len(ro.line_items) == 1

    def test_create_ro_requires_customer(self, auth_client, db):
        r = auth_client.post('/ro/new', data={
            'customer_id': '',
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_edit_ro(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/edit', data={
            'complaint': 'Updated complaint',
            'intake_condition': 'Some damage',
            'work_performed': 'Fixed it',
            'technician': 'Tech2',
            'status': 'In Progress',
            'tax_rate': '8.25',
            'date_in': '2026-04-06',
            'date_out': '',
            'has_customer_parts': '',
            'customer_parts_notes': '',
            'item_type[]': [],
            'item_part_number[]': [],
            'item_desc[]': [],
            'item_qty[]': [],
            'item_price[]': [],
        }, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert sample_ro.complaint == 'Updated complaint'
        assert sample_ro.technician == 'Tech2'

    def test_update_status(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/status',
                             data={'status': 'In Progress'},
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert sample_ro.status == 'In Progress'

    def test_update_status_complete_sets_date_out(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/status',
                             data={'status': 'Complete'},
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert sample_ro.date_out is not None

    def test_delete_ro(self, auth_client, db, sample_ro):
        ro_id = sample_ro.id
        r = auth_client.post(f'/ro/{ro_id}/delete', follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(RepairOrder, ro_id) is None

    def test_filter_ro_by_status(self, auth_client, sample_ro):
        r = auth_client.get('/ro/?status=Open')
        assert r.status_code == 200
        assert b'RO-2026-0001' in r.data

    def test_filter_ro_no_match(self, auth_client, sample_ro):
        r = auth_client.get('/ro/?status=Delivered')
        assert r.status_code == 200
        assert b'RO-2026-0001' not in r.data

    def test_machines_for_customer_api(self, auth_client, sample_customer, sample_machine):
        r = auth_client.get(f'/ro/api/machines_for_customer?customer_id={sample_customer.id}')
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]['id'] == sample_machine.id

    def test_sign_off(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/signoff',
                             data={'signoff_name': 'Jane Rider'},
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert sample_ro.signoff_name == 'Jane Rider'
        assert sample_ro.signoff_at is not None

    def test_sign_off_requires_name(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/signoff',
                             data={'signoff_name': ''},
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert sample_ro.signoff_name is None

    def test_clear_sign_off(self, auth_client, db, sample_ro):
        # Sign off first
        auth_client.post(f'/ro/{sample_ro.id}/signoff',
                         data={'signoff_name': 'Jane Rider'})
        db.session.refresh(sample_ro)
        # Now clear it
        r = auth_client.post(f'/ro/{sample_ro.id}/signoff/clear',
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert sample_ro.signoff_name is None
        assert sample_ro.signoff_at is None


# ---------------------------------------------------------------------------
# Customer Authorizations
# ---------------------------------------------------------------------------

class TestAuthorizations:
    def test_add_authorization(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/authorizations',
                             data={'description': 'Cracked CV boot found'},
                             follow_redirects=True)
        assert r.status_code == 200
        auth = CustomerAuthorization.query.filter_by(ro_id=sample_ro.id).first()
        assert auth is not None
        assert auth.approved is None  # pending

    def test_add_authorization_requires_description(self, auth_client, db, sample_ro):
        r = auth_client.post(f'/ro/{sample_ro.id}/authorizations',
                             data={'description': ''},
                             follow_redirects=True)
        assert r.status_code == 200
        assert CustomerAuthorization.query.filter_by(ro_id=sample_ro.id).count() == 0

    def test_approve_authorization(self, auth_client, db, sample_ro):
        auth = CustomerAuthorization(ro_id=sample_ro.id,
                                     description='CV boot cracked')
        db.session.add(auth)
        db.session.commit()

        r = auth_client.post(
            f'/ro/{sample_ro.id}/authorizations/{auth.id}/resolve',
            data={'decision': 'approve', 'approval_method': 'Phone',
                  'approved_by': 'Jane Rider', 'notes': ''},
            follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(auth)
        assert auth.approved is True
        assert auth.approval_method == 'Phone'

    def test_decline_authorization(self, auth_client, db, sample_ro):
        auth = CustomerAuthorization(ro_id=sample_ro.id,
                                     description='Upgrade exhaust')
        db.session.add(auth)
        db.session.commit()

        r = auth_client.post(
            f'/ro/{sample_ro.id}/authorizations/{auth.id}/resolve',
            data={'decision': 'decline', 'approval_method': 'Text',
                  'approved_by': 'Jane Rider', 'notes': 'Too expensive'},
            follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(auth)
        assert auth.approved is False

    def test_delete_authorization(self, auth_client, db, sample_ro):
        auth = CustomerAuthorization(ro_id=sample_ro.id,
                                     description='Old item')
        db.session.add(auth)
        db.session.commit()
        auth_id = auth.id

        r = auth_client.post(
            f'/ro/{sample_ro.id}/authorizations/{auth_id}/delete',
            follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(CustomerAuthorization, auth_id) is None


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------

class TestPhotos:
    def test_upload_photo(self, auth_client, db, sample_ro, tmp_path, app):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        data = {
            'photos': (io.BytesIO(b'fakeimagecontent'), 'test.jpg'),
            'caption': 'Front damage',
        }
        r = auth_client.post(f'/ro/{sample_ro.id}/photos',
                             data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert len(sample_ro.photos) == 1
        assert sample_ro.photos[0].caption == 'Front damage'

    def test_upload_invalid_file_type(self, auth_client, db, sample_ro, tmp_path, app):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        data = {
            'photos': (io.BytesIO(b'notanimage'), 'virus.exe'),
            'caption': '',
        }
        r = auth_client.post(f'/ro/{sample_ro.id}/photos',
                             data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_ro)
        assert len(sample_ro.photos) == 0


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class TestInventory:
    def test_list_parts(self, auth_client, sample_part):
        r = auth_client.get('/inventory/')
        assert r.status_code == 200
        assert b'CV-001' in r.data

    def test_create_part(self, auth_client, db):
        r = auth_client.post('/inventory/new', data={
            'part_number': 'FILTER-01',
            'description': 'Oil Filter',
            'vendor': 'WIX',
            'cost_price': '5.00',
            'sell_price': '12.00',
            'quantity_on_hand': '10',
            'low_stock_threshold': '3',
            'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Part.query.filter_by(part_number='FILTER-01').first() is not None

    def test_create_part_requires_part_number(self, auth_client, db):
        r = auth_client.post('/inventory/new', data={
            'part_number': '',
            'description': 'Some part',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Part.query.count() == 0

    def test_create_part_duplicate_part_number(self, auth_client, db, sample_part):
        r = auth_client.post('/inventory/new', data={
            'part_number': 'CV-001',
            'description': 'Duplicate',
            'vendor': '', 'cost_price': '0', 'sell_price': '0',
            'quantity_on_hand': '0', 'low_stock_threshold': '2', 'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Part.query.filter_by(part_number='CV-001').count() == 1

    def test_edit_part(self, auth_client, db, sample_part):
        r = auth_client.post(f'/inventory/{sample_part.id}/edit', data={
            'part_number': 'CV-001',
            'description': 'Updated CV Boot Kit',
            'vendor': 'All Balls Racing',
            'cost_price': '22.00',
            'sell_price': '50.00',
            'quantity_on_hand': '5',
            'low_stock_threshold': '2',
            'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_part)
        assert sample_part.description == 'Updated CV Boot Kit'
        assert float(sample_part.sell_price) == 50.00

    def test_adjust_stock_add(self, auth_client, db, sample_part):
        original = sample_part.quantity_on_hand
        r = auth_client.post(f'/inventory/{sample_part.id}/adjust',
                             data={'delta': '3'}, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_part)
        assert sample_part.quantity_on_hand == original + 3

    def test_adjust_stock_remove(self, auth_client, db, sample_part):
        original = sample_part.quantity_on_hand
        r = auth_client.post(f'/inventory/{sample_part.id}/adjust',
                             data={'delta': '-2'}, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_part)
        assert sample_part.quantity_on_hand == original - 2

    def test_adjust_stock_cannot_go_negative(self, auth_client, db, sample_part):
        r = auth_client.post(f'/inventory/{sample_part.id}/adjust',
                             data={'delta': '-999'}, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(sample_part)
        assert sample_part.quantity_on_hand == 0

    def test_delete_part(self, auth_client, db, sample_part):
        part_id = sample_part.id
        r = auth_client.post(f'/inventory/{part_id}/delete', follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(Part, part_id) is None

    def test_search_parts_api(self, auth_client, sample_part):
        r = auth_client.get('/inventory/api/search?q=CV')
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]['part_number'] == 'CV-001'

    def test_search_parts_api_no_results(self, auth_client, sample_part):
        r = auth_client.get('/inventory/api/search?q=XXXXNOTFOUND')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_search_parts_api_empty_query(self, auth_client):
        r = auth_client.get('/inventory/api/search?q=')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_low_stock_filter(self, auth_client, db):
        low = Part(part_number='LOW-01', description='Low Stock Part',
                   quantity_on_hand=1, low_stock_threshold=3)
        ok = Part(part_number='OK-01', description='OK Stock Part',
                  quantity_on_hand=10, low_stock_threshold=3)
        db.session.add_all([low, ok])
        db.session.commit()
        r = auth_client.get('/inventory/?low_stock=1')
        assert r.status_code == 200
        assert b'LOW-01' in r.data
        assert b'OK-01' not in r.data
