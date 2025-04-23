document.addEventListener('DOMContentLoaded', () => {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
        themeToggle.textContent = '☀️';
    }
    
    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-theme');
        const isDark = body.classList.contains('dark-theme');
        themeToggle.textContent = isDark ? '☀️' : '🌙';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // Auth elements
    const authSection = document.getElementById('authSection');
    const mainContent = document.getElementById('mainContent');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const toggleRegister = document.getElementById('toggleRegister');
    const toggleLogin = document.getElementById('toggleLogin');
    const authError = document.getElementById('authError');
    const authTitle = document.getElementById('authTitle');
    const guestButtons = document.querySelector('.auth-buttons-guest');
    const userButtons = document.querySelector('.auth-buttons-user');
    const usernameSpan = document.querySelector('.username');

    // Auth functions
    async function login(username, password) {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            
            const response = await fetch('/auth/token', {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('username', username); // Store username
                updateAuthUI(true, username);
                checkAuth();
            } else {
                showAuthError('Неверное имя пользователя или пароль');
            }
        } catch (error) {
            showAuthError('Ошибка соединения');
            console.error('Login error:', error);
        }
    }
    
    async function register(username, email, password) {
        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });
            
            if (response.ok) {
                showAuthMessage('Регистрация успешна! Войдите в систему', 'success');
                toggleForms();
            } else {
                const error = await response.json();
                showAuthError(error.detail || 'Ошибка регистрации');
            }
        } catch (error) {
            showAuthError('Ошибка соединения');
            console.error('Registration error:', error);
        }
    }
    
    function updateAuthUI(isAuthenticated, username = '') {
        if (isAuthenticated) {
            if (guestButtons) guestButtons.classList.add('hidden');
            if (userButtons) userButtons.classList.remove('hidden');
            if (usernameSpan) usernameSpan.textContent = username;
        } else {
            if (guestButtons) guestButtons.classList.remove('hidden');
            if (userButtons) userButtons.classList.add('hidden');
            if (usernameSpan) usernameSpan.textContent = '';
        }
    }
    
    function logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        updateAuthUI(false);
        window.location.href = '/';
    }
    
    async function checkAuth() {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        
        if (!token) {
            updateAuthUI(false);
            return;
        }
        
        try {
            const response = await fetch('/protected-route', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                updateAuthUI(true, username);
            } else {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                updateAuthUI(false);
            }
        } catch (error) {
            console.error('Auth check error:', error);
            updateAuthUI(false);
        }
    }
    
    function showAuth() {
        authSection.classList.remove('hidden');
        mainContent.classList.add('hidden');
    }
    
    function showMainContent() {
        authSection.classList.add('hidden');
        mainContent.classList.remove('hidden');
    }
    
    function showAuthError(message) {
        authError.textContent = message;
        authError.classList.remove('hidden', 'alert-success');
        authError.classList.add('alert-danger');
    }
    
    function showAuthMessage(message, type = 'success') {
        authError.textContent = message;
        authError.classList.remove('hidden', 'alert-danger');
        authError.classList.add('alert-' + type);
    }
    
    function toggleForms() {
        loginForm.classList.toggle('hidden');
        registerForm.classList.toggle('hidden');
        authTitle.textContent = loginForm.classList.contains('hidden') ? 'Регистрация' : 'Вход';
    }
    
    // Event listeners for auth
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        login(username, password);
    });
    
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        register(username, email, password);
    });
    
    toggleRegister.addEventListener('click', toggleForms);
    toggleLogin.addEventListener('click', toggleForms);
    logoutBtn.addEventListener('click', logout);
    
    // Telegram Analytics functionality
    document.getElementById('chatForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const chatName = document.getElementById('chat_name').value.trim();
        const startDate = document.getElementById('start_date').value;
        const endDate = document.getElementById('end_date').value;
        const minWordLength = document.getElementById('min_word_length').value;
        
        const progressBar = document.getElementById('progressBar');
        const progressContainer = document.getElementById('progressContainer');
        const errorAlert = document.getElementById('errorAlert');
        
        // Reset state
        errorAlert.style.display = 'none';
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        
        const token = localStorage.getItem('token');
        if (!token) {
            showAuthError('Требуется авторизация');
            return;
        }
        
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = function() {
            ws.send(JSON.stringify({
                chat_name: chatName,
                start_date: startDate,
                end_date: endDate,
                token: token
            }));
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.status === 'loading') {
                const progress = Math.round(data.progress);
                progressBar.style.width = `${progress}%`;
                progressBar.textContent = `${progress}%`;
            } 
            else if (data.status === 'completed') {
                window.location.href = `/get_history?filename=${encodeURIComponent(data.filename)}&min_word_length=${minWordLength}`;
            } 
            else if (data.status === 'error') {
                errorAlert.textContent = data.message;
                errorAlert.style.display = 'block';
                progressContainer.style.display = 'none';
                
                if (data.message.includes('авторизации')) {
                    logout();
                }
            }
        };
        
        ws.onerror = function() {
            errorAlert.textContent = 'Ошибка соединения с сервером';
            errorAlert.style.display = 'block';
            progressContainer.style.display = 'none';
        };
    });
    
    // Check auth on load
    checkAuth();
}); 