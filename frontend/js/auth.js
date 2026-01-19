// Проверяем, что API_CONFIG определен
if (typeof API_CONFIG === 'undefined') {
    console.error('API_CONFIG не определен. Убедитесь, что config.js подключен перед auth.js');
}

// Получение токена
function getToken() {
    const token = localStorage.getItem(API_CONFIG.TOKEN_KEY);
    console.log('getToken вызван, токен:', token ? 'присутствует' : 'отсутствует');
    return token;
}

// Сохранение токена
function setToken(token) {
    localStorage.setItem(API_CONFIG.TOKEN_KEY, token);
}

// Выход
function logout() {
    localStorage.removeItem(API_CONFIG.TOKEN_KEY);
    localStorage.removeItem(API_CONFIG.USER_KEY);
    window.location.href = 'index.html';
}

// Проверка авторизации
function isAuthenticated() {
    return getToken() !== null;
}

// Функция входа
async function loginUser(email, password) {
    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            return { success: false, message: error.detail || 'Ошибка входа' };
        }
        
        const data = await response.json();
        console.log('Токен получен:', data.access_token);
        
        // Сохраняем токен
        setToken(data.access_token);
        
        // Получаем информацию о пользователе
        const userResponse = await fetch(`${API_CONFIG.BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${data.access_token}`,
                'Accept': 'application/json'
            }
        });
        
        if (userResponse.ok) {
            const userData = await userResponse.json();
            setUserInfo(userData);
            console.log('Пользователь сохранен:', userData);
        }
        
        return { success: true };
        
    } catch (error) {
        console.error('Ошибка входа:', error);
        return { success: false, message: 'Сетевая ошибка' };
    }
}

// Функция регистрации
async function registerUser(nickname, email, password) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                nickname: nickname,
                email: email,
                password: password
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            return { success: false, message: error.detail || 'Ошибка регистрации' };
        }
        
        // После успешной регистрации автоматически входим
        return await loginUser(email, password);
        
    } catch (error) {
        console.error('Ошибка регистрации:', error);
        return { success: false, message: 'Сетевая ошибка' };
    }
}

// Функция смены пароля
async function changePassword(oldPassword, newPassword) {
    try {
        const token = getToken();
        if (!token) {
            return { success: false, message: 'Не авторизован' };
        }
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/change-password`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            return { success: false, message: error.detail || 'Ошибка смены пароля' };
        }
        
        return { success: true, message: 'Пароль успешно изменен' };
        
    } catch (error) {
        console.error('Ошибка смены пароля:', error);
        return { success: false, message: 'Сетевая ошибка' };
    }
}

// Инициализация форм на login.html
if (window.location.pathname.includes('login.html')) {
    document.addEventListener('DOMContentLoaded', function() {
        // Проверяем, что API_CONFIG определен
        if (typeof API_CONFIG === 'undefined') {
            console.error('API_CONFIG не определен. Убедитесь, что config.js подключен перед auth.js');
            return;
        }
        
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const authMessage = document.getElementById('authMessage');
        
        // Обработка формы входа
        if (loginForm) {
            loginForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                
                authMessage.textContent = 'Вход...';
                authMessage.className = 'alert alert-info mt-3';
                authMessage.classList.remove('d-none');
                
                const result = await loginUser(email, password);
                
                if (result.success) {
                    authMessage.textContent = 'Успешный вход! Перенаправление...';
                    authMessage.className = 'alert alert-success mt-3';
                    
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1000);
                } else {
                    authMessage.textContent = result.message;
                    authMessage.className = 'alert alert-danger mt-3';
                }
            });
        }
        
        // Обработка формы регистрации
        if (registerForm) {
            registerForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const nickname = document.getElementById('registerNickname').value;
                const email = document.getElementById('registerEmail').value;
                const password = document.getElementById('registerPassword').value;
                
                authMessage.textContent = 'Регистрация...';
                authMessage.className = 'alert alert-info mt-3';
                authMessage.classList.remove('d-none');
                
                const result = await registerUser(nickname, email, password);
                
                if (result.success) {
                    authMessage.textContent = 'Регистрация успешна! Вход...';
                    authMessage.className = 'alert alert-success mt-3';
                    
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1000);
                } else {
                    authMessage.textContent = result.message;
                    authMessage.className = 'alert alert-danger mt-3';
                }
            });
        }
    });
}

// Проверка на dashboard.html
if (window.location.pathname.includes('dashboard.html')) {
    document.addEventListener('DOMContentLoaded', function() {
        if (!isAuthenticated()) {
            window.location.href = 'index.html';
            return;
        }
        
        // Показываем имя пользователя
        const user = getUserInfo();
        if (user) {
            const greeting = document.getElementById('userGreeting');
            if (greeting) {
                greeting.textContent = `Привет, ${user.nickname}!`;
            }
        }
        
        // Кнопка выхода
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                logout();
            });
        }
    });
}