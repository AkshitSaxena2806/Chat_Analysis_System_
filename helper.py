from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re

extractor = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Fetch number of messages
    num_messages = df.shape[0]
    
    # Fetch number of words
    words = []
    for message in df['message']:
        words.extend(message.split())
    
    # Fetch number of media messages
    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]
    
    # Fetch number of links
    links = []
    for message in df['message']:
        links.extend(extractor.find_urls(message))
    
    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head()
    new_df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'user': 'name', 'count': 'percent'})
    return x, new_df

def workcloud(selected_user, df):
    try:
        f = open('stop_hinglish.txt', 'r')
        stop_words = f.read()
        f.close()
    except FileNotFoundError:
        # Create default stop words if file doesn't exist
        stop_words = "the a an and or but in on at to for of with by from up about into through during before after is are was were be been being have has had do does did will would shall should may might must can could i you he she it we they them their your my his her its this that these those"
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']
    
    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)
    
    wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')
    temp['message'] = temp['message'].apply(remove_stop_words)
    df_wc = wc.generate(temp['message'].str.cat(sep=" "))
    return df_wc

def most_common_words(selected_user, df):
    try:
        f = open('stop_hinglish.txt', 'r')
        stop_words = f.read()
        f.close()
    except FileNotFoundError:
        stop_words = "the a an and or but in on at to for of with by from up about into through during before after is are was were be been being have has had do does did will would shall should may might must can could i you he she it we they them their your my his her its this that these those"
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']
    
    words = []
    for message in temp['message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)
    
    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df

def emojies(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
    
    emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))
    return emoji_df

def monthly_timelines(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()
    
    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))
    
    timeline['time'] = time
    return timeline

def day_timelines(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    timeline = df.groupby('day_name').count()['message'].reset_index()
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    daily_timeline = df.groupby('only_date').count()['message'].reset_index()
    return daily_timeline

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
    
    # Check if required columns exist
    if 'day_name' not in df.columns or 'period' not in df.columns:
        return pd.DataFrame()
    
    user_heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
    return user_heatmap
