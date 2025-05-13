from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64
import os
from pathlib import Path
from datetime import datetime
from collections import Counter
import re

# Регистрация шрифта DejaVuSans из папки font
font_path = Path('fonts/DejaVuSans.ttf')
if font_path.exists():
    pdfmetrics.registerFont(TTFont('DejaVuSans', str(font_path)))
else:
    print("Warning: DejaVuSans.ttf not found in fonts directory")

def get_word_frequency(filename, min_word_length=3):
    """
    Анализирует текстовый файл и возвращает список наиболее часто встречающихся слов.
    
    Args:
        filename (str): Путь к файлу для анализа
        min_word_length (int, optional): Минимальная длина слова для учета. По умолчанию 3.
    
    Returns:
        list: Список кортежей (слово, количество) отсортированный по частоте использования.
              Возвращает пустой список в случае ошибки.
    
    Процесс работы:
    1. Читает файл с указанной кодировкой UTF-8
    2. Извлекает русские слова с помощью регулярных выражений
    3. Фильтруем слова по минимальной длине
    4. Исключаем стоп-слова
    5. Подсчитывает частоту каждого слова
    6. Возвращает топ-50 наиболее часто встречающихся слов
    """
    try:
        # Преобразуем путь в объект Path
        file_path = Path(filename)
        print(f"Trying to read file: {file_path}")
        print(f"File exists: {file_path.exists()}")
        
        if not file_path.exists():
            print(f"File not found: {filename}")
            return []
            
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            print(f"Successfully read file. Text length: {len(text)}")
            
            # Улучшенное регулярное выражение для русских слов
            # Ищем слова, начинающиеся с буквы, содержащие только буквы
            words = re.findall(r'[а-яА-ЯёЁ][а-яА-ЯёЁ-]*[а-яА-ЯёЁ]', text)
            print(f"Found {len(words)} words")
            
            # Фильтруем слова по длине
            words = [word for word in words if len(word) >= min_word_length]
            print(f"After length filtering: {len(words)} words")
            
            if not words:
                print("No words found in the text")
                return []
                
            # Приводим все слова к нижнему регистру для корректного подсчета
            words = [word.lower() for word in words]
            
            # Исключаем стоп-слова
            stop_words = {'это', 'что', 'как', 'для', 'если', 'или', 'но', 'и', 'а', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'от', 'до', 'за', 'из', 'над', 'под', 'при', 'через', 'без', 'между', 'перед', 'после', 'через', 'во', 'со', 'об', 'не', 'нет', 'да', 'нет', 'быть', 'есть', 'был', 'была', 'было', 'были', 'стать', 'стал', 'стала', 'стало', 'стали', 'мочь', 'могу', 'можешь', 'может', 'можем', 'можете', 'могут', 'хотеть', 'хочу', 'хочешь', 'хочет', 'хотим', 'хотите', 'хотят'}
            words = [word for word in words if word not in stop_words]
            print(f"After filtering stop words: {len(words)} words")
            
            result = Counter(words).most_common(50)
            print(f"Returning {len(result)} most common words")
            return result
            
    except Exception as e:
        print(f"Error in get_word_frequency: {str(e)}")
        return []

