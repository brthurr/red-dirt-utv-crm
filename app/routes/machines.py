import json
from datetime import date
from urllib.request import urlopen
from urllib.parse import quote
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required
from app import db
from app.models import Customer, Machine
from app.utv_models import UTV_MODELS

machines_bp = Blueprint('machines', __name__, url_prefix='/machines')

UTV_MAKES = [
    'Arctic Cat', 'Can-Am', 'CFMOTO', 'Club Car', 'E-Z-GO',
    'Hisun', 'Honda', 'John Deere', 'Kawasaki', 'Kioti',
    'Kubota', 'Kymco', 'Massimo', 'Polaris', 'Suzuki',
    'Textron', 'Yamaha',
]

ENGINE_SIZES = [
    '200cc', '250cc', '300cc', '400cc', '450cc', '500cc',
    '570cc', '600cc', '650cc', '700cc', '750cc', '800cc',
    '850cc', '900cc', '950cc', '1000cc', '1000cc Turbo',
    '1000cc Turbo R', '1000cc Turbo RR', '1100cc', '1200cc',
]

MACHINE_COLORS = [
    'Black', 'White', 'Silver', 'Gray', 'Red', 'Blue', 'Green',
    'Orange', 'Yellow', 'Tan', 'Camo', 'Burgundy', 'Purple',
    'Lime Green', 'Midnight Blue', 'Desert Sand', 'Matte Black',
]


def _form_context():
    """Shared template context for year/make/engine/color dropdowns."""
    current_year = date.today().year
    years = list(range(current_year + 1, 1969, -1))
    return dict(years=years, utv_makes=UTV_MAKES,
                engine_sizes=ENGINE_SIZES, machine_colors=MACHINE_COLORS)


def _save_machine_from_form(machine):
    machine.year = request.form.get('year', '').strip()
    machine.make = request.form.get('make', '').strip()
    machine.model = request.form.get('model', '').strip()
    machine.engine_cc = request.form.get('engine_cc', '').strip()
    machine.vin = request.form.get('vin', '').strip()
    machine.odometer_hours = request.form.get('odometer_hours', '').strip()
    machine.color = request.form.get('color', '').strip()
    machine.notes = request.form.get('notes', '').strip()


# ---------------------------------------------------------------------------
# AJAX: model lookup via NHTSA vPIC
# ---------------------------------------------------------------------------

@machines_bp.route('/api/models')
@login_required
def api_models():
    make = request.args.get('make', '').strip()
    year = request.args.get('year', '').strip()
    if not make:
        return jsonify([])

    # Check curated static data first (case-insensitive key match)
    for key, models in UTV_MODELS.items():
        if key.lower() == make.lower():
            return jsonify(models)

    # Fall back to NHTSA vPIC for makes not in our curated list
    try:
        if year and year.isdigit():
            url = (
                f'https://vpic.nhtsa.dot.gov/api/vehicles/'
                f'GetModelsForMakeYear/make/{quote(make)}/modelyear/{year}?format=json'
            )
        else:
            url = (
                f'https://vpic.nhtsa.dot.gov/api/vehicles/'
                f'GetModelsForMake/{quote(make)}?format=json'
            )
        with urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        models = sorted({r['Model_Name'] for r in data.get('Results', []) if r.get('Model_Name')})
        return jsonify(models)
    except Exception:
        return jsonify([])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@machines_bp.route('/new')
@login_required
def new_machine(customer_id=None):
    """GET: show form. customer_id may come from query string (intake flow)."""
    customer_id = request.args.get('customer_id', type=int)
    intake = request.args.get('intake', 0, type=int)
    customer = db.get_or_404(Customer, customer_id) if customer_id else None
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('machines/form.html',
                           machine=None,
                           customer=customer,
                           customers=customers,
                           intake=intake,
                           title='New Machine',
                           **_form_context())


@machines_bp.route('/new', methods=['POST'])
@login_required
def create_machine():
    customer_id = request.form.get('customer_id', type=int)
    intake = request.form.get('intake', 0, type=int)
    if not customer_id:
        flash('A customer must be selected.', 'danger')
        return redirect(url_for('machines.new_machine'))
    customer = db.get_or_404(Customer, customer_id)
    machine = Machine(customer_id=customer_id)
    _save_machine_from_form(machine)
    db.session.add(machine)
    db.session.flush()
    if intake and request.form.get('continue_to_ro'):
        db.session.commit()
        return redirect(url_for('repair_orders.new_ro',
                                customer_id=customer_id,
                                machine_id=machine.id,
                                intake=1))
    db.session.commit()
    flash(f'Machine added for {customer.name}.', 'success')
    return redirect(url_for('customers.view_customer', customer_id=customer_id))


@machines_bp.route('/<int:machine_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_machine(machine_id):
    machine = db.get_or_404(Machine, machine_id)
    customers = Customer.query.order_by(Customer.name).all()
    if request.method == 'POST':
        _save_machine_from_form(machine)
        db.session.commit()
        flash('Machine updated.', 'success')
        return redirect(url_for('customers.view_customer', customer_id=machine.customer_id))
    return render_template('machines/form.html',
                           machine=machine,
                           customer=machine.customer,
                           customers=customers,
                           intake=0,
                           title='Edit Machine',
                           **_form_context())


@machines_bp.route('/<int:machine_id>/delete', methods=['POST'])
@login_required
def delete_machine(machine_id):
    machine = db.get_or_404(Machine, machine_id)
    customer_id = machine.customer_id
    db.session.delete(machine)
    db.session.commit()
    flash('Machine removed.', 'info')
    return redirect(url_for('customers.view_customer', customer_id=customer_id))
