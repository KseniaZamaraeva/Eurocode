// ==================== КОНФІГУРАЦІЯ ====================
const API_URL = 'http://localhost:5000/api';
let currentTechnician = null;

// ==================== УТИЛІТИ ====================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${getNotificationIcon(type)}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none; border:none; color:white; margin-left:auto; cursor:pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// ==================== АВТОРИЗАЦІЯ ====================
if (window.location.pathname.endsWith('login.html')) {
    document.addEventListener('DOMContentLoaded', function() {
        // Автозаповнення останнього email
        const lastTech = JSON.parse(localStorage.getItem('technician'));
        if (lastTech) {
            document.getElementById('email').value = lastTech.email;
        }
    });
}

// ==================== ПАНЕЛЬ ТЕХНІКА ====================
if (window.location.pathname.endsWith('technician-dashboard.html')) {
    document.addEventListener('DOMContentLoaded', async function() {
        // Перевірка авторизації
        const technician = JSON.parse(localStorage.getItem('technician'));
        if (!technician) {
            window.location.href = 'login.html';
            return;
        }
        
        currentTechnician = technician;
        
        // Оновлюємо інформацію про техніка
        updateTechnicianInfo(technician);
        
        // Завантажуємо завдання
        await loadTechnicianTasks();
        
        // Налаштовуємо кнопку виходу
        document.getElementById('logoutBtn')?.addEventListener('click', function() {
            if (confirm('Вийти з системи?')) {
                localStorage.removeItem('technician');
                window.location.href = 'login.html';
            }
        });
        
        // Налаштовуємо таби
        setupTabs();
        
        // Автооновлення кожні 30 секунд
        setInterval(loadTechnicianTasks, 30000);
    });
}

// ==================== СТВОРЕННЯ ЗАЯВКИ ====================
if (window.location.pathname.endsWith('create-request.html')) {
    document.addEventListener('DOMContentLoaded', function() {
        // Перевірка авторизації
        const technician = JSON.parse(localStorage.getItem('technician'));
        if (!technician) {
            window.location.href = 'login.html';
            return;
        }
        
        currentTechnician = technician;
        
        // Заповнюємо поле техніка
        document.getElementById('technicianName').textContent = technician.name;
        document.getElementById('technicianEmail').textContent = technician.email;
        
        // Налаштовуємо форму
        const form = document.getElementById('requestForm');
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            await submitNewRequest(technician.id);
        });
    });
}

// ==================== ДОСТУПНІ ЗАВДАННЯ ====================
if (window.location.pathname.endsWith('available-tasks.html')) {
    document.addEventListener('DOMContentLoaded', async function() {
        // Перевірка авторизації
        const technician = JSON.parse(localStorage.getItem('technician'));
        if (!technician) {
            window.location.href = 'login.html';
            return;
        }
        
        currentTechnician = technician;
        
        // Завантажуємо доступні завдання
        await loadAvailableTasks();
        
        // Налаштовуємо кнопку оновлення
        document.getElementById('refreshBtn')?.addEventListener('click', loadAvailableTasks);
    });
}

// ==================== ОСНОВНІ ФУНКЦІЇ ====================

// Оновлення інформації про техніка
function updateTechnicianInfo(technician) {
    const techNameElement = document.getElementById('techName');
    const techEmailElement = document.getElementById('techEmail');
    const techAvatarElement = document.getElementById('techAvatar');
    
    if (techNameElement) techNameElement.textContent = technician.name;
    if (techEmailElement) techEmailElement.textContent = technician.email;
    if (techAvatarElement) techAvatarElement.textContent = technician.name.charAt(0);
    
    // Оновлюємо заголовок сторінки
    document.title = `${technician.name} | Єврокод`;
}

