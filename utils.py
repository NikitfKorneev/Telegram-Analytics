import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from collections import defaultdict
from wordcloud import WordCloud
import numpy as np

def count_words_in_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
        words = text.split()
        return len(words)

def create_plots(filename, min_word_length=5):
    plots = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        sender_counts = defaultdict(int)
        day_counts = defaultdict(int)
        hour_counts = defaultdict(int)
        word_counts = defaultdict(int)
        non_text_counts = defaultdict(int)
        message_lengths = []
        month_day_counts = defaultdict(lambda: [0] * 31)

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

                day_counts[date] += 1
                hour_counts[hour] += 1
                sender_counts[sender_id] += 1
                message_lengths.append(len(message))
                month_day_counts[year_month][day - 1] += 1

                if not message.strip():
                    non_text_counts[sender_id] += 1

                for word in message.split():
                    if len(word) >= min_word_length:
                        word_counts[word] += 1

            except (IndexError, ValueError) as e:
                continue

        # График 1: Активность по месяцам и дням
        plt.figure(figsize=(10, 6))
        months = sorted(month_day_counts.keys())
        heatmap_data = [month_day_counts[month] for month in months]
        sns.heatmap(heatmap_data, annot=False, fmt="d", cmap="YlGnBu", xticklabels=range(1, 32), yticklabels=months)
        plt.title('Активность по месяцам и дням')
        plt.xlabel('День')
        plt.ylabel('Месяц')
        plt.xticks(rotation=45)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 2: Сообщения по авторам
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(sender_counts.keys()), y=list(sender_counts.values()))
        plt.title('Сообщения по авторам')
        plt.xlabel('Автор')
        plt.ylabel('Количество сообщений')
        plt.xticks(rotation=45)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 3: Активность по часам
        plt.figure(figsize=(10, 6))
        sns.heatmap(np.array([list(hour_counts.values())]), annot=True, fmt="d", cmap="YlGnBu")
        plt.title('Активность по часам')
        plt.xlabel('Час')
        plt.ylabel('Активность')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 4: Нетекстовые сообщения
        plt.figure(figsize=(10, 6))
        plt.pie(non_text_counts.values(), labels=non_text_counts.keys(), autopct='%1.1f%%')
        plt.title('Нетекстовые сообщения')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # График 5: Слова по частоте
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Слова по частоте (от 5 букв)')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

    except Exception as e:
        print(f"Error generating plots: {str(e)}")

    return plots