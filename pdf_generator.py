from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64
import os
from pathlib import Path

# Регистрация шрифта DejaVuSans из папки font
font_path = Path('font/DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', str(font_path)))

def create_pdf(filepath, plots, word_list):
    try:
        # Создание PDF
        pdf_path = Path(filepath).with_suffix('.pdf')
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        width, height = letter

        # Добавление заголовка
        c.setFont("DejaVuSans", 24)
        c.drawString(1*inch, height - 1*inch, "Анализ чата Telegram")
        c.setFont("DejaVuSans", 12)

        # Сохранение графиков во временные файлы и добавление их в PDF
        y_position = height - 2*inch
        for i, plot_data in enumerate(plots):
            # Декодирование base64 данных
            plot_bytes = base64.b64decode(plot_data)
            
            # Сохранение во временный файл
            temp_file = f"temp_plot_{i}.png"
            with open(temp_file, 'wb') as f:
                f.write(plot_bytes)
            
            # Добавление изображения в PDF
            c.drawImage(temp_file, 1*inch, y_position - 3*inch, width=6*inch, height=3*inch)
            y_position -= 4*inch
            
            # Удаление временного файла
            os.remove(temp_file)
            
            if y_position < 2*inch:
                c.showPage()
                c.setFont("DejaVuSans", 12)
                y_position = height - 1*inch

        # Добавление списка слов
        c.showPage()
        c.setFont("DejaVuSans", 16)
        c.drawString(1*inch, height - 1*inch, "Частотный список слов")
        c.setFont("DejaVuSans", 12)

        # Добавление слов в две колонки
        y_position = height - 2*inch
        x_position = 1*inch
        column_width = 3*inch
        words_per_column = 50

        for i, (word, count) in enumerate(word_list[:100]):
            if i % words_per_column == 0 and i > 0:
                x_position += column_width + 1*inch
                y_position = height - 2*inch

            text = f"{word}: {count}"
            c.drawString(x_position, y_position, text)
            y_position -= 0.3*inch

            if y_position < 1*inch:
                c.showPage()
                c.setFont("DejaVuSans", 12)
                y_position = height - 1*inch
                x_position = 1*inch

        c.save()
        return str(pdf_path)

    except Exception as e:
        print(f"Ошибка при генерации PDF: {str(e)}")
        return None
