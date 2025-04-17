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
const modal = document.getElementById('modal');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const closeBtn = document.querySelector('.close-btn');

// Открытие модального окна для входа
document.getElementById('open-login-modal').addEventListener('click', (e) => {
    e.preventDefault();
    modal.style.display = 'flex';
    registerForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
});

// Открытие модального окна для регистрации
document.getElementById('open-register-modal').addEventListener('click', (e) => {
    e.preventDefault();
    modal.style.display = 'flex';
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
});

// Главная кнопка регистрации
document.getElementById('main-register-btn').addEventListener('click', (e) => {
    e.preventDefault();
    modal.style.display = 'flex';
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
});

// Закрытие модального окна
closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

// Закрытие модального окна при клике вне его
window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Переключение между формами
document.getElementById('switch-to-register').addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
});

document.getElementById('switch-to-login').addEventListener('click', (e) => {
    e.preventDefault();
    registerForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
});

// Закрытие по Esc
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        document.getElementById('modal').style.display = 'none';
    }
});

// Обработка формы чата
const chatForm = document.getElementById('chatForm');
if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Требуется авторизация');
            window.location.href = '/';
            return;
        }

        const chatName = document.getElementById('chat_name').value;
        const startDate = document.getElementById('start_date').value;
        const endDate = document.getElementById('end_date').value;

        const progressBar = document.querySelector('.progress-bar');
        const progressContainer = document.querySelector('.progress-container');
        const errorAlert = document.getElementById('errorAlert');

        progressContainer.style.display = 'block';
        errorAlert.style.display = 'none';

        const ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onopen = () => {
            ws.send(JSON.stringify({
                chat_name: chatName,
                start_date: startDate,
                end_date: endDate
            }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === 'loading') {
                const progress = Math.round(data.progress);
                progressBar.style.width = `${progress}%`;
                progressBar.textContent = `${progress}%`;
            } else if (data.status === 'completed') {
                window.location.href = `/get_history?filename=${encodeURIComponent(data.filename)}`;
            } else if (data.status === 'error') {
                errorAlert.textContent = data.message;
                errorAlert.style.display = 'block';
                progressContainer.style.display = 'none';
            }
        };

        ws.onerror = () => {
            errorAlert.textContent = 'Ошибка соединения с сервером';
            errorAlert.style.display = 'block';
            progressContainer.style.display = 'none';
        };
    });
}

// Login form submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('login-error');
    errorDiv.style.display = 'none';

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                username: username,
                password: password,
                grant_type: 'password'
            })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            window.location.href = '/';
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Ошибка входа';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Ошибка соединения с сервером';
        errorDiv.style.display = 'block';
    }
});

// Registration form submission
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('register-error');
    errorDiv.style.display = 'none';

    const name = document.getElementById('register-name').value;
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (password !== confirmPassword) {
        errorDiv.textContent = 'Пароли не совпадают';
        errorDiv.style.display = 'block';
        return;
    }

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                username: username,
                email: email || null,
                password: password
            })
        });

        if (response.ok) {
            // После успешной регистрации переключаем на форму входа
            window.location.href = '/welcome?form=login';
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Ошибка регистрации';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Ошибка соединения с сервером';
        errorDiv.style.display = 'block';
    }
});

// Проверка авторизации при загрузке страницы
async function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const response = await fetch('/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                // Обновляем UI для авторизованного пользователя
                const authButtons = document.querySelector('.auth-buttons');
                if (authButtons) {
                    authButtons.innerHTML = `
                        <span class="user-info">${userData.name}</span>
                        <button id="logout-btn" class="btn-secondary">Выйти</button>
                        <button id="theme-toggle" class="btn-theme">🌙</button>
                    `;
                    
                    // Добавляем обработчик для кнопки выхода
                    document.getElementById('logout-btn').addEventListener('click', logout);
                }
            } else {
                // Если токен невалидный, очищаем его
                localStorage.removeItem('token');
            }
        } catch (error) {
            console.error('Ошибка проверки авторизации:', error);
        }
    }
}

// Функция выхода
function logout() {
    localStorage.removeItem('token');
    window.location.reload();
}

// Проверяем авторизацию при загрузке страницы
document.addEventListener('DOMContentLoaded', checkAuth);