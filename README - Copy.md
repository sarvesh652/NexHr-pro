# 🚀 AI HR Intelligence System v2.0 — Enterprise Edition

## ✨ What's New in v2.0

### 🤖 AI Features
| Feature | Description |
|---|---|
| **Smart Candidate Ranking** | Formula: `(Skill×40%) + (Experience×30%) + (Interview×30%)` with gold/silver/bronze rank |
| **AI Performance Prediction** | Predicts High Performer / Average / At Risk based on attendance, task completion, review score |
| **HR Chatbot** | Rule-based bot — answers questions about headcount, salary, performance, attendance |

### 📊 Dashboard Upgrades
- **Animated stat counters** — numbers count up on load
- **Chart.js charts** — Donut chart (dept distribution), Bar chart (salary by dept), Line chart (attendance trend), Bar chart (performance scores)
- **Hiring pipeline stats** — candidate count, pending interviews, offers made

### 🗂 New Modules
- **Candidate Ranking System** — Full pipeline: Applied → Shortlisted → Interviewed → Offered → Rejected
- **Attendance Tracker** — Mark daily attendance (Present / WFH / Late / Absent), view trend chart
- **Performance Prediction** — Card view per employee with SVG score rings and improvement suggestions

### 🎨 UI Upgrades
- Toast notification system
- Animated stat counters
- Chatbot widget (bottom-right, all pages)
- Mini progress bars in tables
- Status pills with color coding
- Responsive 2-column forms

---

## 🏗 Project Structure
```
AI_HR_Intelligence_System/
├── app.py                    # Flask app factory
├── config.py                 # Config (SECRET_KEY, DB path)
├── requirements.txt
├── database/
│   └── db.py                 # SQLite init + seeding
├── routes/
│   ├── auth_routes.py        # Login / logout
│   ├── admin_routes.py       # Admin dashboard + employees + users
│   ├── hr_routes.py          # HR dashboard + candidates + attendance + prediction + chatbot
│   └── manager_routes.py     # Manager dashboard
├── services/
├── templates/
│   ├── base.html             # Layout + chatbot widget + Chart.js
│   ├── dashboard_admin.html  # Admin dashboard with charts
│   ├── dashboard_hr.html     # HR dashboard with charts
│   ├── dashboard_manager.html
│   ├── candidates.html       # Smart ranking table
│   ├── attendance.html       # Attendance tracker + trend chart
│   ├── performance_prediction.html  # AI prediction cards
│   ├── view_employees.html
│   ├── add_employee.html     # Upgraded with exp + task fields
│   ├── edit_employee.html
│   ├── manage_users.html
│   └── login.html
└── static/css/style.css
```

## 🗄 Database Schema
```sql
users          -- id, name, email, password, role (admin/hr/manager)
employees      -- id, name, email, phone, department, designation, salary,
               --   performance_score, experience_years, task_completion, status
attendance     -- id, employee_id, date, status (present/absent/late/wfh)
candidates     -- id, name, email, department, skill_score, experience_years,
```

## 🔐 Default Login Credentials
| Role | Email | Password |
|---|---|---|
| Admin | admin@hrpro.com | Admin@123 |
| HR | hr@hrpro.com | Hr@123 |
| Manager | manager@hrpro.com | Manager@123 |

## 🚀 Run Locally
```bash
pip install -r requirements.txt
python app.py
# Open: http://127.0.0.1:5000
```

## 🏆 Tech Stack
- **Backend**: Python 3.x + Flask 3.0
- **Database**: SQLite (production: swap to PostgreSQL)
- **Frontend**: Vanilla HTML/CSS + Chart.js 4.4 + Jinja2
- **AI**: Keyword NLP (no external API needed)
- **Auth**: Flask session + Werkzeug password hashing

## 📈 AI Scoring Formulas
```
Candidate Rank = (skill_score × 0.40) + (exp_score × 0.30) + (interview_score × 0.30)
Perf Prediction = (attendance × 0.30) + (task_completion × 0.35) + (review_score × 0.35)
```
