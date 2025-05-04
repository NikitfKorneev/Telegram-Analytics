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
        non_text_messages_by_hour = defaultdict(int)  # New counter for non-text messages by hour

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

        # Create figure with 2 columns
        fig, axes = plt.subplots(5, 2, figsize=(20, 25))
        axes = axes.flatten()

        # Original plots (now in first column)
        # Plot 1: Activity by months and days
        sns.heatmap([month_day_counts[month] for month in sorted(month_day_counts.keys())], 
                   xticklabels=range(1, 32), 
                   yticklabels=sorted(month_day_counts.keys()), 
                   cmap='YlOrRd', 
                   ax=axes[0])
        axes[0].set_title('Активность по месяцам и дням')
        axes[0].set_xlabel('День месяца')
        axes[0].set_ylabel('Месяц')

        # Plot 2: Message distribution by hour
        hours = sorted(hour_counts.keys())
        text_counts = [hour_counts[h] - non_text_messages_by_hour[h] for h in hours]
        non_text_counts = [non_text_messages_by_hour[h] for h in hours]
        
        x = np.arange(len(hours))
        width = 0.35
        
        axes[1].bar(x - width/2, text_counts, width, label='Текстовые сообщения')
        axes[1].bar(x + width/2, non_text_counts, width, label='Не текстовые сообщения')
        
        axes[1].set_title('Распределение сообщений по часам суток')
        axes[1].set_xlabel('Час')
        axes[1].set_ylabel('Количество сообщений')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(hours)
        axes[1].legend()

        # Plot 3: Message length distribution
        if message_lengths:  # Only plot if we have text messages
            axes[2].hist(message_lengths, bins=50, label='Текстовые сообщения')
            axes[2].axvline(x=0, color='r', linestyle='--', label='Не текстовые сообщения')
            axes[2].set_title('Распределение длины сообщений')
            axes[2].set_xlabel('Длина сообщения')
            axes[2].set_ylabel('Количество сообщений')
            axes[2].legend()

        # Plot 4: Top 10 most active participants
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        axes[3].bar([str(s[0]) for s in top_senders], [s[1] for s in top_senders])
        axes[3].set_title('Топ-10 самых активных участников')
        axes[3].set_xlabel('ID участника')
        axes[3].set_ylabel('Количество сообщений')
        axes[3].tick_params(axis='x', rotation=45)

        # Plot 5: Word cloud
        if word_counts:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
            axes[4].imshow(wordcloud, interpolation='bilinear')
            axes[4].axis('off')
            axes[4].set_title('Облако слов из сообщений (слова от {} букв)'.format(min_word_length))

        # New plots (in second column)
        # Plot 6: Emotional tone by day
        avg_sentiment = {day: np.mean(sentiments) for day, sentiments in day_sentiment.items()}
        dates = sorted(avg_sentiment.keys())
        sentiments = [avg_sentiment[date] for date in dates]
        axes[5].plot(dates, sentiments)
        axes[5].set_title('Эмоциональный окрас сообщений по дням')
        axes[5].set_xlabel('Дата')
        axes[5].set_ylabel('Средний эмоциональный тон')
        axes[5].tick_params(axis='x', rotation=45)

        # Plot 7: Word length distribution (now horizontal bar chart)
        word_length_data = sorted(word_lengths.items())
        # Group words less than 10 letters
        grouped_lengths = defaultdict(int)
        for length, count in word_length_data:
            if length < 10:
                grouped_lengths['<10'] += count
            else:
                grouped_lengths[str(length)] += count
        
        # Sort the grouped data
        sorted_groups = sorted(grouped_lengths.items(), 
                             key=lambda x: int(x[0]) if x[0] != '<10' else 0)
        
        # Calculate percentages
        total_words = sum(count for _, count in sorted_groups)
        percentages = [(count / total_words * 100) for _, count in sorted_groups]
        labels = [f'{length} букв' if length != '<10' else '<10 букв' 
                 for length, _ in sorted_groups]
        
        # Create horizontal bar chart
        y_pos = np.arange(len(labels))
        bars = axes[6].barh(y_pos, percentages)
        
        # Add percentage labels at the end of each bar
        for i, bar in enumerate(bars):
            width = bar.get_width()
            axes[6].text(width + 1, bar.get_y() + bar.get_height()/2,
                        f'{percentages[i]:.1f}%',
                        ha='left', va='center', fontsize=10)
        
        # Customize the chart
        axes[6].set_yticks(y_pos)
        axes[6].set_yticklabels(labels)
        axes[6].set_xlabel('Процент слов')
        axes[6].set_title('Распределение длины слов')
        
        # Remove top and right spines
        axes[6].spines['top'].set_visible(False)
        axes[6].spines['right'].set_visible(False)
        
        # Add grid lines for better readability
        axes[6].grid(True, axis='x', linestyle='--', alpha=0.7)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Plot 8: Message frequency by day of week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        counts = [day_of_week_counts[day] for day in days]
        axes[7].bar(days, counts)
        axes[7].set_title('Активность по дням недели')
        axes[7].set_xlabel('День недели')
        axes[7].set_ylabel('Количество сообщений')
        axes[7].tick_params(axis='x', rotation=45)

        # Plot 9: Average message length by sender
        avg_lengths = {sender: np.mean(lengths) for sender, lengths in sender_avg_lengths.items()}
        top_senders_length = sorted(avg_lengths.items(), key=lambda x: x[1], reverse=True)[:10]
        axes[8].bar([str(s[0]) for s in top_senders_length], [s[1] for s in top_senders_length])
        axes[8].set_title('Средняя длина сообщений по отправителям')
        axes[8].set_xlabel('ID участника')
        axes[8].set_ylabel('Средняя длина сообщения')
        axes[8].tick_params(axis='x', rotation=45)

        # Plot 10: Message activity by time period
        time_periods = ['Morning', 'Afternoon', 'Evening', 'Night']
        counts = [time_period_counts[period] for period in time_periods]
        axes[9].pie(counts, labels=time_periods, autopct='%1.1f%%')
        axes[9].set_title('Активность по времени суток')

        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plots.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
        plt.close()

    except Exception as e:
        print(f"Error generating plots: {str(e)}")

    return plots