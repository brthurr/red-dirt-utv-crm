"""
Unit tests for DirtDesk models.

Tests cover business logic (totals, status flags, properties) without
going through the HTTP layer.
"""
from datetime import datetime
import pytest
from app.models import (Customer, Machine, RepairOrder, LineItem,
                        Part, IntakePhoto, CustomerAuthorization)


class TestCustomer:
    def test_full_address_all_fields(self, db):
        c = Customer(name='Bob', address='123 Main', city='Waller',
                     state='TX', zip_code='77484')
        assert c.full_address == '123 Main, Waller, TX, 77484'

    def test_full_address_partial(self, db):
        c = Customer(name='Bob', city='Waller', state='TX')
        assert c.full_address == 'Waller, TX'

    def test_full_address_empty(self, db):
        c = Customer(name='Bob')
        assert c.full_address == ''

    def test_repr(self, db):
        c = Customer(name='Jane Rider')
        assert 'Jane Rider' in repr(c)


class TestMachine:
    def test_display_name_full(self, db, sample_customer):
        m = Machine(customer_id=sample_customer.id,
                    year='2022', make='Polaris', model='RZR Pro XP')
        assert m.display_name == '2022 Polaris RZR Pro XP'

    def test_display_name_partial(self, db, sample_customer):
        m = Machine(customer_id=sample_customer.id, make='Can-Am')
        assert m.display_name == 'Can-Am'

    def test_display_name_empty(self, db, sample_customer):
        m = Machine(customer_id=sample_customer.id)
        assert m.display_name == ''

    def test_repr(self, db, sample_machine):
        assert 'Machine' in repr(sample_machine)


class TestLineItem:
    def test_calculate_total(self, db):
        item = LineItem(item_type='part', description='Test',
                        quantity=3, unit_price=10.00)
        item.calculate_total()
        assert float(item.line_total) == 30.00

    def test_calculate_total_fractional_hours(self, db):
        item = LineItem(item_type='labor', description='Labor',
                        quantity=1.5, unit_price=95.00)
        item.calculate_total()
        assert float(item.line_total) == 142.50

    def test_calculate_total_zero(self, db):
        item = LineItem(item_type='part', description='Test',
                        quantity=0, unit_price=50.00)
        item.calculate_total()
        assert float(item.line_total) == 0.00


class TestRepairOrder:
    def test_recalculate_totals(self, db, sample_ro):
        # part: 1 x $45 = $45, labor: 2 x $95 = $190
        assert float(sample_ro.parts_total) == 45.00
        assert float(sample_ro.labor_total) == 190.00

    def test_subtotal(self, db, sample_ro):
        assert sample_ro.subtotal == 235.00

    def test_tax_amount(self, db, sample_ro):
        expected = round(235.00 * 0.0825, 2)
        assert sample_ro.tax_amount == expected

    def test_grand_total(self, db, sample_ro):
        expected = round(235.00 + 235.00 * 0.0825, 2)
        assert float(sample_ro.grand_total) == expected

    def test_grand_total_zero_tax(self, db, sample_customer):
        ro = RepairOrder(ro_number='RO-2026-XXXX', customer_id=sample_customer.id,
                         tax_rate=0.0)
        db.session.add(ro)
        db.session.flush()
        item = LineItem(ro_id=ro.id, item_type='part', description='Part',
                        quantity=1, unit_price=100.00)
        item.calculate_total()
        db.session.add(item)
        db.session.flush()
        ro.recalculate_totals()
        assert float(ro.grand_total) == 100.00

    def test_pending_authorizations(self, db, sample_ro):
        auth_pending = CustomerAuthorization(ro_id=sample_ro.id,
                                             description='Fix CV boot',
                                             approved=None)
        auth_approved = CustomerAuthorization(ro_id=sample_ro.id,
                                              description='Replace filter',
                                              approved=True)
        db.session.add_all([auth_pending, auth_approved])
        db.session.commit()
        pending = sample_ro.pending_authorizations
        assert len(pending) == 1
        assert pending[0].description == 'Fix CV boot'

    def test_repr(self, db, sample_ro):
        assert 'RO-2026-0001' in repr(sample_ro)


class TestPart:
    def test_is_low_stock_below_threshold(self, db):
        p = Part(part_number='X1', description='Test', quantity_on_hand=1,
                 low_stock_threshold=2)
        assert p.is_low_stock is True

    def test_is_low_stock_at_threshold(self, db):
        p = Part(part_number='X2', description='Test', quantity_on_hand=2,
                 low_stock_threshold=2)
        assert p.is_low_stock is True

    def test_is_not_low_stock(self, db):
        p = Part(part_number='X3', description='Test', quantity_on_hand=10,
                 low_stock_threshold=2)
        assert p.is_low_stock is False

    def test_margin_calculation(self, db):
        p = Part(part_number='X4', description='Test',
                 cost_price=20.00, sell_price=45.00)
        expected = round((45 - 20) / 45 * 100, 1)
        assert p.margin == expected

    def test_margin_zero_sell_price(self, db):
        p = Part(part_number='X5', description='Test',
                 cost_price=20.00, sell_price=0.00)
        assert p.margin == 0.0

    def test_repr(self, db, sample_part):
        assert 'CV-001' in repr(sample_part)


class TestCustomerAuthorization:
    def test_status_label_pending(self, db, sample_ro):
        auth = CustomerAuthorization(ro_id=sample_ro.id,
                                     description='Check brakes', approved=None)
        assert auth.status_label == 'Pending'
        assert auth.status_badge == 'warning'

    def test_status_label_approved(self, db, sample_ro):
        auth = CustomerAuthorization(ro_id=sample_ro.id,
                                     description='Check brakes', approved=True)
        assert auth.status_label == 'Approved'
        assert auth.status_badge == 'success'

    def test_status_label_declined(self, db, sample_ro):
        auth = CustomerAuthorization(ro_id=sample_ro.id,
                                     description='Check brakes', approved=False)
        assert auth.status_label == 'Declined'
        assert auth.status_badge == 'danger'
