from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re
import numpy as np

# Initialize URL extractor
extractor = URLExtract()

# Common stop words (including Hindi/English)
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
    'before', 'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
    'should', 'may', 'might', 'must', 'can', 'could', 'i', 'you', 'he',
    'she', 'it', 'we', 'they', 'them', 'their', 'your', 'my', 'his',
    'her', 'its', 'this', 'that', 'these', 'those', 'ka', 'ki', 'ke', 
    'ko', 'se', 'mein', 'par', 'aur', 'hai', 'hain', 'tha', 'the', 'thi',
    'raha', 'rahe', 'rahi', 'kar', 'karke', 'karna', 'hoga', 'hoge',
    'hogi', 'sakta', 'sakte', 'sakti', 'chahiye', 'apna', 'tum', 'aap',
    'main', 'hum', 'yeh', 'woh', 'kya', 'kyun', 'kaise', 'kahan', 'kab',
    'kitna', 'kitne', 'itna', 'utna', 'jab', 'tab', 'jahan', 'tahan',
    'jaisa', 'aisa', 'waisa', 'maam', 'ma\'am', 'sir', 'miss', 'mrs', 'mr',
    'hi', 'hello', 'hey', 'ok', 'okay', 'thanks', 'thank', 'please'
}

def fetch_stats(selected_user, df):
    """Fetch basic statistics"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    num_messages = len(df)
    
    words = []
    for message in df['message']:
        words.extend([word for word in str(message).split() if word.strip()])
    
    num_media_messages = df[df['message'].str.contains('<Media omitted>', na=False, regex=False)].shape[0]
    
    links = []
    for message in df['message']:
        links.extend(extractor.find_urls(str(message)))
    
    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    """Get most active users"""
    user_counts = df['user'].value_counts()
    # Filter out system messages
    user_counts = user_counts[~user_counts.index.isin(['System', 'group_notification'])]
    
    x = user_counts.head(10)
    new_df = round((user_counts / len(df)) * 100, 2).reset_index()
    new_df.columns = ['User', 'Percentage']
    return x, new_df

def workcloud(selected_user, df, max_words=150):
    """Generate word cloud"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Filter out system messages and media
    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]
    
    if len(temp) == 0:
        return None
    
    # Clean text
    def clean_text(text):
        # Convert to string and lowercase
        text = str(text).lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove emojis
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        # Split into words
        words = text.split()
        # Filter words
        words = [word for word in words if word not in STOP_WORDS and len(word) > 2]
        return ' '.join(words)
    
    temp['clean_message'] = temp['message'].apply(clean_text)
    all_text = ' '.join(temp['clean_message'].astype(str))
    
    if not all_text.strip():
        return None
    
    wc = WordCloud(
        width=800,
        height=400,
        max_words=max_words,
        background_color='white',
        colormap='viridis',
        random_state=42
    )
    
    return wc.generate(all_text)

def most_common_words(selected_user, df):
    """Get most common words"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]
    
    words = []
    for message in temp['message']:
        # Convert to string and lowercase
        text = str(message).lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove emojis
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split into words
        message_words = text.split()
        # Filter words
        filtered_words = [word for word in message_words 
                         if word not in STOP_WORDS and len(word) > 2]
        words.extend(filtered_words)
    
    common_words = Counter(words).most_common(20)
    return pd.DataFrame(common_words, columns=['Word', 'Frequency'])

def emojies(selected_user, df):
    """Extract emoji statistics"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    emojis = []
    for message in df['message']:
        emojis.extend([c for c in str(message) if c in emoji.EMOJI_DATA])
    
    emoji_counts = Counter(emojis).most_common(15)
    return pd.DataFrame(emoji_counts, columns=['Emoji', 'Count'])

def monthly_timelines(selected_user, df):
    """Get monthly timeline"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    timeline = df.groupby(['year', 'month_num', 'month']).size().reset_index(name='message')
    timeline = timeline.sort_values(['year', 'month_num'])
    timeline['time'] = timeline['month'] + " " + timeline['year'].astype(str)
    return timeline

def daily_timeline(selected_user, df):
    """Get daily timeline"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    return df.groupby('only_date').size().reset_index(name='message').sort_values('only_date')

def week_activity_map(selected_user, df):
    """Get weekday activity"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    """Get monthly activity"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    """Create activity heatmap data"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    if 'period' not in df.columns:
        return pd.DataFrame()
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_name'] = pd.Categorical(df['day_name'], categories=day_order, ordered=True)
    
    pivot_table = df.pivot_table(
        index='day_name',
        columns='period',
        values='message',
        aggfunc='count',
        fill_value=0,
        observed=False
    )
    
    return pivot_table
