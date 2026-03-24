from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, send_file, current_app)
from flask_login import login_required
from app import db
from app.models import Customer, Machine, RepairOrder, LineItem, RO_STATUSES
from app.pdf_utils import generate_pdf
from datetime import date
import io

ro_bp = Blueprint('repair_orders', __name__, url_prefix='/ro')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_ro_number():
    """Generate RO number: RO-YYYY-NNNN."""
    year = date.today().year
    prefix = f'RO-{year}-'
    last = (RepairOrder.query
            .filter(RepairOrder.ro_number.like(f'{prefix}%'))
            .order_by(RepairOrder.ro_number.desc())
            .first())
    if last:
        try:
            seq = int(last.ro_number.split('-')[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f'{prefix}{seq:04d}'


def _save_ro_header(ro):
    ro.complaint = request.form.get('complaint', '').strip()
    ro.work_performed = request.form.get('work_performed', '').strip()
    ro.technician = request.form.get('technician', '').strip()
    ro.status = request.form.get('status', 'Open')
    ro.tax_rate = float(request.form.get('tax_rate', 8.25)) / 100
    ro.has_customer_parts = bool(request.form.get('has_customer_parts'))
    ro.customer_parts_notes = request.form.get('customer_parts_notes', '').strip()
    date_in_str = request.form.get('date_in', '')
    date_out_str = request.form.get('date_out', '')
    if date_in_str:
        ro.date_in = date.fromisoformat(date_in_str)
    if date_out_str:
        ro.date_out = date.fromisoformat(date_out_str)
    else:
        ro.date_out = None
    machine_id = request.form.get('machine_id', type=int)
    ro.machine_id = machine_id if machine_id else None


def _save_line_items(ro):
    """Rebuild line items from POSTed arrays."""
    # Remove existing items
    for item in list(ro.line_items):
        db.session.delete(item)
    db.session.flush()

    types = request.form.getlist('item_type[]')
    descs = request.form.getlist('item_desc[]')
    qtys = request.form.getlist('item_qty[]')
    prices = request.form.getlist('item_price[]')
    supplied = request.form.getlist('item_customer_supplied[]')

    for i, (itype, desc) in enumerate(zip(types, descs)):
        if not desc.strip():
            continue
        item = LineItem(ro_id=ro.id)
        item.item_type = itype
        item.description = desc.strip()
        item.sort_order = i
        try:
            item.quantity = float(qtys[i]) if i < len(qtys) else 1
        except (ValueError, TypeError):
            item.quantity = 1
        try:
            item.unit_price = float(prices[i]) if i < len(prices) else 0
        except (ValueError, TypeError):
            item.unit_price = 0
        item.customer_supplied = str(i) in supplied or f'{i}' in supplied
        item.calculate_total()
        db.session.add(item)

    db.session.flush()
    ro.recalculate_totals()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@ro_bp.route('/')
@login_required
def list_ros():
    status_filter = request.args.get('status', '')
    q = request.args.get('q', '').strip()
    query = RepairOrder.query.join(Customer)
    if status_filter:
        query = query.filter(RepairOrder.status == status_filter)
    if q:
        query = query.filter(Customer.name.ilike(f'%{q}%'))
    ros = query.order_by(RepairOrder.date_in.desc()).all()
    return render_template('repair_orders/list.html',
                           ros=ros, statuses=RO_STATUSES,
                           status_filter=status_filter, q=q)


@ro_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_ro():
    customer_id = request.args.get('customer_id', type=int)
    machine_id = request.args.get('machine_id', type=int)
    intake = request.args.get('intake', 0, type=int)

    customers = Customer.query.order_by(Customer.name).all()
    customer = Customer.query.get(customer_id) if customer_id else None
    machines = Machine.query.filter_by(customer_id=customer_id).all() if customer_id else []
    machine = Machine.query.get(machine_id) if machine_id else None

    if request.method == 'POST':
        customer_id = request.form.get('customer_id', type=int)
        if not customer_id:
            flash('A customer is required.', 'danger')
            return redirect(url_for('repair_orders.new_ro'))

        ro = RepairOrder(
            ro_number=_next_ro_number(),
            customer_id=customer_id,
            date_in=date.today(),
        )
        db.session.add(ro)
        db.session.flush()
        _save_ro_header(ro)
        _save_line_items(ro)
        db.session.commit()
        flash(f'Repair Order {ro.ro_number} created.', 'success')
        return redirect(url_for('repair_orders.view_ro', ro_id=ro.id))

    return render_template('repair_orders/form.html',
                           ro=None,
                           customers=customers,
                           customer=customer,
                           machines=machines,
                           machine=machine,
                           statuses=RO_STATUSES,
                           intake=intake,
                           title='New Repair Order')


@ro_bp.route('/<int:ro_id>')
@login_required
def view_ro(ro_id):
    ro = RepairOrder.query.get_or_404(ro_id)
    return render_template('repair_orders/detail.html', ro=ro)


@ro_bp.route('/<int:ro_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ro(ro_id):
    ro = RepairOrder.query.get_or_404(ro_id)
    customers = Customer.query.order_by(Customer.name).all()
    machines = Machine.query.filter_by(customer_id=ro.customer_id).all()

    if request.method == 'POST':
        _save_ro_header(ro)
        _save_line_items(ro)
        db.session.commit()
        flash('Repair order updated.', 'success')
        return redirect(url_for('repair_orders.view_ro', ro_id=ro.id))

    return render_template('repair_orders/form.html',
                           ro=ro,
                           customers=customers,
                           customer=ro.customer,
                           machines=machines,
                           machine=ro.machine,
                           statuses=RO_STATUSES,
                           intake=0,
                           title=f'Edit {ro.ro_number}')


@ro_bp.route('/<int:ro_id>/delete', methods=['POST'])
@login_required
def delete_ro(ro_id):
    ro = RepairOrder.query.get_or_404(ro_id)
    db.session.delete(ro)
    db.session.commit()
    flash('Repair order deleted.', 'info')
    return redirect(url_for('repair_orders.list_ros'))


@ro_bp.route('/<int:ro_id>/status', methods=['POST'])
@login_required
def update_status(ro_id):
    ro = RepairOrder.query.get_or_404(ro_id)
    new_status = request.form.get('status')
    if new_status in RO_STATUSES:
        ro.status = new_status
        if new_status in ('Complete', 'Delivered') and not ro.date_out:
            ro.date_out = date.today()
        db.session.commit()
        flash(f'Status updated to {new_status}.', 'success')
    return redirect(url_for('repair_orders.view_ro', ro_id=ro_id))


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

@ro_bp.route('/<int:ro_id>/pdf/<doc_type>')
@login_required
def pdf(ro_id, doc_type):
    valid = ('intake', 'repair_order', 'parts_waiver', 'vehicle_release')
    if doc_type not in valid:
        flash('Unknown document type.', 'danger')
        return redirect(url_for('repair_orders.view_ro', ro_id=ro_id))
    ro = RepairOrder.query.get_or_404(ro_id)
    pdf_bytes = generate_pdf(doc_type, ro, current_app)
    filename = f'{ro.ro_number}_{doc_type}.pdf'
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=filename,
    )


@ro_bp.route('/api/machines_for_customer')
@login_required
def machines_for_customer():
    """AJAX endpoint: return machines for a customer as JSON."""
    from flask import jsonify
    customer_id = request.args.get('customer_id', type=int)
    machines = Machine.query.filter_by(customer_id=customer_id).all() if customer_id else []
    return jsonify([
        {'id': m.id, 'display': m.display_name or f'Machine #{m.id}'}
        for m in machines
    ])