// Завантаження завдань техніка
async function loadTechnicianTasks() {
    if (!currentTechnician) return;
    
    try {
        const response = await fetch(`${API_URL}/technician/${currentTechnician.id}/tasks`);
        if (!response.ok) throw new Error('API не відповідає');
        
        const data = await response.json();
        
        // Оновлюємо статистику
        updateStats(data.stats);
        
        // Показуємо активні завдання
        displayActiveTasks(data.active_tasks);
        
        // Показуємо історію
        displayHistory(data.history_tasks);
        
        // Показуємо доступні завдання (якщо є відповідний контейнер)
        if (document.getElementById('availableTasksContainer')) {
            displayAvailableTasks(data.available_tasks);
        }
        
    } catch (error) {
        console.error('Помилка завантаження завдань:', error);
        showNotification('Помилка завантаження даних', 'error');
        loadDemoData();
    }
}

// Оновлення статистики
function updateStats(stats) {
    const activeCount = document.getElementById('activeCount');
    const progressCount = document.getElementById('progressCount');
    const completedCount = document.getElementById('completedCount');
    const availableCount = document.getElementById('availableCount');
    
    if (activeCount) activeCount.textContent = stats.active || 0;
    if (progressCount) progressCount.textContent = stats.in_progress || 0;
    if (completedCount) completedCount.textContent = stats.completed || 0;
    if (availableCount) availableCount.textContent = stats.available || 0;
}