def create_pdf(filepath, plots, word_count):
    """
    Создает PDF-отчет с анализом чата Telegram, включая графики и статистику.
    
    Args:
        filepath (str): Путь к файлу с историей чата
        plots (list): Список графиков в формате base64
        word_count (int): Общее количество слов в чате
    
    Returns:
        tuple: (str, str) - Путь к созданному PDF файлу и его имя
    
    Raises:
        Exception: При ошибке создания PDF файла
    
    Структура PDF:
    1. Титульная страница с заголовком и общей статистикой
    2. Страница с частотным анализом слов
    3. Страницы с графиками:
       - Активность по месяцам и дням
       - Распределение сообщений по часам
       - Распределение длины сообщений
       - Топ-10 активных участников
       - Облако слов
       - Эмоциональный окрас сообщений
       - Распределение длины слов
       - Активность по дням недели
       - Средняя длина сообщений по отправителям
       - Активность по времени суток
    
    Особенности:
    - Использует шрифт DejaVuSans для поддержки русского языка
    - Автоматически создает новые страницы при необходимости
    - Центрирует и масштабирует графики для оптимального отображения
    - Сохраняет временные файлы для графиков и удаляет их после использования
    """
    try:
        # Создание PDF
        pdf_filename = f"telegram_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = Path(filepath).parent / pdf_filename
        c = canvas.Canvas(str(pdf_path), pagesize=A4)  # Используем A4 для большего пространства
        width, height = A4

        # Добавление заголовка
        c.setFont("DejaVuSans", 24)
        c.drawString(2*cm, height - 2*cm, "Анализ чата Telegram")
        c.setFont("DejaVuSans", 12)

        # Добавление статистики
        c.drawString(2*cm, height - 4*cm, f"Всего слов: {word_count}")

        # Анализ частоты слов
        word_freq = get_word_frequency(filepath)
        
        if word_freq:
            # Добавление списка частых слов
            c.setFont("DejaVuSans", 16)
            c.drawString(2*cm, height - 6*cm, "Часто используемые слова:")
            c.setFont("DejaVuSans", 12)
            
            # Настройки для отображения слов в один столбец
            y_position = height - 8*cm
            x_position = 2*cm
            line_height = 0.7*cm  # Высота строки
            words_per_page = 35   # Количество слов на странице
            
            for i, (word, count) in enumerate(word_freq):
                text = f"{word}: {count}"
                c.drawString(x_position, y_position, text)
                y_position -= line_height
                
                # Если достигли конца страницы, создаем новую
                if y_position < 2*cm or (i + 1) % words_per_page == 0:
                    c.showPage()
                    c.setFont("DejaVuSans", 12)
                    y_position = height - 2*cm
                    x_position = 2*cm
        else:
            c.setFont("DejaVuSans", 12)
            c.drawString(2*cm, height - 6*cm, "Не удалось проанализировать частоту слов")

        # Заголовки для каждой диаграммы
        diagram_titles = [
            "Активность по месяцам и дням",
            "Распределение сообщений по часам суток",
            "Распределение длины сообщений",
            "Топ-10 самых активных участников",
            "Облако слов",
            "Эмоциональный окрас сообщений по дням",
            "Распределение длины слов",
            "Активность по дням недели",
            "Средняя длина сообщений по отправителям",
            "Активность по времени суток"
        ]

        # Добавление графиков
        for i, plot_data in enumerate(plots):
            if not plot_data:  # Пропускаем пустые графики
                continue
                
            try:
                # Создаем новую страницу для каждого графика
                c.showPage()
                
                # Добавляем заголовок для графика
                c.setFont("DejaVuSans", 16)
                c.drawString(2*cm, height - 2*cm, diagram_titles[i])
                c.setFont("DejaVuSans", 12)
                
                # Декодирование base64 данных
                plot_bytes = base64.b64decode(plot_data)
                
                # Сохранение во временный файл с уникальным именем
                temp_file = f"temp_plot_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                with open(temp_file, 'wb') as f:
                    f.write(plot_bytes)
                
                # Используем большую часть страницы для изображения
                image_width = width - 4*cm
                image_height = height - 6*cm
                
                # Центрируем изображение на странице
                x_position = 2*cm
                y_position = height - 6*cm
                
                c.drawImage(
                    temp_file,
                    x_position,
                    y_position - image_height,
                    width=image_width,
                    height=image_height,
                    preserveAspectRatio=True
                )
                
                # Удаление временного файла
                os.remove(temp_file)
                
            except Exception as e:
                print(f"Error adding plot {i} to PDF: {str(e)}")
                continue

        c.save()
        return str(pdf_path), pdf_filename

    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        raise  # Пробрасываем исключение дальше
