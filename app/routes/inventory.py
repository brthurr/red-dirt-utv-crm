from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, jsonify)
from flask_login import login_required
from app import db
from app.models import Part

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


def _save_part_from_form(part):
    part.part_number = request.form.get('part_number', '').strip()
    part.description = request.form.get('description', '').strip()
    part.vendor = request.form.get('vendor', '').strip()
    part.notes = request.form.get('notes', '').strip()
    try:
        part.cost_price = float(request.form.get('cost_price', 0))
    except (ValueError, TypeError):
        part.cost_price = 0
    try:
        part.sell_price = float(request.form.get('sell_price', 0))
    except (ValueError, TypeError):
        part.sell_price = 0
    try:
        part.quantity_on_hand = int(request.form.get('quantity_on_hand', 0))
    except (ValueError, TypeError):
        part.quantity_on_hand = 0
    try:
        part.low_stock_threshold = int(request.form.get('low_stock_threshold', 2))
    except (ValueError, TypeError):
        part.low_stock_threshold = 2


@inventory_bp.route('/')
@login_required
def list_parts():
    q = request.args.get('q', '').strip()
    low_stock = request.args.get('low_stock', '')
    query = Part.query
    if q:
        query = query.filter(
            db.or_(
                Part.part_number.ilike(f'%{q}%'),
                Part.description.ilike(f'%{q}%'),
                Part.vendor.ilike(f'%{q}%'),
            )
        )
    parts = query.order_by(Part.description).all()
    if low_stock:
        parts = [p for p in parts if p.is_low_stock]
    return render_template('inventory/list.html', parts=parts, q=q, low_stock=low_stock)


@inventory_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_part():
    if request.method == 'POST':
        part_number = request.form.get('part_number', '').strip()
        description = request.form.get('description', '').strip()
        if not part_number or not description:
            flash('Part number and description are required.', 'danger')
            return render_template('inventory/form.html', part=None, title='New Part')
        if Part.query.filter_by(part_number=part_number).first():
            flash(f'Part number {part_number} already exists.', 'danger')
            return render_template('inventory/form.html', part=None, title='New Part')
        part = Part()
        _save_part_from_form(part)
        db.session.add(part)
        db.session.commit()
        flash(f'Part {part.part_number} added to inventory.', 'success')
        return redirect(url_for('inventory.list_parts'))
    return render_template('inventory/form.html', part=None, title='New Part')


@inventory_bp.route('/<int:part_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    part = Part.query.get_or_404(part_id)
    if request.method == 'POST':
        part_number = request.form.get('part_number', '').strip()
        description = request.form.get('description', '').strip()
        if not part_number or not description:
            flash('Part number and description are required.', 'danger')
            return render_template('inventory/form.html', part=part, title=f'Edit {part.part_number}')
        existing = Part.query.filter_by(part_number=part_number).first()
        if existing and existing.id != part.id:
            flash(f'Part number {part_number} is already used by another part.', 'danger')
            return render_template('inventory/form.html', part=part, title=f'Edit {part.part_number}')
        _save_part_from_form(part)
        db.session.commit()
        flash('Part updated.', 'success')
        return redirect(url_for('inventory.list_parts'))
    return render_template('inventory/form.html', part=part, title=f'Edit {part.part_number}')


@inventory_bp.route('/<int:part_id>/adjust', methods=['POST'])
@login_required
def adjust_stock(part_id):
    """Quick stock quantity adjustment (+ or -)."""
    part = Part.query.get_or_404(part_id)
    try:
        delta = int(request.form.get('delta', 0))
    except (ValueError, TypeError):
        delta = 0
    part.quantity_on_hand = max(0, part.quantity_on_hand + delta)
    db.session.commit()
    flash(f'Stock updated: {part.part_number} now has {part.quantity_on_hand} on hand.', 'success')
    return redirect(url_for('inventory.list_parts'))


@inventory_bp.route('/<int:part_id>/delete', methods=['POST'])
@login_required
def delete_part(part_id):
    part = Part.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    flash(f'Part {part.part_number} deleted.', 'info')
    return redirect(url_for('inventory.list_parts'))


@inventory_bp.route('/api/search')
@login_required
def search_parts():
    """AJAX: search parts catalog for RO line item lookup."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    parts = Part.query.filter(
        db.or_(
            Part.part_number.ilike(f'%{q}%'),
            Part.description.ilike(f'%{q}%'),
        )
    ).limit(10).all()
    return jsonify([
        {
            'id': p.id,
            'part_number': p.part_number,
            'description': p.description,
            'sell_price': float(p.sell_price or 0),
            'quantity_on_hand': p.quantity_on_hand,
        }
        for p in parts
    ])