// Відображення активних завдань
function displayActiveTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle fa-2x" style="color: #2ecc71;"></i>
                <h3>Немає активних завдань</h3>
                <p>У вас поки що немає завдань для виконання</p>
                <a href="available-tasks.html" class="btn btn-primary" style="margin-top: 1rem;">
                    <i class="fas fa-plus"></i> Знайти завдання
                </a>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    tasks.forEach(task => {
        const statusClass = `status-${task.status}`;
        const statusText = getStatusText(task.status);
        const priorityClass = `priority-${task.priority || 'normal'}`;
        
        html += `
        <div class="task-card ${task.priority === 'high' ? 'urgent' : ''}" data-task-id="${task.id}">
            <div class="task-header">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0;">
                        <span class="${priorityClass}">${task.priority === 'high' ? '🔥 ' : ''}</span>
                        Завдання #${task.id}
                    </h3>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">
                        <i class="fas fa-building"></i> ${task.company_name || 'Клієнт'}
                    </p>
                </div>
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
            
            <p><strong><i class="fas fa-laptop"></i> Пристрій:</strong> ${task.model || 'Не вказано'} 
               ${task.serial_number ? `(${task.serial_number})` : ''}</p>
            <p><strong><i class="fas fa-map-marker-alt"></i> Адреса:</strong> ${task.address || 'Не вказано'}</p>
            <p><strong><i class="fas fa-phone"></i> Телефон:</strong> ${task.contact_phone || 'Не вказано'}</p>
            <p><strong><i class="fas fa-file-alt"></i> Опис:</strong> ${task.description || 'Без опису'}</p>
            
            <div class="task-actions">
                ${task.status === 'in_progress' ? `
                <button class="btn btn-success" onclick="completeTask(${task.id})">
                    <i class="fas fa-check"></i> Завершити
                </button>
                ` : ''}
                
                <button class="btn btn-outline" onclick="viewTaskDetails(${task.id})">
                    <i class="fas fa-info-circle"></i> Деталі
                </button>
                
                ${task.contact_phone && task.contact_phone !== 'Не вказано' ? `
                <button class="btn btn-outline" onclick="callClient('${task.contact_phone}')">
                    <i class="fas fa-phone"></i> Зателефонувати
                </button>
                ` : ''}
                
                <button class="btn btn-outline" onclick="addPhotoToTask(${task.id})">
                    <i class="fas fa-camera"></i> Додати фото
                </button>
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

// Відображення історії
function displayHistory(tasks) {
    const container = document.getElementById('historyContainer');
    if (!container) return;
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history fa-2x" style="color: #95a5a6;"></i>
                <h3>Історія порожня</h3>
                <p>У вас ще немає завершених завдань</p>
            </div>
        `;
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 0.5rem;">';
    
    tasks.forEach(task => {
        const date = task.completed_at ? 
            new Date(task.completed_at).toLocaleDateString('uk-UA') : 
            'Не вказано';
        
        html += `
        <div class="history-item">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <strong>#${task.id} - ${task.company_name}</strong>
                    <div style="font-size: 0.9rem; color: #666;">
                        <i class="fas fa-laptop"></i> ${task.model} • 
                        <i class="fas fa-calendar"></i> ${date}
                    </div>
                </div>
                <span class="status-badge status-completed">Завершено</span>
            </div>
            ${task.description ? `<p style="margin-top: 0.5rem;">${task.description}</p>` : ''}
            ${task.photo_path ? `
            <div style="margin-top: 0.5rem;">
                <small><i class="fas fa-camera" style="color: #3498db;"></i> Є фото-звіт</small>
            </div>
            ` : ''}
        </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Відображення доступних завдань
function displayAvailableTasks(tasks) {
    const container = document.getElementById('availableTasksContainer');
    if (!container) return;
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle fa-2x" style="color: #2ecc71;"></i>
                <h3>Немає доступних завдань</h3>
                <p>Всі завдання вже розподілені між техніками</p>
                <button class="btn btn-primary" style="margin-top: 1rem;" onclick="loadAvailableTasks()">
                    <i class="fas fa-sync-alt"></i> Оновити
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    tasks.forEach(task => {
        html += `
        <div class="task-card" data-task-id="${task.id}">
            <div class="task-header">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0;">Завдання #${task.id}</h3>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">
                        <i class="fas fa-building"></i> ${task.company_name || 'Клієнт'}
                    </p>
                </div>
                <span class="status-badge status-new">Доступне</span>
            </div>
            
            <p><strong><i class="fas fa-laptop"></i> Пристрій:</strong> ${task.model || 'Не вказано'}</p>
            <p><strong><i class="fas fa-map-marker-alt"></i> Адреса:</strong> ${task.address || 'Не вказано'}</p>
            <p><strong><i class="fas fa-phone"></i> Телефон:</strong> ${task.contact_phone || 'Не вказано'}</p>
            <p><strong><i class="fas fa-file-alt"></i> Опис:</strong> ${task.description || 'Без опису'}</p>
            
            <div class="task-actions">
                <button class="btn btn-primary" onclick="takeAvailableTask(${task.id})">
                    <i class="fas fa-hand-paper"></i> Прийняти завдання
                </button>
                <button class="btn btn-outline" onclick="viewTaskDetails(${task.id})">
                    <i class="fas fa-info-circle"></i> Деталі
                </button>
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

// Завантаження доступних завдань
async function loadAvailableTasks() {
    if (!currentTechnician) return;
    
    try {
        const response = await fetch(`${API_URL}/tasks/available`);
        if (!response.ok) throw new Error('API не відповідає');
        
        const tasks = await response.json();
        displayAvailableTasks(tasks);
        
    } catch (error) {
        console.error('Помилка завантаження доступних завдань:', error);
        showNotification('Помилка завантаження завдань', 'error');
    }
}

// ==================== ДІЇ З ЗАВДАННЯМИ ====================

// Прийняття доступного завдання
async function takeAvailableTask(taskId) {
    if (!currentTechnician) {
        showNotification('Спочатку увійдіть в систему', 'error');
        return;
    }
    
    if (!confirm('Прийняти це завдання на себе?')) return;
    
    try {
        const response = await fetch(`${API_URL}/task/${taskId}/take`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ technician_id: currentTechnician.id })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || 'Завдання прийнято!', 'success');
            
            // Оновлюємо список завдань
            setTimeout(() => {
                if (window.location.pathname.endsWith('available-tasks.html')) {
                    loadAvailableTasks();
                } else {
                    loadTechnicianTasks();
                }
            }, 1000);
            
        } else {
            const error = await response.json();
            showNotification(error.error || 'Помилка прийняття завдання', 'error');
        }
        
    } catch (error) {
        console.error('Помилка:', error);
        showNotification('Демо-режим: Завдання прийнято', 'success');
        
        // Демо-оновлення
        setTimeout(() => {
            if (window.location.pathname.endsWith('available-tasks.html')) {
                loadAvailableTasks();
            }
        }, 1000);
    }
}

// Завершення завдання
async function completeTask(taskId) {
    if (!confirm('Завершити це завдання?')) return;
    
    try {
        const response = await fetch(`${API_URL}/task/${taskId}/status`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ status: 'completed' })
        });
        
        if (response.ok) {
            showNotification('Завдання завершено!', 'success');
            setTimeout(() => loadTechnicianTasks(), 1000);
        } else {
            showNotification('Помилка завершення завдання', 'error');
        }
        
    } catch (error) {
        console.error('Помилка:', error);
        showNotification('Демо-режим: Завдання завершено', 'success');
        setTimeout(() => loadTechnicianTasks(), 1000);
    }
}

