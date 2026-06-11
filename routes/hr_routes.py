from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from database.db import get_db
from utils.decorators import login_required, role_required
from services.ai_service import rank_candidates, predict_performance, chatbot_response
import datetime

hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/dashboard')
@login_required
@role_required('hr')
def dashboard():
    db = get_db()
    total_employees = db.execute("SELECT COUNT(*) FROM employees WHERE status='active'").fetchone()[0]
    recent_employees = db.execute(
        "SELECT * FROM employees WHERE status='active' ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    dept_data = db.execute(
        "SELECT department, COUNT(*) as count FROM employees WHERE status='active' GROUP BY department"
    ).fetchall()
    ai_logs = db.execute(
        "SELECT al.*, e.name as emp_name FROM ai_logs al JOIN employees e ON al.employee_id = e.id ORDER BY al.created_at DESC LIMIT 5"
    ).fetchall()
    # Attendance today
    today = datetime.date.today().isoformat()
    att_today = db.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status IN ('present','wfh','late')", (today,)).fetchone()[0]
    # Candidates
    total_candidates = db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    pending_interviews = db.execute("SELECT COUNT(*) FROM candidates WHERE status='shortlisted'").fetchone()[0]

    return render_template('dashboard_hr.html',
        total_employees=total_employees,
        recent_employees=recent_employees,
        dept_data=dept_data,
        ai_logs=ai_logs,
        att_today=att_today,
        total_candidates=total_candidates,
        pending_interviews=pending_interviews,
    )


@hr_bp.route('/candidates', methods=['GET', 'POST'])
@login_required
@role_required('hr', 'admin')
def candidates():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            department = request.form.get('department', '').strip()
            skill_score = float(request.form.get('skill_score', 0))
            experience_years = int(request.form.get('experience_years', 0))
            interview_score = float(request.form.get('interview_score', 0))
            db.execute(
                "INSERT INTO candidates (name, email, department, skill_score, experience_years, interview_score) VALUES (?,?,?,?,?,?)",
                (name, email, department, skill_score, experience_years, interview_score)
            )
            db.commit()
            flash(f'Candidate {name} added!', 'success')
        elif action == 'status':
            cid = request.form.get('candidate_id')
            status = request.form.get('status')
            db.execute("UPDATE candidates SET status=? WHERE id=?", (status, cid))
            db.commit()
            flash('Candidate status updated.', 'success')

    dept_filter = request.args.get('department', '')
    query = "SELECT * FROM candidates"
    params = []
    if dept_filter:
        query += " WHERE department=?"
        params.append(dept_filter)
    query += " ORDER BY created_at DESC"

    raw_candidates = [dict(c) for c in db.execute(query, params).fetchall()]
    ranked = rank_candidates(raw_candidates)
    departments = db.execute("SELECT DISTINCT department FROM candidates").fetchall()

    return render_template('candidates.html', candidates=ranked, departments=departments, dept_filter=dept_filter)


@hr_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('hr', 'admin', 'manager')
def attendance():
    db = get_db()
    today = datetime.date.today().isoformat()

    if request.method == 'POST':
        emp_id = request.form.get('employee_id')
        date = request.form.get('date', today)
        status = request.form.get('status')
        db.execute(
            "INSERT INTO attendance (employee_id, date, status) VALUES (?,?,?) ON CONFLICT(employee_id, date) DO UPDATE SET status=?",
            (emp_id, date, status, status)
        )
        db.commit()
        flash('Attendance marked successfully!', 'success')

    date_filter = request.args.get('date', today)
    employees = db.execute("SELECT * FROM employees WHERE status='active' ORDER BY name").fetchall()
    att_records = db.execute(
        "SELECT a.*, e.name as emp_name, e.department FROM attendance a JOIN employees e ON a.employee_id=e.id WHERE a.date=? ORDER BY e.name",
        (date_filter,)
    ).fetchall()

    att_map = {r['employee_id']: r for r in att_records}
    present = sum(1 for r in att_records if r['status'] in ('present', 'wfh', 'late'))
    absent = sum(1 for r in att_records if r['status'] == 'absent')

    # Monthly attendance summary
    month_start = datetime.date.today().replace(day=1).isoformat()
    monthly = db.execute(
        "SELECT date, COUNT(*) as present_count FROM attendance WHERE date >= ? AND status IN ('present','wfh','late') GROUP BY date ORDER BY date",
        (month_start,)
    ).fetchall()

    return render_template('attendance.html',
        employees=employees, att_map=att_map, date_filter=date_filter,
        present=present, absent=absent, monthly=monthly, today=today
    )


@hr_bp.route('/performance-prediction')
@login_required
@role_required('hr', 'admin', 'manager')
def performance_prediction():
    db = get_db()
    employees = db.execute(
        "SELECT * FROM employees WHERE status='active' ORDER BY performance_score DESC"
    ).fetchall()

    # For each employee, compute attendance % (last 30 days)
    today = datetime.date.today()
    month_ago = (today - datetime.timedelta(days=30)).isoformat()

    predictions = []
    for emp in employees:
        att_count = db.execute(
            "SELECT COUNT(*) FROM attendance WHERE employee_id=? AND date>=? AND status IN ('present','wfh','late')",
            (emp['id'], month_ago)
        ).fetchone()[0]
        # assume 22 working days in 30 days
        att_pct = min((att_count / 22) * 100, 100)
        pred = predict_performance({
            'attendance_pct': att_pct,
            'task_completion': emp['task_completion'],
            'performance_score': emp['performance_score'],
        })
        predictions.append({
            'employee': emp,
            'prediction': pred,
            'att_pct': round(att_pct, 1),
        })

    # Sort by pred_score desc
    predictions.sort(key=lambda x: x['prediction']['pred_score'], reverse=True)
    return render_template('performance_prediction.html', predictions=predictions)


@hr_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    query = request.json.get('query', '')
    db = get_db()

    total_employees = db.execute("SELECT COUNT(*) FROM employees WHERE status='active'").fetchone()[0]
    avg_salary = db.execute("SELECT AVG(salary) FROM employees WHERE status='active'").fetchone()[0] or 0
    avg_performance = db.execute("SELECT AVG(performance_score) FROM employees WHERE status='active'").fetchone()[0] or 0
    dept_rows = db.execute("SELECT department, COUNT(*) as c FROM employees WHERE status='active' GROUP BY department").fetchall()
    dept_counts = {r['department']: r['c'] for r in dept_rows}
    top = db.execute("SELECT name, department, performance_score FROM employees WHERE status='active' ORDER BY performance_score DESC LIMIT 1").fetchone()
    latest_emp = db.execute("SELECT name, department, designation FROM employees WHERE status='active' ORDER BY created_at DESC LIMIT 1").fetchone()
    today = datetime.date.today().isoformat()
    att_today = db.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status IN ('present','wfh','late')", (today,)).fetchone()[0]

    stats = {
        'total_employees': total_employees,
        'avg_salary': avg_salary,
        'avg_performance': avg_performance,
        'dept_counts': dept_counts,
        'top_performer': dict(top) if top else {},
        'latest_employee': dict(latest_emp) if latest_emp else {},
        'attendance_today': att_today,
    }

    response = chatbot_response(query, stats)
    return jsonify({'response': response})
