class ToDoApp {
    constructor() {
        this.currentPage = 'tasks';
        this.currentFilter = 'all';
        this.currentQuadrant = null;
        this.tasks = [];
        
        this.init();
    }
    
    async init() {
        if (!isAuthenticated()) {
            window.location.href = 'index.html';
            return;
        }
        
        this.initNavbar();
        this.initEventListeners();
        await this.loadPage(this.currentPage);
    }
    
    initNavbar() {
        const user = getUserInfo();
        if (user) {
            const greetingEl = document.getElementById('userGreeting');
            if (greetingEl) {
                greetingEl.textContent = `Привет, ${user.nickname}!`;
            }
            
            if (user.role === 'admin') {
                const adminMenuItem = document.getElementById('adminMenuItem');
                if (adminMenuItem) {
                    adminMenuItem.style.display = 'block';
                }
            }
        }
    }
    
    initEventListeners() {
        document.querySelectorAll('[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.target.closest('[data-page]').dataset.page;
                this.loadPage(page);
            });
        });
        
        document.querySelectorAll('[data-filter]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const filter = e.target.closest('[data-filter]').dataset.filter;
                this.setFilter(filter);
            });
        });
        
        document.querySelectorAll('[data-quadrant]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const quadrant = e.target.closest('[data-quadrant]').dataset.quadrant;
                this.setQuadrantFilter(quadrant);
            });
        });
        
        const createTaskBtn = document.getElementById('createTaskBtn');
        if (createTaskBtn) {
            createTaskBtn.addEventListener('click', () => {
                this.showTaskModal();
            });
        }
        
        const saveTaskBtn = document.getElementById('saveTaskBtn');
        if (saveTaskBtn) {
            saveTaskBtn.addEventListener('click', () => {
                this.saveTask();
            });
        }
        
        const savePasswordBtn = document.getElementById('savePasswordBtn');
        if (savePasswordBtn) {
            savePasswordBtn.addEventListener('click', () => {
                this.changePassword();
            });
        }
        
        // Обработчики для галочек задач
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('task-checkbox')) {
                const taskId = e.target.dataset.taskId;
                this.toggleTaskComplete(taskId);
            }
            
            // Обработчик для кнопки редактирования
            if (e.target.closest('.edit-task')) {
                const taskId = e.target.closest('.edit-task').dataset.taskId;
                const task = this.tasks.find(t => t.id == taskId);
                if (task) {
                    this.showTaskModal(task);
                }
            }
            
            // Обработчик для кнопки удаления
            if (e.target.closest('.delete-task')) {
                const taskId = e.target.closest('.delete-task').dataset.taskId;
                this.deleteTask(taskId);
            }
        });
    }
    
    async loadPage(page) {
        this.currentPage = page;
        
        document.querySelectorAll('[data-page]').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.page === page) {
                link.classList.add('active');
            }
        });
        
        switch (page) {
            case 'tasks':
                await this.loadTasksPage();
                break;
            case 'stats':
                await this.loadStatsPage();
                break;
            case 'admin':
                await this.loadAdminPage();
                break;
            default:
                await this.loadTasksPage();
        }
    }
    
    setFilter(filter) {
        this.currentFilter = filter;
        
        document.querySelectorAll('[data-filter]').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.filter === filter) {
                link.classList.add('active');
            }
        });
        
        this.loadTasksPage();
    }
    
    setQuadrantFilter(quadrant) {
        this.currentQuadrant = quadrant === this.currentQuadrant ? null : quadrant;
        
        document.querySelectorAll('[data-quadrant]').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.quadrant === this.currentQuadrant) {
                link.classList.add('active');
            }
        });
        
        this.loadTasksPage();
    }
    
    async loadTasksPage() {
        try {
            this.showLoading();
            
            const token = getToken();
            console.log('Токен для запроса задач:', token ? 'присутствует' : 'отсутствует');
            console.log('Полный токен (первые 20 символов):', token ? token.substring(0, 20) + '...' : 'null');
            
            const url = `${API_CONFIG.BASE_URL}/`;
            console.log('URL запроса:', url);
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                }
            });
            
            console.log('Статус ответа задач:', response.status);
            console.log('Response ok:', response.ok);
            console.log('Response headers:', [...response.headers.entries()]);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.log('Статус ответа:', response.status);
                console.log('Заголовки ответа:', [...response.headers.entries()]);
                console.log('Тело ошибки:', errorText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.tasks = await response.json();
            this.renderTasks();
        } catch (error) {
            this.showError('Ошибка загрузки задач');
            console.error('Ошибка загрузки задач:', error);
            console.error('Stack trace:', error.stack);
        }
    }
    
    renderTasks() {
        const mainContent = document.getElementById('mainContent');
        
        let filteredTasks = [...this.tasks];
        
        if (this.currentFilter === 'pending') {
            filteredTasks = filteredTasks.filter(task => !task.completed);
        } else if (this.currentFilter === 'completed') {
            filteredTasks = filteredTasks.filter(task => task.completed);
        }
        
        if (this.currentQuadrant) {
            filteredTasks = filteredTasks.filter(task => task.quadrant === this.currentQuadrant);
        }
        
        const tasksByQuadrant = {
            'Q1': [],
            'Q2': [],
            'Q3': [],
            'Q4': []
        };
        
        filteredTasks.forEach(task => {
            tasksByQuadrant[task.quadrant].push(task);
        });
        
        let html = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Мои задачи</h2>
                <div>
                    <span class="badge bg-secondary">Всего: ${filteredTasks.length}</span>
                </div>
            </div>
            
            <div class="row">
        `;
        
        // Добавляем квадранты
        ['Q1', 'Q2', 'Q3', 'Q4'].forEach(quadrant => {
            const quadrantNames = {
                'Q1': 'Важные и срочные',
                'Q2': 'Важные, не срочные',
                'Q3': 'Срочные, не важные',
                'Q4': 'Не важные, не срочные'
            };
            
            const quadrantColors = {
                'Q1': 'danger',
                'Q2': 'success',
                'Q3': 'warning',
                'Q4': 'secondary'
            };
            
            html += `
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="card quadrant-card ${quadrant.toLowerCase()}">
                        <div class="card-header bg-${quadrantColors[quadrant]} ${quadrant === 'Q3' ? 'text-dark' : 'text-white'}">
                            <h6 class="mb-0">
                                <span class="badge bg-white text-${quadrantColors[quadrant]} me-2">${quadrant}</span>
                                ${quadrantNames[quadrant]}
                                <span class="badge bg-light text-dark float-end">${tasksByQuadrant[quadrant].length}</span>
                            </h6>
                        </div>
                        <div class="card-body" id="quadrant-${quadrant.toLowerCase()}">
                            ${this.renderQuadrantTasks(tasksByQuadrant[quadrant])}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
        
        mainContent.innerHTML = html;
    }
    
    renderQuadrantTasks(tasks) {
        if (tasks.length === 0) {
            return '<div class="text-center text-muted py-3">Задач нет</div>';
        }
        
        let html = '';
        tasks.forEach(task => {
            const daysLeft = calculateDaysUntilDeadline(task.deadline_at);
            let deadlineBadge = '';
            
            if (daysLeft !== null) {
                if (daysLeft < 0) {
                    deadlineBadge = `<span class="badge bg-danger">Просрочено ${Math.abs(daysLeft)} д.</span>`;
                } else if (daysLeft === 0) {
                    deadlineBadge = `<span class="badge bg-warning">Сегодня</span>`;
                } else if (daysLeft <= 3) {
                    deadlineBadge = `<span class="badge bg-warning">${daysLeft} д.</span>`;
                } else {
                    deadlineBadge = `<span class="badge bg-secondary">${daysLeft} д.</span>`;
                }
            }
            
            const taskClass = task.completed ? 'task-item completed' : 'task-item';
            
            html += `
                <div class="${taskClass}" data-task-id="${task.id}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1 me-2">
                            <div class="form-check">
                                <input class="form-check-input task-checkbox" type="checkbox" 
                                       data-task-id="${task.id}" ${task.completed ? 'checked' : ''}>
                                <label class="form-check-label task-title">
                                    ${escapeHtml(task.title)}
                                </label>
                            </div>
                            ${task.description ? `
                                <small class="text-muted d-block mt-1">
                                    ${escapeHtml(task.description.substring(0, 50))}
                                    ${task.description.length > 50 ? '...' : ''}
                                </small>
                            ` : ''}
                            <div class="mt-2">
                                ${deadlineBadge}
                                <small class="text-muted ms-2">
                                    ${formatDate(task.created_at)}
                                </small>
                            </div>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary edit-task" data-task-id="${task.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger delete-task" data-task-id="${task.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        return html;
    }
    
    showTaskModal(task = null) {
        const modal = new bootstrap.Modal(document.getElementById('taskModal'));
        const title = document.getElementById('modalTitle');
        
        if (task) {
            title.textContent = 'Редактировать задачу';
            document.getElementById('taskId').value = task.id;
            document.getElementById('taskTitle').value = task.title;
            document.getElementById('taskDescription').value = task.description || '';
            document.getElementById('taskImportant').checked = task.is_important;
            
            if (task.deadline_at) {
                const deadline = new Date(task.deadline_at);
                deadline.setMinutes(deadline.getMinutes() - deadline.getTimezoneOffset());
                document.getElementById('taskDeadline').value = deadline.toISOString().slice(0, 16);
            } else {
                document.getElementById('taskDeadline').value = '';
            }
        } else {
            title.textContent = 'Новая задача';
            document.getElementById('taskForm').reset();
            document.getElementById('taskId').value = '';
        }
        
        modal.show();
    }
    
    async saveTask() {
        const taskId = document.getElementById('taskId').value;
        const taskData = {
            title: document.getElementById('taskTitle').value,
            description: document.getElementById('taskDescription').value,
            is_important: document.getElementById('taskImportant').checked,
            deadline_at: document.getElementById('taskDeadline').value || null
        };
        
        try {
            const token = getToken();
            let response;
            
            if (taskId) {
                response = await fetch(`${API_CONFIG.BASE_URL}/task/${taskId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(taskData)
                });
            } else {
                response = await fetch(`${API_CONFIG.BASE_URL}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(taskData)
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка сохранения');
            }
            
            showAlert(taskId ? 'Задача обновлена' : 'Задача создана', 'success');
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('taskModal'));
            modal.hide();
            
            await this.loadTasksPage();
        } catch (error) {
            showAlert(error.message || 'Ошибка сохранения задачи', 'danger');
        }
    }
    
    async changePassword() {
        const oldPassword = document.getElementById('oldPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const messageEl = document.getElementById('passwordMessage');
        
        if (newPassword !== confirmPassword) {
            messageEl.textContent = 'Новые пароли не совпадают';
            messageEl.className = 'alert alert-danger';
            messageEl.classList.remove('d-none');
            return;
        }
        
        if (newPassword.length < 6) {
            messageEl.textContent = 'Пароль должен содержать минимум 6 символов';
            messageEl.className = 'alert alert-danger';
            messageEl.classList.remove('d-none');
            return;
        }
        
        try {
            const result = await changePassword(oldPassword, newPassword);
            
            if (result.success) {
                messageEl.textContent = result.message;
                messageEl.className = 'alert alert-success';
                messageEl.classList.remove('d-none');
                
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('changePasswordModal'));
                    modal.hide();
                    document.getElementById('changePasswordForm').reset();
                    messageEl.classList.add('d-none');
                }, 2000);
            } else {
                messageEl.textContent = result.message;
                messageEl.className = 'alert alert-danger';
                messageEl.classList.remove('d-none');
            }
        } catch (error) {
            messageEl.textContent = 'Ошибка при смене пароля';
            messageEl.className = 'alert alert-danger';
            messageEl.classList.remove('d-none');
        }
    }
    
    async toggleTaskComplete(taskId) {
        try {
            const token = getToken();
            const response = await fetch(`${API_CONFIG.BASE_URL}/task/${taskId}/complete`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json',
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка изменения статуса задачи');
            }
            
            showAlert('Статус задачи изменен', 'success');
            await this.loadTasksPage();
        } catch (error) {
            showAlert(error.message || 'Ошибка изменения статуса задачи', 'danger');
        }
    }
    
    async deleteTask(taskId) {
        if (!confirm('Вы уверены, что хотите удалить эту задачу?')) {
            return;
        }
        
        try {
            const token = getToken();
            const response = await fetch(`${API_CONFIG.BASE_URL}/task/${taskId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка удаления задачи');
            }
            
            showAlert('Задача удалена', 'success');
            await this.loadTasksPage();
        } catch (error) {
            showAlert(error.message || 'Ошибка удаления задачи', 'danger');
        }
    }
    
    renderStatsPage(stats, deadlines, today) {
        const mainContent = document.getElementById('mainContent');
        
        let html = `
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stats-card bg-success text-white">
                        <div class="card-body text-center">
                            <h6 class="card-title">Выполнено</h6>
                            <h2 class="display-6">${stats.by_status.completed}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card bg-warning text-dark">
                        <div class="card-body text-center">
                            <h6 class="card-title">В работе</h6>
                            <h2 class="display-6">${stats.by_status.pending}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card bg-info text-white">
                        <div class="card-body text-center">
                            <h6 class="card-title">Процент выполнения</h6>
                            <h2 class="display-6">${completionRate}%</h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Распределение по квадрантам</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
        `;
        
        // Добавляем квадранты
        const quadrants = ['Q1', 'Q2', 'Q3', 'Q4'];
        const quadrantColors = {
            'Q1': 'danger',
            'Q2': 'success',
            'Q3': 'warning',
            'Q4': 'secondary'
        };
        
        quadrants.forEach(quadrant => {
            html += `
                <div class="col-3 text-center">
                    <div class="mb-2">
                        <span class="badge bg-${quadrantColors[quadrant]} fs-6 p-2">${quadrant}</span>
                    </div>
                    <h3>${stats.by_quadrant[quadrant] || 0}</h3>
                    <small class="text-muted">задач</small>
                </div>
            `;
        });
        
        html += `
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Статус дедлайнов</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-4 text-center">
                                    <div class="mb-2">
                                        <span class="badge bg-danger fs-6 p-2">Просрочено</span>
                                    </div>
                                    <h3>${deadlines.overdue_tasks}</h3>
                                </div>
                                <div class="col-4 text-center">
                                    <div class="mb-2">
                                        <span class="badge bg-warning text-dark fs-6 p-2">Срочные</span>
                                    </div>
                                    <h3>${deadlines.urgent_tasks}</h3>
                                </div>
                                <div class="col-4 text-center">
                                    <div class="mb-2">
                                        <span class="badge bg-secondary fs-6 p-2">Нормальные</span>
                                    </div>
                                    <h3>${deadlines.normal_tasks}</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Задачи на сегодня (${formatDate(new Date().toISOString())})</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-3">
                        <span>Всего задач: ${today.total_tasks_due_today}</span>
                        <span>Выполнено: ${today.by_status.completed} из ${today.total_tasks_due_today}</span>
                    </div>
        `;
        
        if (today.tasks.length > 0) {
            html += `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Задача</th>
                                <th>Квадрант</th>
                                <th>Статус</th>
                                <th>Создана</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            today.tasks.forEach(task => {
                html += `
                    <tr>
                        <td>${escapeHtml(task.title)}</td>
                        <td><span class="badge bg-${this.getQuadrantColor(task.quadrant)}">${task.quadrant}</span></td>
                        <td>
                            ${task.completed 
                                ? '<span class="badge bg-success">Выполнена</span>' 
                                : '<span class="badge bg-warning">В работе</span>'
                            }
                        </td>
                        <td>${formatDateTime(task.created_at)}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            html += '<p class="text-center text-muted">На сегодня задач нет</p>';
        }
        
        html += `
                </div>
            </div>
        `;
        
        mainContent.innerHTML = html;
    }
    
    async loadAdminPage() {
        const user = getUserInfo();
        if (user?.role !== 'admin') {
            showAlert('Доступ запрещен', 'danger');
            this.loadPage('tasks');
            return;
        }
        
        try {
            this.showLoading();
            const token = getToken();
            
            const response = await fetch(`${API_CONFIG.BASE_URL}/admin/users`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Ошибка загрузки админ-панели');
            }
            
            const users = await response.json();
            this.renderAdminPage(users);
        } catch (error) {
            this.showError('Ошибка загрузки админ-панели');
            console.error('Ошибка загрузки админ-панели:', error);
        }
    }
    
    renderAdminPage(users) {
        const mainContent = document.getElementById('mainContent');
        
        let html = `
            <h2 class="mb-4">Админ-панель</h2>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Все пользователи</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Никнейм</th>
                                    <th>Email</th>
                                    <th>Роль</th>
                                    <th>Кол-во задач</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        users.forEach(user => {
            html += `
                <tr>
                    <td>${user.id}</td>
                    <td>${escapeHtml(user.nickname)}</td>
                    <td>${escapeHtml(user.email)}</td>
                    <td>
                        ${user.role === 'admin' 
                            ? '<span class="badge bg-danger">Админ</span>' 
                            : '<span class="badge bg-secondary">Пользователь</span>'
                        }
                    </td>
                    <td>${user.task_count}</td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        mainContent.innerHTML = html;
    }
    
    getQuadrantColor(quadrant) {
        switch (quadrant) {
            case 'Q1': return 'danger';
            case 'Q2': return 'success';
            case 'Q3': return 'warning';
            case 'Q4': return 'secondary';
            default: return 'secondary';
        }
    }
    
    showLoading() {
        const mainContent = document.getElementById('mainContent');
        mainContent.innerHTML = `
            <div class="text-center mt-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
                <p class="mt-2">Загрузка данных...</p>
            </div>
        `;
    }
    
    showError(message) {
        const mainContent = document.getElementById('mainContent');
        mainContent.innerHTML = `
            <div class="alert alert-danger">
                ${message}
                <button class="btn btn-sm btn-outline-danger ms-3" onclick="window.location.reload()">
                    Обновить страницу
                </button>
            </div>
        `;
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('dashboard.html')) {
        new ToDoApp();
    }
});