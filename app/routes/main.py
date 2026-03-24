from flask import Blueprint, render_template
from flask_login import login_required
from app.models import RepairOrder, Customer, Machine

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    open_statuses = ['Open', 'In Progress', 'Draft']
    open_ros = (RepairOrder.query
                .filter(RepairOrder.status.in_(open_statuses))
                .order_by(RepairOrder.date_in.desc())
                .all())
    recent_complete = (RepairOrder.query
                       .filter(RepairOrder.status.in_(['Complete', 'Delivered']))
                       .order_by(RepairOrder.date_out.desc())
                       .limit(5)
                       .all())
    customer_count = Customer.query.count()
    machine_count = Machine.query.count()
    total_ro_count = RepairOrder.query.count()
    return render_template(
        'dashboard.html',
        open_ros=open_ros,
        recent_complete=recent_complete,
        customer_count=customer_count,
        machine_count=machine_count,
        total_ro_count=total_ro_count,
    )
