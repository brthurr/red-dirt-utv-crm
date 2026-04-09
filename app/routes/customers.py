from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app import db
from app.models import Customer, Machine, RepairOrder
from datetime import date

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


def _save_customer_from_form(customer):
    customer.name = request.form['name'].strip()
    customer.phone = request.form.get('phone', '').strip()
    customer.email = request.form.get('email', '').strip()
    customer.address = request.form.get('address', '').strip()
    customer.city = request.form.get('city', '').strip()
    customer.state = request.form.get('state', 'TX').strip()
    customer.zip_code = request.form.get('zip_code', '').strip()
    customer.notes = request.form.get('notes', '').strip()


@customers_bp.route('/')
@login_required
def list_customers():
    q = request.args.get('q', '').strip()
    query = Customer.query
    if q:
        query = query.filter(Customer.name.ilike(f'%{q}%'))
    customers = query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers, q=q)


@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    """Step 1 of intake flow: create customer."""
    if request.method == 'POST':
        if not request.form.get('name', '').strip():
            flash('Customer name is required.', 'danger')
            return render_template('customers/form.html', customer=None, title='New Customer')
        customer = Customer()
        _save_customer_from_form(customer)
        db.session.add(customer)
        db.session.flush()
        # Check if we should continue to machine entry
        if request.form.get('continue_to_machine'):
            db.session.commit()
            return redirect(url_for('machines.new_machine', customer_id=customer.id, intake=1))
        db.session.commit()
        flash(f'Customer {customer.name} created.', 'success')
        return redirect(url_for('customers.view_customer', customer_id=customer.id))
    return render_template('customers/form.html', customer=None, title='New Customer')


@customers_bp.route('/<int:customer_id>')
@login_required
def view_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    return render_template('customers/detail.html', customer=customer)


@customers_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    if request.method == 'POST':
        if not request.form.get('name', '').strip():
            flash('Customer name is required.', 'danger')
            return render_template('customers/form.html', customer=customer, title='Edit Customer')
        _save_customer_from_form(customer)
        db.session.commit()
        flash('Customer updated.', 'success')
        return redirect(url_for('customers.view_customer', customer_id=customer.id))
    return render_template('customers/form.html', customer=customer, title='Edit Customer')


@customers_bp.route('/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer {customer.name} deleted.', 'info')
    return redirect(url_for('customers.list_customers'))
