import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from collections import defaultdict
from wordcloud import WordCloud
import numpy as np
from pathlib import Path
from textblob import TextBlob
from datetime import datetime

def count_words_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
            words = text.split()
            return len(words)
    except Exception as e:
        print(f"Error counting words: {str(e)}")
        return 0

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
        day_sentiment = defaultdict(list)
        word_lengths = defaultdict(int)
        day_of_week_counts = defaultdict(int)
        sender_avg_lengths = defaultdict(list)
        time_period_counts = defaultdict(int)
        non_text_messages_by_hour = defaultdict(int)

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
                
                # Get day of week
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                day_of_week = date_obj.strftime('%A')
                
                # Check if message is non-text (contains only special characters or is empty)
                is_non_text = not any(c.isalnum() for c in message)
                
                if is_non_text:
                    non_text_messages_by_hour[hour] += 1
                else:
                    # Calculate sentiment only for text messages
                    sentiment = TextBlob(message).sentiment.polarity
                    day_sentiment[date].append(sentiment)
                    
                    # Count word lengths only for text messages
                    for word in message.split():
                        word_lengths[len(word)] += 1
                    
                    # Add message length only for text messages
                    message_lengths.append(len(message))
                    
                    # Count words for word cloud only for text messages
                    for word in message.split():
                        if len(word) >= min_word_length:
                            word_counts[word.lower()] += 1
                
                # Calculate time period
                if 5 <= hour < 12:
                    time_period = 'Morning'
                elif 12 <= hour < 17:
                    time_period = 'Afternoon'
                elif 17 <= hour < 22:
                    time_period = 'Evening'
                else:
                    time_period = 'Night'
                
                sender_counts[sender_id] += 1
                hour_counts[hour] += 1
                month_day_counts[year_month][day - 1] += 1
                day_of_week_counts[day_of_week] += 1
                sender_avg_lengths[sender_id].append(len(message))
                time_period_counts[time_period] += 1

            except (IndexError, ValueError):
                continue

        # Sort words by frequency for the PDF
        word_list = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Plot 1: Activity by months and days
        plt.figure(figsize=(12, 8))
        sns.heatmap([month_day_counts[month] for month in sorted(month_day_counts.keys())], 
                   xticklabels=range(1, 32), 
                   yticklabels=sorted(month_day_counts.keys()), 
                   cmap='YlOrRd')
        plt.title('Активность по месяцам и дням')
        plt.xlabel('День месяца')
        plt.ylabel('Месяц')
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 2: Message distribution by hour
        plt.figure(figsize=(12, 8))
        hours = sorted(hour_counts.keys())
        text_counts = [hour_counts[h] - non_text_messages_by_hour[h] for h in hours]
        non_text_counts = [non_text_messages_by_hour[h] for h in hours]
        
        x = np.arange(len(hours))
        width = 0.35
        
        plt.bar(x - width/2, text_counts, width, label='Текстовые сообщения')
        plt.bar(x + width/2, non_text_counts, width, label='Не текстовые сообщения')
        
        plt.title('Распределение сообщений по часам суток')
        plt.xlabel('Час')
        plt.ylabel('Количество сообщений')
        plt.xticks(x, hours)
        plt.legend()
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 3: Message length distribution
        if message_lengths:
            plt.figure(figsize=(12, 8))
            plt.hist(message_lengths, bins=50, label='Текстовые сообщения')
            plt.axvline(x=0, color='r', linestyle='--', label='Не текстовые сообщения')
            plt.title('Распределение длины сообщений')
            plt.xlabel('Длина сообщения')
            plt.ylabel('Количество сообщений')
            plt.legend()
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
            plt.close()

        # Plot 4: Top 10 most active participants
        plt.figure(figsize=(12, 8))
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        plt.bar([str(s[0]) for s in top_senders], [s[1] for s in top_senders])
        plt.title('Топ-10 самых активных участников')
        plt.xlabel('ID участника')
        plt.ylabel('Количество сообщений')
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 5: Word cloud
        if word_counts:
            plt.figure(figsize=(12, 8))
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Облако слов из сообщений (слова от {} букв)'.format(min_word_length))
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
            plt.close()

        # Plot 6: Emotional tone by day
        plt.figure(figsize=(12, 8))
        avg_sentiment = {day: np.mean(sentiments) for day, sentiments in day_sentiment.items()}
        dates = sorted(avg_sentiment.keys())
        sentiments = [avg_sentiment[date] for date in dates]
        plt.plot(dates, sentiments)
        plt.title('Эмоциональный окрас сообщений по дням')
        plt.xlabel('Дата')
        plt.ylabel('Средний эмоциональный тон')
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 7: Word length distribution
        plt.figure(figsize=(12, 8))
        word_length_data = sorted(word_lengths.items())
        grouped_lengths = defaultdict(int)
        for length, count in word_length_data:
            if length < 10:
                grouped_lengths['<10'] += count
            else:
                grouped_lengths[str(length)] += count
        
        sorted_groups = sorted(grouped_lengths.items(), 
                             key=lambda x: int(x[0]) if x[0] != '<10' else 0)
        
        total_words = sum(count for _, count in sorted_groups)
        percentages = [(count / total_words * 100) for _, count in sorted_groups]
        labels = [f'{length} букв' if length != '<10' else '<10 букв' 
                 for length, _ in sorted_groups]
        
        y_pos = np.arange(len(labels))
        bars = plt.barh(y_pos, percentages)
        
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height()/2,
                    f'{percentages[i]:.1f}%',
                    ha='left', va='center', fontsize=10)
        
        plt.yticks(y_pos, labels)
        plt.xlabel('Процент слов')
        plt.title('Распределение длины слов')
        plt.grid(True, axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 8: Message frequency by day of week
        plt.figure(figsize=(12, 8))
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        counts = [day_of_week_counts[day] for day in days]
        plt.bar(days, counts)
        plt.title('Активность по дням недели')
        plt.xlabel('День недели')
        plt.ylabel('Количество сообщений')
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 9: Average message length by sender
        plt.figure(figsize=(12, 8))
        avg_lengths = {sender: np.mean(lengths) for sender, lengths in sender_avg_lengths.items()}
        top_senders_length = sorted(avg_lengths.items(), key=lambda x: x[1], reverse=True)[:10]
        plt.bar([str(s[0]) for s in top_senders_length], [s[1] for s in top_senders_length])
        plt.title('Средняя длина сообщений по отправителям')
        plt.xlabel('ID участника')
        plt.ylabel('Средняя длина сообщения')
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

        # Plot 10: Message activity by time period
        plt.figure(figsize=(12, 8))
        time_periods = ['Morning', 'Afternoon', 'Evening', 'Night']
        counts = [time_period_counts[period] for period in time_periods]
        plt.pie(counts, labels=time_periods, autopct='%1.1f%%')
        plt.title('Активность по времени суток')
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

    except Exception as e:
        print(f"Error generating plots: {str(e)}")

    return plots