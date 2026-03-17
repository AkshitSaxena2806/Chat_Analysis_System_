from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re

extractor = URLExtract()

# Common stop words (English + basic Hindi)
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
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = len(df)

    words = []
    for msg in df['message']:
        words.extend([w for w in str(msg).split() if w.strip()])

    num_media = df[df['message'].str.contains('<Media omitted>', na=False, regex=False)].shape[0]

    links = []
    for msg in df['message']:
        links.extend(extractor.find_urls(str(msg)))

    return num_messages, len(words), num_media, len(links)

def most_busy_users(df):
    user_counts = df['user'].value_counts()
    user_counts = user_counts[~user_counts.index.isin(['System', 'group_notification'])]
    x = user_counts.head(10)
    new_df = round((user_counts / len(df)) * 100, 2).reset_index()
    new_df.columns = ['User', 'Percentage']
    return x, new_df

def workcloud(selected_user, df, max_words=150):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]

    if len(temp) == 0:
        return None

    def clean_text(text):
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        words = text.split()
        words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        return ' '.join(words)

    temp['clean'] = temp['message'].apply(clean_text)
    all_text = ' '.join(temp['clean'].astype(str))
    if not all_text.strip():
        return None

    wc = WordCloud(width=800, height=400, max_words=max_words,
                   background_color='white', colormap='viridis', random_state=42)
    return wc.generate(all_text)

def most_common_words(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]

    words = []
    for msg in temp['message']:
        text = str(msg).lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        text = re.sub(r'[^\w\s]', ' ', text)
        for w in text.split():
            if w not in STOP_WORDS and len(w) > 2:
                words.append(w)

    common = Counter(words).most_common(20)
    return pd.DataFrame(common, columns=['Word', 'Frequency'])

def emojies(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for msg in df['message']:
        emojis.extend([c for c in str(msg) if c in emoji.EMOJI_DATA])

    counts = Counter(emojis).most_common(15)
    return pd.DataFrame(counts, columns=['Emoji', 'Count'])

def monthly_timelines(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    tl = df.groupby(['year', 'month_num', 'month']).size().reset_index(name='message')
    tl = tl.sort_values(['year', 'month_num'])
    tl['time'] = tl['month'] + " " + tl['year'].astype(str)
    return tl

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    return df.groupby('only_date').size().reset_index(name='message').sort_values('only_date')

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

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_name'] = pd.Categorical(df['day_name'], categories=day_order, ordered=True)

    pivot = df.pivot_table(index='day_name', columns='period', values='message',
                           aggfunc='count', fill_value=0, observed=False)
    return pivot
