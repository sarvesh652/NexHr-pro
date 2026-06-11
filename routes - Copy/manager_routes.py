from flask import Blueprint, render_template
from database.db import get_db
from utils.decorators import login_required, role_required

manager_bp = Blueprint('manager', __name__)

@manager_bp.route('/dashboard')
@login_required
@role_required('manager')
def dashboard():
    db = get_db()
    total_employees = db.execute("SELECT COUNT(*) FROM employees WHERE status='active'").fetchone()[0]
    avg_performance = db.execute("SELECT AVG(performance_score) FROM employees WHERE status='active'").fetchone()[0]
    dept_data = db.execute(
        "SELECT department, COUNT(*) as count, AVG(performance_score) as avg_perf FROM employees WHERE status='active' GROUP BY department"
    ).fetchall()
    top_performers = db.execute(
        "SELECT * FROM employees WHERE status='active' ORDER BY performance_score DESC LIMIT 5"
    ).fetchall()
    employees = db.execute(
        "SELECT * FROM employees WHERE status='active' ORDER BY department, name"
    ).fetchall()

    return render_template('dashboard_manager.html',
        total_employees=total_employees,
        avg_performance=round(avg_performance or 0, 1),
        dept_data=dept_data,
        top_performers=top_performers,
        employees=employees
    )