// Створення нової заявки
async function submitNewRequest(technicianId) {
    const formData = {
        client_name: document.getElementById('clientName').value.trim(),
        client_phone: document.getElementById('clientPhone').value.trim(),
        device_model: document.getElementById('deviceModel').value.trim(),
        serial_number: document.getElementById('serialNumber').value.trim(),
        device_type: document.getElementById('deviceType').value.trim(),
        description: document.getElementById('description').value.trim(),
        technician_id: technicianId
    };
    
    // Перевірка обов'язкових полів
    if (!formData.client_name || !formData.device_model || !formData.description) {
        showNotification('Заповніть обов\'язкові поля: клієнт, пристрій, опис', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/requests/technician`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || 'Заявку створено та прийнято!', 'success');
            
            setTimeout(() => {
                window.location.href = 'technician-dashboard.html';
            }, 2000);
            
        } else {
            const error = await response.json();
            showNotification(error.error || 'Помилка створення заявки', 'error');
        }
        
    } catch (error) {
        console.error('Помилка:', error);
        showNotification('Демо-режим: Заявку створено', 'success');
        
        setTimeout(() => {
            window.location.href = 'technician-dashboard.html';
        }, 1000);
    }
}

// ==================== ДОПОМІЖНІ ФУНКЦІЇ ====================

function getStatusText(status) {
    const statusMap = {
        'new': 'Нове',
        'in_progress': 'В роботі',
        'completed': 'Завершено',
        'cancelled': 'Скасовано'
    };
    return statusMap[status] || status;
}

function viewTaskDetails(taskId) {
    alert(`Деталі завдання #${taskId}\n\nФункція детального перегляду в розробці`);
}

function callClient(phone) {
    if (phone && phone !== 'Не вказано') {
        if (confirm(`Зателефонувати клієнту?\n${phone}`)) {
            // В реальній системі: window.open(`tel:${phone}`);
            showNotification(`Імітація дзвінка на ${phone}`, 'info');
        }
    } else {
        showNotification('Номер телефону не вказаний', 'warning');
    }
}

function addPhotoToTask(taskId) {
    alert(`Додати фото до завдання #${taskId}\n\nФункція завантаження фото в розробці`);
}

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('onclick').match(/'([^']+)'/)[1];
            
            // Оновлюємо активні кнопки
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Показуємо відповідний контент
            tabContents.forEach(content => {
                if (content.id === tabName + 'Tab') {
                    content.style.display = 'block';
                } else {
                    content.style.display = 'none';
                }
            });
        });
    });
}

// ==================== ДЕМО-РЕЖИМ ====================

function loadDemoData() {
    // Демо-статистика
    document.getElementById('activeCount').textContent = '2';
    document.getElementById('progressCount').textContent = '1';
    document.getElementById('completedCount').textContent = '5';
    document.getElementById('availableCount').textContent = '3';
    
    // Демо-завдання
    const demoTasks = [
        {
            id: 1023,
            company_name: 'Кафе «Львівська»',
            address: 'м. Львів, вул. Шевченка, 25',
            contact_phone: '+380672345678',
            model: 'RICH 1800K',
            serial_number: 'FIS-2024-001',
            description: 'Заміна термопаперу, профілактика обладнання',
            status: 'in_progress',
            priority: 'normal'
        }
    ];
    
    displayActiveTasks(demoTasks);
}

// ==================== ГЛОБАЛЬНІ ФУНКЦІЇ ====================

window.takeAvailableTask = takeAvailableTask;
window.completeTask = completeTask;
window.viewTaskDetails = viewTaskDetails;
window.callClient = callClient;
window.addPhotoToTask = addPhotoToTask;