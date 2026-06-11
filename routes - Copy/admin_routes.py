from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from database.db import get_db
from utils.decorators import login_required, role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    db = get_db()
    total_employees = db.execute("SELECT COUNT(*) FROM employees WHERE status='active'").fetchone()[0]
    total_departments = db.execute("SELECT COUNT(DISTINCT department) FROM employees").fetchone()[0]
    avg_salary = db.execute("SELECT AVG(salary) FROM employees WHERE status='active'").fetchone()[0]
    avg_performance = db.execute("SELECT AVG(performance_score) FROM employees WHERE status='active'").fetchone()[0]
    total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_candidates = db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    offered = db.execute("SELECT COUNT(*) FROM candidates WHERE status='offered'").fetchone()[0]

    dept_data = db.execute(
        "SELECT department, COUNT(*) as count FROM employees WHERE status='active' GROUP BY department"
    ).fetchall()

    # Monthly growth — last 6 months
    monthly_growth = db.execute(
        """SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
           FROM employees WHERE status='active'
           GROUP BY month ORDER BY month DESC LIMIT 6"""
    ).fetchall()

    recent_employees = db.execute(
        "SELECT * FROM employees WHERE status='active' ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    salary_by_dept = db.execute(
        "SELECT department, AVG(salary) as avg_sal FROM employees WHERE status='active' GROUP BY department"
    ).fetchall()

    return render_template('dashboard_admin.html',
        total_employees=total_employees,
        total_departments=total_departments,
        avg_salary=round(avg_salary or 0, 2),
        avg_performance=round(avg_performance or 0, 1),
        total_users=total_users,
        total_candidates=total_candidates,
        offered=offered,
        dept_data=dept_data,
        recent_employees=recent_employees,
        monthly_growth=list(reversed(monthly_growth)),
        salary_by_dept=salary_by_dept,
    )

@admin_bp.route('/employees')
@login_required
@role_required('admin', 'hr')
def view_employees():
    db = get_db()
    search = request.args.get('search', '')
    dept_filter = request.args.get('department', '')

    query = "SELECT * FROM employees WHERE status='active'"
    params = []
    if search:
        query += " AND (name LIKE ? OR email LIKE ? OR designation LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if dept_filter:
        query += " AND department = ?"
        params.append(dept_filter)
    query += " ORDER BY created_at DESC"

    employees = db.execute(query, params).fetchall()
    departments = db.execute("SELECT DISTINCT department FROM employees WHERE status='active'").fetchall()

    return render_template('view_employees.html', employees=employees, departments=departments,
                           search=search, dept_filter=dept_filter)

@admin_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'hr')
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()
        salary = request.form.get('salary', 0)
        performance_score = request.form.get('performance_score', 0)
        experience_years = request.form.get('experience_years', 0)
        task_completion = request.form.get('task_completion', 70)

        if not all([name, email, department, designation, salary]):
            flash('All required fields must be filled.', 'danger')
            return render_template('add_employee.html')

        db = get_db()
        try:
            db.execute(
                "INSERT INTO employees (name, email, phone, department, designation, salary, performance_score, experience_years, task_completion) VALUES (?,?,?,?,?,?,?,?,?)",
                (name, email, phone, department, designation, int(salary), int(performance_score), int(experience_years), int(task_completion))
            )
            db.commit()
            flash(f'Employee {name} added successfully!', 'success')
            return redirect(url_for('admin.view_employees'))
        except Exception as e:
            flash(f'Error: Email already exists or invalid data.', 'danger')

    return render_template('add_employee.html')

@admin_bp.route('/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'hr')
def edit_employee(emp_id):
    db = get_db()
    employee = db.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()

    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('admin.view_employees'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()
        salary = request.form.get('salary', 0)
        performance_score = request.form.get('performance_score', 0)
        experience_years = request.form.get('experience_years', 0)
        task_completion = request.form.get('task_completion', 70)

        db.execute(
            "UPDATE employees SET name=?, phone=?, department=?, designation=?, salary=?, performance_score=?, experience_years=?, task_completion=? WHERE id=?",
            (name, phone, department, designation, int(salary), int(performance_score), int(experience_years), int(task_completion), emp_id)
        )
        db.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('admin.view_employees'))

    return render_template('edit_employee.html', employee=employee)

@admin_bp.route('/employees/delete/<int:emp_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_employee(emp_id):
    db = get_db()
    db.execute("UPDATE employees SET status='inactive' WHERE id = ?", (emp_id,))
    db.commit()
    flash('Employee removed from system.', 'info')
    return redirect(url_for('admin.view_employees'))

@admin_bp.route('/users')
@login_required
@role_required('admin')
def manage_users():
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return render_template('manage_users.html', users=users)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '')

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
            (name, email, generate_password_hash(password), role)
        )
        db.commit()
        flash(f'User {name} created successfully!', 'success')
    except:
        flash('Error: Email already exists.', 'danger')

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash('User deleted.', 'info')
    return redirect(url_for('admin.manage_users'))
