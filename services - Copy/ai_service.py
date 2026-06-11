import re

def rank_candidates(candidates: list) -> list:
    """
    Smart ranking: Overall Score = (Skill*40%) + (Experience*30%) + (Performance*30%)
    candidates: list of dicts with keys: name, skill_score, experience_years, performance_score
    """
    ranked = []
    for c in candidates:
        skill = min(float(c.get('skill_score', 0)), 100)
        exp_raw = min(float(c.get('experience_years', 0)), 15)  # cap at 15 years
        exp_score = (exp_raw / 15) * 100
        perf = min(float(c.get('performance_score', 0)), 100)

        overall = round((skill * 0.40) + (exp_score * 0.30) + (perf * 0.30), 1)
        c['overall_score'] = overall
        c['skill_score'] = round(skill, 1)
        c['exp_score'] = round(exp_score, 1)
        ranked.append(c)

    ranked.sort(key=lambda x: x['overall_score'], reverse=True)
    for i, c in enumerate(ranked):
        c['rank'] = i + 1
        if c['overall_score'] >= 75:
            c['rank_badge'] = 'high'
        elif c['overall_score'] >= 50:
            c['rank_badge'] = 'mid'
        else:
            c['rank_badge'] = 'low'
    return ranked


def predict_performance(employee: dict) -> dict:
    """
    Performance prediction based on attendance %, task completion, review score.
    Returns: label, confidence, suggestions
    """
    attendance = float(employee.get('attendance_pct', 75))
    task_completion = float(employee.get('task_completion', 70))
    review_score = float(employee.get('performance_score', 60))

    # Weighted score
    pred_score = (attendance * 0.30) + (task_completion * 0.35) + (review_score * 0.35)

    if pred_score >= 78:
        label = 'High Performer'
        icon = '🚀'
        color = 'success'
        suggestions = ['Promote to senior role', 'Assign mentorship responsibilities', 'Fast-track for leadership program']
    elif pred_score >= 55:
        label = 'Average Performer'
        icon = '📊'
        color = 'warning'
        suggestions = ['Provide skill development training', 'Set clear quarterly KPIs', 'Schedule regular 1-on-1 check-ins']
    else:
        label = 'At Risk'
        icon = '⚠️'
        color = 'danger'
        suggestions = ['Immediate performance improvement plan', 'Daily task monitoring required', 'HR counseling recommended']

    return {
        'label': label,
        'icon': icon,
        'color': color,
        'pred_score': round(pred_score, 1),
        'suggestions': suggestions,
        'attendance': attendance,
        'task_completion': task_completion,
        'review_score': review_score,
    }


def chatbot_response(query: str, db_stats: dict) -> str:
    """Rule-based HR chatbot"""
    q = query.lower().strip()

    # Employee count queries
    if any(x in q for x in ['how many employee', 'total employee', 'employee count', 'staff count']):
        dept_match = None
        for dept in ['engineering', 'marketing', 'sales', 'hr', 'finance']:
            if dept in q:
                dept_match = dept.capitalize()
                break
        if dept_match and dept_match in db_stats.get('dept_counts', {}):
            count = db_stats['dept_counts'][dept_match]
            return f"There are <strong>{count}</strong> employees in the {dept_match} department."
        return f"There are currently <strong>{db_stats.get('total_employees', 'N/A')}</strong> active employees in the system."

    if 'department' in q and ('list' in q or 'show' in q or 'which' in q):
        depts = list(db_stats.get('dept_counts', {}).keys())
        return f"Current departments: <strong>{', '.join(depts)}</strong>"

    if any(x in q for x in ['avg salary', 'average salary', 'mean salary', 'salary average']):
        return f"The average employee salary is <strong>${db_stats.get('avg_salary', 0):,.0f}</strong>."

    if any(x in q for x in ['top performer', 'best performer', 'highest performer']):
        top = db_stats.get('top_performer', {})
        if top:
            return f"Top performer is <strong>{top.get('name')}</strong> ({top.get('department')}) with a score of <strong>{top.get('performance_score')}%</strong>."
        return "No performance data available yet."

    if any(x in q for x in ['attendance', 'present today', 'who is in']):
        return f"Today's attendance: <strong>{db_stats.get('attendance_today', 0)}</strong> employees marked present."

    if any(x in q for x in ['avg performance', 'average performance', 'performance average']):
        return f"Average performance score across all employees: <strong>{db_stats.get('avg_performance', 0):.1f}%</strong>."

    if any(x in q for x in ['recent hire', 'new employee', 'recently added', 'latest employee']):
        emp = db_stats.get('latest_employee', {})
        if emp:
            return f"Most recent hire: <strong>{emp.get('name')}</strong> — {emp.get('designation')} in {emp.get('department')}."
        return "No recent hire data available."

    if any(x in q for x in ['hello', 'hi ', 'hey', 'greet']):
        return "Hello! 👋 I'm your HR Assistant. Ask me about employee counts, performance, salaries, or attendance!"

    if any(x in q for x in ['help', 'what can you', 'commands', 'options']):
        return ("I can answer: <br>• <em>How many employees in Engineering?</em><br>"
                "• <em>What is the average salary?</em><br>"
                "• <em>Who is the top performer?</em><br>"
                "• <em>Show all departments</em><br>"
                "• <em>Average performance score</em><br>"
                "• <em>Who was recently hired?</em>")

    return "I'm not sure about that. Try asking about <em>employee count, salary, performance, or attendance</em>. Type <strong>help</strong> to see all options."

