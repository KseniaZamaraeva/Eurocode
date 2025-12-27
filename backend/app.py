from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def db_connection():
    conn = sqlite3.connect('service_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# СИСТЕМНИЙ ПАРОЛЬ для входу
SYSTEM_PASSWORD = "eurocode2024"

# ==================== АВТОРИЗАЦІЯ ТЕХНІКІВ З ПАРОЛЕМ ====================
@app.route('/api/login', methods=['POST'])
def login():
    """Авторизація техніків з паролем системи"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Введіть email'}), 400
    
    if not password:
        return jsonify({'success': False, 'message': 'Введіть пароль системи'}), 400
    
    # Перевірка пароля системи
    if password != SYSTEM_PASSWORD:
        return jsonify({'success': False, 'message': 'Невірний пароль системи'}), 401
    
    # Визначаємо техніка за email
    technicians = {
        'andrii@eurocode.ua': {'name': 'Андрій Технік', 'id': 1},
        'sergii@eurocode.ua': {'name': 'Сергій Майстер', 'id': 2},
        'maksym@eurocode.ua': {'name': 'Максим Спеціаліст', 'id': 3},
        'ivan@eurocode.ua': {'name': 'Іван Технік', 'id': 4},
        'petro@eurocode.ua': {'name': 'Петро Ремонтник', 'id': 5}
    }
    
    # Якщо це відомий технік - використовуємо його дані
    if email in technicians:
        tech_data = technicians[email]
    else:
        # Для будь-якого іншого email - створюємо нового техніка
        tech_name = email.split('@')[0].capitalize() + ' Технік'
        tech_id = hash(email) % 1000
        
        # Зберігаємо в базі
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO Users (email, full_name, role)
            VALUES (?, ?, 'technician')
        ''', (email, tech_name))
        conn.commit()
        conn.close()
        
        tech_data = {'name': tech_name, 'id': tech_id}
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'name': tech_data['name'],
            'id': tech_data.get('id', 0),
            'role': 'technician'
        }
    }), 200

# ==================== ОТРИМАННЯ ЗАВДАНЬ ТЕХНІКА ====================
@app.route('/api/technician/<int:tech_id>/tasks', methods=['GET'])
def get_technician_tasks(tech_id):
    """Отримати завдання конкретного техніка"""
    conn = db_connection()
    
    # Отримуємо активні завдання
    cursor = conn.execute('''
        SELECT r.*, c.company_name, c.address, c.contact_phone, 
               d.serial_number, d.model, d.device_type
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        WHERE r.assigned_technician_id = ? AND r.status != 'completed'
        ORDER BY 
            CASE WHEN r.status = 'new' THEN 1
                 WHEN r.status = 'in_progress' THEN 2
                 ELSE 3 END,
            r.created_at DESC
    ''', (tech_id,))
    
    active_tasks = [dict(row) for row in cursor.fetchall()]
    
    # Отримуємо історію завдань (завершені)
    cursor = conn.execute('''
        SELECT r.*, c.company_name, c.address, d.model,
               r.completed_at, r.photo_path, r.client_signature_path
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        WHERE r.assigned_technician_id = ? AND r.status = 'completed'
        ORDER BY r.completed_at DESC
        LIMIT 20
    ''', (tech_id,))
    
    history_tasks = [dict(row) for row in cursor.fetchall()]
    
    # Отримуємо ВСІ доступні завдання (для прийняття)
    cursor = conn.execute('''
        SELECT r.*, c.company_name, c.address, c.contact_phone,
               d.serial_number, d.model, d.device_type
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        WHERE r.assigned_technician_id IS NULL AND r.status = 'new'
        ORDER BY r.created_at DESC
    ''')
    
    available_tasks = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'active_tasks': active_tasks,
        'history_tasks': history_tasks,
        'available_tasks': available_tasks,
        'stats': {
            'active': len(active_tasks),
            'completed': len(history_tasks),
            'available': len(available_tasks)
        }
    })

# ==================== ПРИЙНЯТТЯ ЗАВДАННЯ ТЕХНІКОМ ====================
@app.route('/api/task/<int:task_id>/take', methods=['POST'])
def take_task(task_id):
    """Технік приймає завдання на себе"""
    data = request.get_json()
    technician_id = data.get('technician_id')
    
    if not technician_id:
        return jsonify({'error': 'Не вказано ID техніка'}), 400
    
    conn = db_connection()
    cursor = conn.cursor()
    
    # Перевіряємо, чи завдання ще доступне
    cursor.execute('SELECT assigned_technician_id FROM Requests WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    
    if task and task['assigned_technician_id']:
        conn.close()
        return jsonify({'error': 'Завдання вже призначено іншому техніку'}), 400
    
    # Призначаємо техніка
    cursor.execute('''
        UPDATE Requests 
        SET assigned_technician_id = ?, status = 'in_progress', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (technician_id, task_id))
    
    conn.commit()
    
    # Отримуємо оновлене завдання
    cursor.execute('''
        SELECT r.*, c.company_name, d.model
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        WHERE r.id = ?
    ''', (task_id,))
    
    updated_task = cursor.fetchone()
    conn.close()
    
    if updated_task:
        return jsonify({
            'success': True,
            'task': dict(updated_task),
            'message': 'Завдання прийнято'
        })
    
    return jsonify({'error': 'Завдання не знайдено'}), 404

# ==================== ОНОВЛЕННЯ СТАТУСУ ЗАВДАННЯ ====================
@app.route('/api/task/<int:task_id>/status', methods=['POST'])
def update_task_status(task_id):
    """Технік оновлює статус свого завдання"""
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['in_progress', 'completed', 'cancelled']:
        return jsonify({'error': 'Невірний статус'}), 400
    
    conn = db_connection()
    cursor = conn.cursor()
    
    if new_status == 'completed':
        cursor.execute('''
            UPDATE Requests 
            SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, task_id))
    else:
        cursor.execute('''
            UPDATE Requests 
            SET status = ?
            WHERE id = ?
        ''', (new_status, task_id))
    
    conn.commit()
    
    # Отримуємо оновлене завдання
    cursor.execute('''
        SELECT r.*, c.company_name, d.model
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        WHERE r.id = ?
    ''', (task_id,))
    
    task = cursor.fetchone()
    conn.close()
    
    if task:
        return jsonify({
            'success': True,
            'task': dict(task),
            'message': 'Статус оновлено'
        })
    
    return jsonify({'error': 'Завдання не знайдено'}), 404

# ==================== СТВОРЕННЯ НОВОЇ ЗАЯВКИ ТЕХНІКОМ ====================
@app.route('/api/requests/technician', methods=['POST'])
def create_request_by_technician():
    """Технік створює нову заявку"""
    data = request.get_json()
    
    # Обов'язкові поля
    required = ['client_name', 'device_model', 'description', 'technician_id']
    if not all(k in data for k in required):
        return jsonify({'error': 'Відсутні обовʼязкові поля'}), 400
    
    conn = db_connection()
    cursor = conn.cursor()
    
    # Створюємо тимчасового клієнта
    cursor.execute('''
        INSERT INTO Clients (company_name, contact_phone)
        VALUES (?, ?)
    ''', (data['client_name'], data.get('client_phone', '')))
    
    client_id = cursor.lastrowid
    
    # Створюємо тимчасовий пристрій
    cursor.execute('''
        INSERT INTO Devices (client_id, model, serial_number, device_type)
        VALUES (?, ?, ?, ?)
    ''', (client_id, data['device_model'], 
          data.get('serial_number', ''), 
          data.get('device_type', 'Касовий апарат')))
    
    device_id = cursor.lastrowid
    
    # Створюємо заявку
    cursor.execute('''
        INSERT INTO Requests (client_id, device_id, description, 
                             assigned_technician_id, status)
        VALUES (?, ?, ?, ?, 'in_progress')
    ''', (client_id, device_id, data['description'], data['technician_id']))
    
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'id': request_id,
        'message': 'Заявку створено та прийнято на виконання'
    }), 201

# ==================== ДОСТУПНІ ЗАВДАННЯ ====================
@app.route('/api/tasks/available', methods=['GET'])
def get_available_tasks():
    """Отримати всі доступні завдання (без призначеного техніка)"""
    conn = db_connection()
    
    cursor = conn.execute('''
        SELECT r.*, c.company_name, c.address, c.contact_phone,
               d.serial_number, d.model, d.device_type
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        WHERE r.assigned_technician_id IS NULL AND r.status = 'new'
        ORDER BY r.created_at DESC
    ''')
    
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(tasks)

# ==================== ВСІ ТЕХНІКИ ====================
@app.route('/api/technicians', methods=['GET'])
def get_all_technicians():
    """Отримати список всіх техніків"""
    conn = db_connection()
    
    cursor = conn.execute('''
        SELECT id, email, full_name 
        FROM Users 
        WHERE role = 'technician'
        ORDER BY full_name
    ''')
    
    technicians = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(technicians)

# ==================== БАЗОВІ ДАНІ ====================
@app.route('/api/clients', methods=['GET'])
def get_clients():
    conn = db_connection()
    cursor = conn.execute("SELECT * FROM Clients ORDER BY company_name")
    clients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(clients)

@app.route('/api/devices', methods=['GET'])
def get_devices():
    conn = db_connection()
    cursor = conn.execute("SELECT * FROM Devices ORDER BY model")
    devices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices)

@app.route('/api/requests', methods=['GET'])
def get_requests():
    conn = db_connection()
    cursor = conn.execute('''
        SELECT r.*, c.company_name, d.serial_number, d.model,
               u.full_name as technician_name
        FROM Requests r
        LEFT JOIN Clients c ON r.client_id = c.id
        LEFT JOIN Devices d ON r.device_id = d.id
        LEFT JOIN Users u ON r.assigned_technician_id = u.id
        ORDER BY r.created_at DESC
    ''')
    requests = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(requests)

# ==================== СТАТИСТИКА ====================
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM Requests")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as new FROM Requests WHERE status = 'new'")
    new = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as in_progress FROM Requests WHERE status = 'in_progress'")
    in_progress = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as completed FROM Requests WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as technicians FROM Users WHERE role = 'technician'")
    technicians = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total': total,
        'new': new,
        'in_progress': in_progress,
        'completed': completed,
        'technicians': technicians
    })

# ==================== ТЕСТОВІ ДАНІ ====================
@app.route('/api/test-data', methods=['GET'])
def test_data():
    return jsonify({
        'message': 'API системи для техніків Єврокод',
        'system_password': 'eurocode2024',
        'endpoints': [
            '/api/login - POST (email, password)',
            '/api/technician/<id>/tasks - GET',
            '/api/tasks/available - GET',
            '/api/task/<id>/take - POST',
            '/api/requests/technician - POST'
        ]
    })

@app.route('/')
def index():
    return jsonify({
        'message': 'Сервісна система Єврокод - API для техніків',
        'version': '1.0',
        'instructions': 'Використовуйте /api/login для входу'
    })

if __name__ == '__main__':
    print("🚀 Сервісна система техніків Єврокод")
    print("🔑 Пароль системи: eurocode2024")
    print("🌐 API доступне на: http://localhost:5000")
    print("📱 Фронтенд: http://localhost:8000")
    app.run(debug=True, port=5000)