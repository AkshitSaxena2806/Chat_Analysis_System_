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
        # Split by spaces and filter out empty strings
        words.extend([word for word in message.split() if word.strip()])
    
    num_media_messages = df[df['message'].str.contains('<Media omitted>', na=False)].shape[0]
    
    links = []
    for message in df['message']:
        links.extend(extractor.find_urls(message))
    
    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head(10)
    new_df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index()
    new_df.columns = ['User', 'Percentage']
    return x, new_df

def workcloud(selected_user, df, max_words=200):
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = set(f.read().split())
    except FileNotFoundError:
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                     'before', 'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
                     'should', 'may', 'might', 'must', 'can', 'could', 'i', 'you', 'he',
                     'she', 'it', 'we', 'they', 'them', 'their', 'your', 'my', 'his',
                     'her', 'its', 'this', 'that', 'these', 'those', 'ka', 'ki', 'ke', 
                     'ko', 'se', 'mein', 'par', 'aur', 'hai', 'hain', 'tha', 'the', 'thi',
                     'thhe', 'thhi', 'raha', 'rahe', 'rahi', 'kar', 'karke', 'karna',
                     'hoga', 'hoge', 'hogi', 'sakta', 'sakte', 'sakti', 'chahiye',
                     'apna', 'tum', 'aap', 'main', 'hum', 'yeh', 'woh', 'kya', 'kyun',
                     'kaise', 'kahan', 'kab', 'kitna', 'kitne', 'itna', 'utna', 'jab',
                     'tab', 'jahan', 'tahan', 'jaisa', 'aisa', 'waisa'}
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Remove group notifications and media messages
    temp = df[~df['user'].str.contains('group_notification', na=False)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False)]
    
    # Remove emojis from text for wordcloud
    def remove_emojis_and_stopwords(text):
        # Remove emojis
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        # Convert to lowercase and split
        words = text.lower().split()
        # Remove stop words and short words (less than 3 characters)
        words = [word for word in words if word not in stop_words and len(word) > 2]
        return ' '.join(words)
    
    temp['clean_message'] = temp['message'].apply(remove_emojis_and_stopwords)
    
    wc = WordCloud(
        width=800, 
        height=400, 
        max_words=max_words,
        min_font_size=10,
        background_color='white',
        colormap='viridis',
        random_state=42,
        collocations=False  # Prevents grouping of words
    )
    
    text = " ".join(temp['clean_message'].astype(str))
    if text.strip():
        return wc.generate(text)
    return None

def most_common_words(selected_user, df):
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = set(f.read().split())
    except FileNotFoundError:
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'ka', 
                     'ki', 'ke', 'ko', 'se', 'mein', 'par', 'aur', 'hai', 'hain', 'tha', 
                     'the', 'thi', 'raha', 'rahe', 'rahi', 'kar', 'karke', 'karna'}
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Remove group notifications and media messages
    temp = df[~df['user'].str.contains('group_notification', na=False)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False)]
    
    words = []
    for message in temp['message']:
        # Remove emojis
        text = ''.join([c for c in message if c not in emoji.EMOJI_DATA])
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        # Split into words
        message_words = text.lower().split()
        # Filter words: min length 3, not in stop words
        filtered_words = [word for word in message_words 
                         if word not in stop_words and len(word) > 2]
        words.extend(filtered_words)
    
    # Get top 30 common words
    common_words = Counter(words).most_common(30)
    return pd.DataFrame(common_words, columns=['Word', 'Frequency'])

def emojies(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    emojis = []
    for message in df['message']:
        # Extract only emojis
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
    
    # Count emojis
    emoji_counts = Counter(emojis).most_common(20)
    return pd.DataFrame(emoji_counts, columns=['Emoji', 'Count'])

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
