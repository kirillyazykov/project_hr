from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/RobotComp.ru/Desktop/Обучение/ООП Python/project_test/employees.db' # Внесите адрес расположения файла db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.Text, nullable=False)
    position = db.Column(db.Text, nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    manager_id = db.Column(db.Integer)

POSITION_LEVELS = {
    "Big Boss": 7,
    "Boss": 6,
    "CEO": 5,
    "Manager": 4,
    "Team Lead": 3,
    "Senior Developer": 2,
    "Developer": 1
}

@app.route('/')
def index():
    sort_by = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    
    search = request.args.get('search', '')
    
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 20 строк на страницу
    
    query = Employee.query
    
    if search:
        query = query.filter(Employee.full_name.contains(search))
    
    if sort_by == 'name':
        if order == 'desc':
            query = query.order_by(Employee.full_name.desc())
        else:
            query = query.order_by(Employee.full_name.asc())
    elif sort_by == 'position':
        from sqlalchemy import case
        
        position_order = case(
            (Employee.position == "Big Boss", 7),
            (Employee.position == "Boss", 6),
            (Employee.position == "CEO", 5),
            (Employee.position == "Manager", 4),
            (Employee.position == "Team Lead", 3),
            (Employee.position == "Senior Developer", 2),
            (Employee.position == "Developer", 1),
            else_=0
        )
        
        if order == 'desc':
            query = query.order_by(position_order.desc())
        else:
            query = query.order_by(position_order.asc())
    elif sort_by == 'salary':
        if order == 'desc':
            query = query.order_by(Employee.salary.desc())
        else:
            query = query.order_by(Employee.salary.asc())
    else:
        if order == 'desc':
            query = query.order_by(Employee.id.desc())
        else:
            query = query.order_by(Employee.id.asc())
    
    employees = query.paginate(page=page, per_page=per_page, error_out=False)
    
    current_positions = [emp.position for emp in employees.items]
    required_levels = set()
    for pos in current_positions:
        level = POSITION_LEVELS.get(pos, 0)
        for position, pos_level in POSITION_LEVELS.items():
            if pos_level > level:
                required_levels.add(position)

    all_managers = db.session.query(Employee.id, Employee.full_name, Employee.position).filter(
        Employee.position.in_(required_levels)
    ).all()
    
    manager_dict = {emp.id: emp for emp in all_managers}
    
    return render_template('index.html', employees=employees, search=search, all_managers=all_managers, manager_dict=manager_dict)

@app.route('/update_manager/<int:emp_id>', methods=['POST'])
def update_manager(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    
    manager_id = request.form.get('manager_id')
    
    if manager_id:
        manager = Employee.query.get(int(manager_id))
        if not manager:
            flash('Начальник не найден!', 'error')
            return redirect(url_for('index'))
        
        if manager.id == employee.id:
            flash('Сотрудник не может быть начальником сам себе!', 'error')
            return redirect(url_for('index'))
        
        emp_level = POSITION_LEVELS.get(employee.position, 0)
        manager_level = POSITION_LEVELS.get(manager.position, 0)
        
        if manager_level <= emp_level:
            flash('Менеджер должен быть выше по должности!', 'error')
            return redirect(url_for('index'))
        
        employee.manager_id = manager.id
    else:
        employee.manager_id = None
    
    try:
        db.session.commit()
        flash('Начальник обновлён!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Проверка иерархии
@app.route('/check_hierarchy')
def check_hierarchy():
    employees = Employee.query.all()
    errors = []
    
    for emp in employees:
        if emp.manager_id:
            manager = Employee.query.get(emp.manager_id)
            if manager:
                emp_level = POSITION_LEVELS.get(emp.position, 0)
                manager_level = POSITION_LEVELS.get(manager.position, 0)
                
                if manager_level <= emp_level:
                    errors.append({
                        'employee': emp.full_name,
                        'position': emp.position,
                        'manager': manager.full_name,
                        'manager_position': manager.position
                    })
    
    return render_template('hierarchy_errors.html', errors=errors)

# Отчёт о росте количества сотрудников
@app.route('/growth_report')
def growth_report():
    from sqlalchemy import extract
    
    # Данные по годам и должностям
    results = db.session.query(
        extract('year', Employee.hire_date).label('year'),
        Employee.position,
        db.func.count(Employee.id).label('count')
    ).group_by(
        extract('year', Employee.hire_date),
        Employee.position
    ).all()
    
    data = {}
    years = set()
    
    for row in results:
        year = int(row.year)
        position = row.position
        count = row.count
        
        years.add(year)
        
        if position not in data:
            data[position] = {}
        
        data[position][year] = count
    
    years = sorted(years)
    
    positions = sorted(data.keys(), key=lambda x: POSITION_LEVELS.get(x, 0), reverse=True)
    growth_data = []
    
    for position in positions:
        row = {'position': position}
        
        total = 0
        for year in years:
            if year in data[position]:
                count = data[position][year]
                row[str(year)] = count
                total += count
            else:
                row[str(year)] = 0  # Нет добавлений в этом году
        
        row['total'] = total
        growth_data.append(row)
    
    return render_template('growth_report.html', growth_data=growth_data, years=years)

#Отчёт о фонде оплаты труда
@app.route('/salary_fund_report')
def salary_fund_report():
    from sqlalchemy import func
    
    # Сумма зарплат по должностям
    results = db.session.query(
        Employee.position,
        func.sum(Employee.salary).label('total_salary')
    ).group_by(Employee.position).all()
    
    # Общая сумма зарплат
    total_fund = db.session.query(func.sum(Employee.salary)).scalar()
    
    salary_data = []
    
    for row in results:
        position = row.position
        total_salary = row.total_salary
        
        # Процент от общего фонда
        percentage = (total_salary / total_fund) * 100 if total_fund > 0 else 0
        
        salary_data.append({
            'position': position,
            'total_salary': total_salary,
            'percentage': round(percentage, 2)
        })
    
    salary_data.sort(key=lambda x: POSITION_LEVELS.get(x['position'], 0), reverse=True)
    
    return render_template('salary_fund_report.html', salary_data=salary_data)

# Выгрузка базы данных
@app.route('/export_db')
def export_db():
    employees = Employee.query.all()
    data = []
    
    for emp in employees:
        data.append({
            'id': emp.id,
            'full_name': emp.full_name,
            'position': emp.position,
            'hire_date': str(emp.hire_date),
            'salary': emp.salary,
            'manager_id': emp.manager_id
        })
    
    return json.dumps(data, ensure_ascii=False, indent=2), 200, {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename=employees.json'
    }

# Выгрузка иерархии
@app.route('/export_hierarchy')
def export_hierarchy():
    hierarchy = build_hierarchy()
    return json.dumps(hierarchy, ensure_ascii=False, indent=2), 200, {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename=hierarchy.json'
    }

def build_hierarchy():
    employees = Employee.query.all()
    emp_dict = {emp.id: emp for emp in employees}
    
    hierarchy = []
    
    for emp in employees:
        if emp.manager_id is None:
            hierarchy.append(build_node(emp, emp_dict))
    
    return hierarchy

def build_node(emp, emp_dict):
    node = {
        'id': emp.id,
        'full_name': emp.full_name,
        'position': emp.position,
        'subordinates': []
    }
    
    for sub in emp_dict.values():
        if sub.manager_id == emp.id:
            node['subordinates'].append(build_node(sub, emp_dict))
    
    return node

if __name__ == '__main__':
    app.run(debug=True)