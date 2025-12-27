import sqlite3
import random
from mimesis import Person, Datetime
from mimesis.enums import Gender

conn = sqlite3.connect('employees.db')
cur = conn.cursor()

cur.execute("""
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    position TEXT NOT NULL,
    hire_date DATE NOT NULL,
    salary REAL NOT NULL,
    manager_id INTEGER
);
""")

person = Person('ru')
dt = Datetime()

POSITIONS = [
    "Big Boss",
    "Boss",
    "CEO",
    "Manager",
    "Team Lead",
    "Senior Developer",
    "Developer"
]

POSITION_LEVELS = {
    "Big Boss": 7,
    "Boss": 6,
    "CEO": 5,
    "Manager": 4,
    "Team Lead": 3,
    "Senior Developer": 2,
    "Developer": 1
}

employees = []
big_boss_id = None

# 1. Big Boss
full_name = person.full_name(gender=Gender.MALE)
position = "Big Boss"
hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
salary = round(random.uniform(300000, 500000), 2)
manager_id = None

cur.execute("""
INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
VALUES (?, ?, ?, ?, ?)
""", (full_name, position, hire_date, salary, manager_id))

big_boss_id = cur.lastrowid
employees.append((big_boss_id, position))

print(f"Создан Big Boss: {full_name}")

# 2. Boss (5 человек, подчиняются Big Boss)
boss_ids = []
for i in range(5):
    full_name = person.full_name(gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE)
    position = "Boss"
    hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
    salary = round(random.uniform(200000, 300000), 2)
    manager_id = big_boss_id

    cur.execute("""
    INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, position, hire_date, salary, manager_id))

    boss_id = cur.lastrowid
    boss_ids.append(boss_id)
    employees.append((boss_id, position))

print(f"Создано {len(boss_ids)} Boss")

# 3. CEO (10 человек, подчиняются Boss)
ceo_ids = []
for i in range(10):
    full_name = person.full_name(gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE)
    position = "CEO"
    hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
    salary = round(random.uniform(150000, 250000), 2)
    # Случайный Boss
    manager_id = random.choice(boss_ids)

    cur.execute("""
    INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, position, hire_date, salary, manager_id))

    ceo_id = cur.lastrowid
    ceo_ids.append(ceo_id)
    employees.append((ceo_id, position))

print(f"Создано {len(ceo_ids)} CEO")

# 4. Manager (50 человек, подчиняются CEO)
manager_ids = []
for i in range(50):
    full_name = person.full_name(gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE)
    position = "Manager"
    hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
    salary = round(random.uniform(100000, 180000), 2)
    # Случайный CEO
    manager_id = random.choice(ceo_ids)

    cur.execute("""
    INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, position, hire_date, salary, manager_id))

    manager_id_new = cur.lastrowid
    manager_ids.append(manager_id_new)
    employees.append((manager_id_new, position))

print(f"Создано {len(manager_ids)} Manager")

# 5. Team Lead (100 человек, подчиняются Manager)
team_lead_ids = []
for i in range(100):
    full_name = person.full_name(gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE)
    position = "Team Lead"
    hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
    salary = round(random.uniform(80000, 120000), 2)
    # Случайный Manager
    manager_id = random.choice(manager_ids)

    cur.execute("""
    INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, position, hire_date, salary, manager_id))

    team_lead_id = cur.lastrowid
    team_lead_ids.append(team_lead_id)
    employees.append((team_lead_id, position))

print(f"Создано {len(team_lead_ids)} Team Lead")

# 6. Senior Developer (200 человек, подчиняются Team Lead)
senior_dev_ids = []
for i in range(200):
    full_name = person.full_name(gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE)
    position = "Senior Developer"
    hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
    salary = round(random.uniform(70000, 100000), 2)
    # Случайный Team Lead
    manager_id = random.choice(team_lead_ids)

    cur.execute("""
    INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, position, hire_date, salary, manager_id))

    senior_dev_id = cur.lastrowid
    senior_dev_ids.append(senior_dev_id)
    employees.append((senior_dev_id, position))

print(f"Создано {len(senior_dev_ids)} Senior Developer")

# 7. Developer (остальные, подчиняются Senior Developer)
for i in range(50000 - 1 - 5 - 10 - 50 - 100 - 200):
    full_name = person.full_name(gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE)
    position = "Developer"
    hire_date = dt.date(start=2018, end=2024).strftime('%Y-%m-%d')
    salary = round(random.uniform(50000, 80000), 2)
    # Случайный Senior Developer
    manager_id = random.choice(senior_dev_ids)

    cur.execute("""
    INSERT INTO employees (full_name, position, hire_date, salary, manager_id)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, position, hire_date, salary, manager_id))

print("Создано Developer")

conn.commit()
print("База данных создана с правильной иерархией!")
print(f"Всего сотрудников: {cur.execute('SELECT COUNT(*) FROM employees').fetchone()[0]}")

conn.close()