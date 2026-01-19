const API_CONFIG = {
    BASE_URL: 'http://localhost:8000/api/v3',
    TOKEN_KEY: 'todo_matrix_token',
    USER_KEY: 'todo_matrix_user'
};

console.log('API_CONFIG загружен:', API_CONFIG);

function showAlert(message, type = 'danger') {
    const container = document.getElementById('alertContainer');
    if (container) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.prepend(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

function calculateDaysUntilDeadline(deadlineAt) {
    if (!deadlineAt) return null;
    
    const deadline = new Date(deadlineAt);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadline.setHours(0, 0, 0, 0);
    
    const diffTime = deadline - today;
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getUserInfo() {
    const userJson = localStorage.getItem(API_CONFIG.USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
}

function setUserInfo(user) {
    localStorage.setItem(API_CONFIG.USER_KEY, JSON.stringify(user));
}