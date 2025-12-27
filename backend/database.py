import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('service_system.db')
    cursor = conn.cursor()

    # Таблиця користувачів (техніки)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('technician')) DEFAULT 'technician',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблиця клієнтів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            address TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблиця пристроїв
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            serial_number TEXT,
            model TEXT NOT NULL,
            device_type TEXT,
            purchase_date DATE,
            FOREIGN KEY (client_id) REFERENCES Clients(id) ON DELETE CASCADE
        )
    ''')

    # Таблиця заявок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            device_id INTEGER NOT NULL,
            assigned_technician_id INTEGER,
            description TEXT NOT NULL,
            status TEXT CHECK(status IN ('new', 'in_progress', 'completed', 'cancelled')) DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            photo_path TEXT,
            client_signature_path TEXT,
            priority TEXT CHECK(priority IN ('low', 'normal', 'high', 'urgent')) DEFAULT 'normal',
            FOREIGN KEY (client_id) REFERENCES Clients(id) ON DELETE CASCADE,
            FOREIGN KEY (device_id) REFERENCES Devices(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_technician_id) REFERENCES Users(id)
        )
    ''')

    # Демо-дані
    create_demo_data(conn, cursor)
    
    conn.commit()
    conn.close()
    print("✅ База даних ініціалізована успішно!")

def create_demo_data(conn, cursor):
    """Створення демо-даних"""
    # Техніки
    technicians = [
        ('andrii@eurocode.ua', 'Андрій Технік'),
        ('sergii@eurocode.ua', 'Сергій Майстер'),
        ('maksym@eurocode.ua', 'Максим Спеціаліст'),
        ('ivan@eurocode.ua', 'Іван Технік'),
        ('petro@eurocode.ua', 'Петро Ремонтник')
    ]
    
    for email, name in technicians:
        cursor.execute("INSERT OR IGNORE INTO Users (email, full_name, role) VALUES (?, ?, 'technician')", 
                      (email, name))
    
    # Клієнти
    clients = [
        ('ТОВ «Єврокод»', 'м. Київ, вул. Тестова, 1', '+380501234567', 'info@eurocode.com.ua'),
        ('Кафе «Львівська»', 'м. Львів, вул. Шевченка, 25', '+380672345678', 'cafe@lvivska.ua'),
        ('Аптека «Здоров\'я»', 'м. Київ, вул. Лікарська, 12', '+380631234567', 'apteka@zdorovya.ua'),
        ('Магазин «Електроніка»', 'м. Київ, вул. Технічна, 8', '+380501112233', 'shop@elektronika.ua')
    ]
    
    client_ids = []
    for client in clients:
        cursor.execute('''
            INSERT OR IGNORE INTO Clients (company_name, address, contact_phone, contact_email)
            VALUES (?, ?, ?, ?)
        ''', client)
        client_ids.append(cursor.lastrowid)
    
    conn.commit()  # Комітимо щоб отримати правильні ID
    
    # Пристрої
    devices = [
        (client_ids[0], 'KAS-2024-001', 'АТОЛ 90F', 'Касовий апарат'),
        (client_ids[0], 'FIS-2024-002', 'RICH 1800K', 'Фіскальний реєстратор'),
        (client_ids[1], 'KAS-2024-003', 'АТОЛ 55F', 'Касовий апарат'),
        (client_ids[2], 'FIS-2024-004', 'POS-80', 'Фіскальний реєстратор'),
        (client_ids[3], 'KAS-2024-005', 'MINI MARKET MM-300', 'Касовий апарат')
    ]
    
    device_ids = []
    for device in devices:
        cursor.execute('''
            INSERT OR IGNORE INTO Devices (client_id, serial_number, model, device_type)
            VALUES (?, ?, ?, ?)
        ''', device)
        device_ids.append(cursor.lastrowid)
    
    conn.commit()  # Комітимо щоб отримати правильні ID
    
    # Заявки
    requests = [
        (client_ids[1], device_ids[2], 1, 'Не друкує чек, помилка паперу', 'in_progress', 'high'),
        (client_ids[2], device_ids[3], 2, 'Чистка внутрішніх компонентів', 'in_progress', 'normal'),
        (client_ids[0], device_ids[0], None, 'Повірка касового апарата', 'new', 'normal'),
        (client_ids[3], device_ids[4], None, 'Налаштування підключення до 1С', 'new', 'high')
    ]
    
    for req in requests:
        cursor.execute('''
            INSERT OR IGNORE INTO Requests 
            (client_id, device_id, assigned_technician_id, description, status, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', req)

if __name__ == "__main__":
    init_db()