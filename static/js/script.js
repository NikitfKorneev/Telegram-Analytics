// Переключение темы
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// Проверяем сохраненную тему в localStorage
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
  body.classList.add('dark-theme');
  themeToggle.textContent = '☀️'; // Иконка солнца для темной темы
} else {
  body.classList.remove('dark-theme');
  themeToggle.textContent = '🌙'; // Иконка луны для светлой темы
}

// Переключение темы по клику
themeToggle.addEventListener('click', () => {
  body.classList.toggle('dark-theme');

  if (body.classList.contains('dark-theme')) {
    localStorage.setItem('theme', 'dark'); // Сохраняем выбор в localStorage
    themeToggle.textContent = '☀️'; // Иконка солнца
  } else {
    localStorage.setItem('theme', 'light'); // Сохраняем выбор в localStorage
    themeToggle.textContent = '🌙'; // Иконка луны
  }
});

// Открытие модального окна (Вход)
document.getElementById('open-login-modal').addEventListener('click', function () {
  document.getElementById('modal').style.display = 'flex';
  document.getElementById('register-form').classList.add('hidden');
  document.getElementById('login-form').classList.remove('hidden');
});

// Открытие модального окна (Регистрация)
document.getElementById('open-register-modal').addEventListener('click', function () {
  document.getElementById('modal').style.display = 'flex';
  document.getElementById('login-form').classList.add('hidden');
  document.getElementById('register-form').classList.remove('hidden');
});

// Закрытие модального окна кнопкой "закрыть"
document.querySelector('.close-btn').addEventListener('click', function () {
  document.getElementById('modal').style.display = 'none';
});

// Переключение между формами входа и регистрации
document.getElementById('switch-to-register').addEventListener('click', function (e) {
  e.preventDefault();
  document.getElementById('login-form').classList.add('hidden');
  document.getElementById('register-form').classList.remove('hidden');
});

document.getElementById('switch-to-login').addEventListener('click', function (e) {
  e.preventDefault();
  document.getElementById('register-form').classList.add('hidden');
  document.getElementById('login-form').classList.remove('hidden');
});

// Проверка совпадения паролей при регистрации
document.getElementById('register-form').addEventListener('submit', function (e) {
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  if (password !== confirmPassword) {
    e.preventDefault(); // Предотвращаем отправку формы
    alert('Пароли не совпадают. Пожалуйста, попробуйте снова.');
  }
});

// Закрытие модального окна при нажатии клавиши Esc
document.addEventListener('keydown', function (event) {
  // Проверяем, была ли нажата клавиша Esc
  if (event.key === 'Escape' || event.keyCode === 27) {
    const modal = document.getElementById('modal');
    if (modal && modal.style.display === 'flex') {
      modal.style.display = 'none'; // Закрываем модальное окно
    }
  }
});

// Логика для страницы личного кабинета
if (window.location.pathname.includes('profile.html')) {
  // Загрузка данных пользователя
  const userName = localStorage.getItem('userName') || 'Пользователь';
  const userEmail = localStorage.getItem('userEmail') || 'example@example.com';

  document.getElementById('user-name').textContent = userName;
  document.getElementById('user-email').textContent = userEmail;

  // Кнопка "Выйти"
  document.getElementById('logout-btn').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    window.location.href = 'index.html'; // Переход на главную страницу
  });

  // Кнопка "Редактировать профиль"
  document.getElementById('edit-profile-btn').addEventListener('click', () => {
    alert('Функция редактирования профиля пока недоступна.');
  });
}

// Логика для формы входа
document.getElementById('login-form').addEventListener('submit', function (e) {
  e.preventDefault();

  const loginEmail = document.getElementById('login-email').value;
  const loginPassword = document.getElementById('login-password').value;

  // Пример проверки данных (замените на реальную логику аутентификации)
  if (loginEmail && loginPassword) {
    localStorage.setItem('userName', 'Имя пользователя'); // Пример имени
    localStorage.setItem('userEmail', loginEmail); // Сохраняем email
    window.location.href = 'profile.html'; // Переход в личный кабинет
  } else {
    alert('Неверный email или пароль. Попробуйте снова.');
  }
});

// Логика для формы регистрации
document.getElementById('register-form').addEventListener('submit', function (e) {
  e.preventDefault();

  const registerName = document.getElementById('register-name').value;
  const registerEmail = document.getElementById('register-email').value;
  const registerPassword = document.getElementById('register-password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  if (registerPassword !== confirmPassword) {
    alert('Пароли не совпадают. Пожалуйста, попробуйте снова.');
    return;
  }

  // Пример регистрации (замените на реальную логику)
  localStorage.setItem('userName', registerName);
  localStorage.setItem('userEmail', registerEmail);

  alert('Регистрация успешна! Вы будете перенаправлены на страницу входа.');
  document.getElementById('switch-to-login').click(); // Переключаемся на форму входа
});



document.querySelectorAll('.sidebar-nav a').forEach(link => {
  link.addEventListener('click', function (e) {
    e.preventDefault();

    // Убираем активный класс у всех ссылок
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));

    // Добавляем активный класс текущей ссылке
    this.classList.add('active');

    // Скрываем все разделы
    document.querySelectorAll('.main-content section').forEach(section => section.classList.add('hidden'));

    // Показываем выбранный раздел
    const target = this.getAttribute('href').substring(1);
    document.getElementById(target).classList.remove('hidden');
  });
});