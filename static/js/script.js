// Переключение темы
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// Проверяем сохраненную тему
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    body.classList.add('dark-theme');
    themeToggle.textContent = '☀️';
} else {
    themeToggle.textContent = '🌙';
}

// Обработчик переключения темы
themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    const isDark = body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    themeToggle.textContent = isDark ? '☀️' : '🌙';
});

// Модальные окна
document.getElementById('open-login-modal').addEventListener('click', () => {
    document.getElementById('modal').style.display = 'flex';
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('login-form').classList.remove('hidden');
});

document.getElementById('open-register-modal').addEventListener('click', () => {
    document.getElementById('modal').style.display = 'flex';
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
});

document.querySelector('.close-btn').addEventListener('click', () => {
    document.getElementById('modal').style.display = 'none';
});

// Переключение между формами
document.getElementById('switch-to-register').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
});

document.getElementById('switch-to-login').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('login-form').classList.remove('hidden');
});

// Закрытие по Esc
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        document.getElementById('modal').style.display = 'none';
    }
});

// Функция для авторизованных запросов
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('authToken');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка запроса');
    }
    
    return response.json();
}

// Логин
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        username: formData.get('login-username'),
        password: formData.get('login-password'),
        grant_type: 'password'
    };
    
    try {
        const response = await fetch('/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка входа');
        }
        
        const { access_token } = await response.json();
        localStorage.setItem('authToken', access_token);
        window.location.href = '/profile';
    } catch (error) {
        alert(error.message);
        console.error('Login error:', error);
    }
});

// Регистрация
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (document.getElementById('register-password').value !== 
        document.getElementById('confirm-password').value) {
        alert('Пароли не совпадают');
        return;
    }
    
    const formData = new FormData(e.target);
    const data = {
        username: formData.get('register-username'),
        password: formData.get('register-password'),
        email: formData.get('register-email') || null,
        name: formData.get('register-name')
    };
    
    try {
        await authFetch('/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        alert('Регистрация успешна! Теперь вы можете войти.');
        document.getElementById('switch-to-login').click();
    } catch (error) {
        alert(error.message);
        console.error('Registration error:', error);
    }
});

// Проверка аутентификации
async function checkAuth() {
    const token = localStorage.getItem('authToken');
    if (!token) return;

    try {
        const user = await authFetch('/users/me');
        updateAuthUI(user);
    } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('authToken');
    }
}

function updateAuthUI(user) {
    const authButtons = document.querySelector('.auth-buttons');
    authButtons.innerHTML = `
        <span class="username">${user.username}</span>
        <button id="logout-btn" class="btn-primary">Выйти</button>
        <button id="theme-toggle" class="btn-theme">${body.classList.contains('dark-theme') ? '☀️' : '🌙'}</button>
    `;
    
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('authToken');
        window.location.href = '/';
    });
}

// Инициализация
document.addEventListener('DOMContentLoaded', checkAuth);