from datetime import datetime, date
from flask_login import UserMixin
from app import db, login_manager


# ---------------------------------------------------------------------------
# Single-user auth shim — no DB table needed
# ---------------------------------------------------------------------------

class ShopUser(UserMixin):
    """Synthetic user object for the single shop owner."""
    id = 1
    username = 'owner'

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    if str(user_id) == '1':
        return ShopUser()
    return None


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    city = db.Column(db.String(80))
    state = db.Column(db.String(40), default='TX')
    zip_code = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    machines = db.relationship('Machine', backref='customer', lazy=True,
                               cascade='all, delete-orphan')
    repair_orders = db.relationship('RepairOrder', backref='customer', lazy=True,
                                    cascade='all, delete-orphan')

    @property
    def full_address(self):
        parts = [self.address, self.city, self.state, self.zip_code]
        return ', '.join(p for p in parts if p)

    def __repr__(self):
        return f'<Customer {self.name}>'


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------

class Machine(db.Model):
    __tablename__ = 'machines'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    year = db.Column(db.String(10))
    make = db.Column(db.String(80))
    model = db.Column(db.String(80))
    engine_cc = db.Column(db.String(40))
    vin = db.Column(db.String(60))
    odometer_hours = db.Column(db.String(40))
    color = db.Column(db.String(60))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    repair_orders = db.relationship('RepairOrder', backref='machine', lazy=True)

    @property
    def display_name(self):
        parts = [self.year, self.make, self.model]
        return ' '.join(p for p in parts if p)

    def __repr__(self):
        return f'<Machine {self.display_name}>'


# ---------------------------------------------------------------------------
# RepairOrder
# ---------------------------------------------------------------------------

RO_STATUSES = ['Draft', 'Open', 'In Progress', 'Complete', 'Delivered']


class RepairOrder(db.Model):
    __tablename__ = 'repair_orders'

    id = db.Column(db.Integer, primary_key=True)
    ro_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=True)

    date_in = db.Column(db.Date, default=date.today)
    date_out = db.Column(db.Date, nullable=True)

    complaint = db.Column(db.Text)           # Customer-reported concern
    work_performed = db.Column(db.Text)      # Tech notes / work done
    technician = db.Column(db.String(80))

    status = db.Column(db.String(30), default='Open')

    # Totals — computed from line items but stored for quick display
    parts_total = db.Column(db.Numeric(10, 2), default=0)
    labor_total = db.Column(db.Numeric(10, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 4), default=0.0825)  # 8.25% TX default
    grand_total = db.Column(db.Numeric(10, 2), default=0)

    # Customer-supplied parts flag
    has_customer_parts = db.Column(db.Boolean, default=False)
    customer_parts_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    line_items = db.relationship('LineItem', backref='repair_order', lazy=True,
                                 cascade='all, delete-orphan',
                                 order_by='LineItem.sort_order')

    def recalculate_totals(self):
        parts = sum(
            float(i.line_total) for i in self.line_items if i.item_type == 'part'
        )
        labor = sum(
            float(i.line_total) for i in self.line_items if i.item_type == 'labor'
        )
        self.parts_total = round(parts, 2)
        self.labor_total = round(labor, 2)
        subtotal = parts + labor
        self.grand_total = round(subtotal + subtotal * float(self.tax_rate or 0), 2)

    @property
    def subtotal(self):
        return float(self.parts_total or 0) + float(self.labor_total or 0)

    @property
    def tax_amount(self):
        return round(self.subtotal * float(self.tax_rate or 0), 2)

    def __repr__(self):
        return f'<RepairOrder {self.ro_number}>'


# ---------------------------------------------------------------------------
# LineItem
# ---------------------------------------------------------------------------

ITEM_TYPES = ['part', 'labor']


class LineItem(db.Model):
    __tablename__ = 'line_items'

    id = db.Column(db.Integer, primary_key=True)
    ro_id = db.Column(db.Integer, db.ForeignKey('repair_orders.id'), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)   # 'part' | 'labor'
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    line_total = db.Column(db.Numeric(10, 2), default=0)
    sort_order = db.Column(db.Integer, default=0)
    customer_supplied = db.Column(db.Boolean, default=False)

    def calculate_total(self):
        self.line_total = round(float(self.quantity or 0) * float(self.unit_price or 0), 2)

    def __repr__(self):
        return f'<LineItem {self.item_type}: {self.description}>'
