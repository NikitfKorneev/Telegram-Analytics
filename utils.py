import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from collections import defaultdict
from wordcloud import WordCloud
import numpy as np
from pathlib import Path
from pdf_generator import create_pdf

def count_words_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()
        words = text.split()
        return len(words)

def create_plots(filepath, min_word_length=5):
    plots = []
    word_list = []  # Store words for PDF

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        sender_counts = defaultdict(int)
        month_day_counts = defaultdict(lambda: [0] * 31)
        hour_counts = defaultdict(int)
        word_counts = defaultdict(int)
        message_lengths = []

        for line in lines:
            parts = line.split(' - ')
            if len(parts) < 2:
                continue

            try:
                date_time = parts[0].split()
                if len(date_time) < 2:
                    continue

                sender_message = parts[1].split(':', 1)
                if len(sender_message) < 2:
                    continue

                sender_id = sender_message[0].strip()
                message = sender_message[1].strip()

                date = date_time[0]
                time_parts = date_time[1].split(':')
                if len(time_parts) < 1:
                    continue

                hour = int(time_parts[0])
                year_month = date[:7]
                day = int(date[8:10])

                sender_counts[sender_id] += 1
                hour_counts[hour] += 1
                message_lengths.append(len(message))
                month_day_counts[year_month][day - 1] += 1

                for word in message.split():
                    if len(word) >= min_word_length:
                        word_counts[word.lower()] += 1

            except (IndexError, ValueError):
                continue

        # Sort words by frequency for the PDF
        word_list = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # График 1: Активность по месяцам и дням
        plt.figure(figsize=(12, 6))
        months = sorted(month_day_counts.keys())
        heatmap_data = [month_day_counts[month] for month in months]
        sns.heatmap(heatmap_data, cmap="YlGnBu", xticklabels=range(1, 32), yticklabels=months)
        plt.title('Активность по дням месяца')
        plt.xlabel('День месяца')
        plt.ylabel('Месяц')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 2: Топ отправителей
        plt.figure(figsize=(10, 6))
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        sns.barplot(x=[v for k, v in top_senders], y=[k for k, v in top_senders])
        plt.title('Топ 10 отправителей')
        plt.xlabel('Количество сообщений')
        plt.ylabel('Отправитель')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 3: Активность по часам
        plt.figure(figsize=(10, 6))
        hours = sorted(hour_counts.keys())
        values = [hour_counts[h] for h in hours]
        sns.lineplot(x=hours, y=values)
        plt.title('Активность по часам')
        plt.xlabel('Час дня')
        plt.ylabel('Количество сообщений')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 4: Распределение длины сообщений
        plt.figure(figsize=(10, 6))
        sns.histplot(message_lengths, bins=50)
        plt.title('Распределение длины сообщений')
        plt.xlabel('Длина сообщения')
        plt.ylabel('Количество')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 5: Облако слов
        if word_counts:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Частые слова (от {} букв)'.format(min_word_length))
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
            plt.close()

        # Create PDF
        pdf_path = create_pdf(filepath, plots, word_list)
        if pdf_path:
            print(f"PDF created successfully: {pdf_path}")
        else:
            print("Failed to create PDF")

    except Exception as e:
        print(f"Error generating plots: {str(e)}")

    return plots