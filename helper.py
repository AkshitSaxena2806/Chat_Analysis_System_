from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re
import numpy as np

extractor = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    num_messages = df.shape[0]
    
    words = []
    for message in df['message']:
        words.extend(message.split())
    
    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]
    
    links = []
    for message in df['message']:
        links.extend(extractor.find_urls(message))
    
    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head(10)
    new_df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'count': 'name', 'user': 'percent'})
    new_df.columns = ['User', 'Percentage']
    return x, new_df

def workcloud(selected_user, df, max_words=200):
    try:
        with open('stop_hinglish.txt', 'r') as f:
            stop_words = f.read().split()
    except FileNotFoundError:
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                     'before', 'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
                     'should', 'may', 'might', 'must', 'can', 'could', 'i', 'you', 'he',
                     'she', 'it', 'we', 'they', 'them', 'their', 'your', 'my', 'his',
                     'her', 'its', 'this', 'that', 'these', 'those']
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']
    
    def remove_stop_words(message):
        return " ".join([word for word in message.lower().split() if word not in stop_words])
    
    temp['message'] = temp['message'].apply(remove_stop_words)
    
    wc = WordConfig(
        width=800, 
        height=400, 
        max_words=max_words,
        min_font_size=10,
        background_color='white',
        colormap='viridis',
        random_state=42
    )
    
    text = " ".join(temp['message'].astype(str))
    if text.strip():
        return wc.generate(text)
    return None

def most_common_words(selected_user, df):
    try:
        with open('stop_hinglish.txt', 'r') as f:
            stop_words = f.read().split()
    except FileNotFoundError:
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through']
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']
    
    words = []
    for message in temp['message']:
        words.extend([word for word in message.lower().split() if word not in stop_words])
    
    return pd.DataFrame(Counter(words).most_common(30))

def emojies(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
    
    return pd.DataFrame(Counter(emojis).most_common(20))

def monthly_timelines(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()
    timeline = timeline.sort_values(['year', 'month_num'])
    
    timeline['time'] = timeline['month'] + " " + timeline['year'].astype(str)
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    return df.groupby('only_date').count()['message'].reset_index().sort_values('only_date')

def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    if 'period' not in df.columns:
        return pd.DataFrame()
    
    # Ensure day_name is categorical with correct order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_name'] = pd.Categorical(df['day_name'], categories=day_order, ordered=True)
    
    pivot_table = df.pivot_table(
        index='day_name', 
        columns='period', 
        values='message', 
        aggfunc='count',
        fill_value=0
    )
    
    # Reorder periods logically
    period_order = ['Late Night', 'Early Morning', 'Morning', 'Afternoon', 'Evening', 'Night']
    pivot_table = pivot_table.reindex(columns=[p for p in period_order if p in pivot_table.columns])
    
    return pivot_table
