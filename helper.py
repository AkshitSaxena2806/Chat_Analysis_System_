import re
from collections import Counter

import emoji
import numpy as np
import pandas as pd
from urlextract import URLExtract

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except Exception:
    WordCloud = None
    WORDCLOUD_AVAILABLE = False

try:
    import language_tool_python
    LANG_TOOL_AVAILABLE = True
except ImportError:
    LANG_TOOL_AVAILABLE = False

# Initialize globally to None so we do it lazily
lang_tool = None

extractor = URLExtract()

# Common stop words (English + basic Hindi) - loaded from file
def load_stop_words():
    """Load stop words from file or use default list"""
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            return set([word.strip().lower() for word in f.readlines() if word.strip()])
    except:
        # Default stop words if file not found
        return {
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
            'jaisa', 'aisa', 'waisa', 'maam', "ma'am", 'sir', 'miss', 'mrs', 'mr',
            'hi', 'hello', 'hey', 'ok', 'okay', 'thanks', 'thank', 'please'
        }

STOP_WORDS = load_stop_words()

def fetch_stats(selected_user, df):
    """Fetch basic statistics"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = len(df)

    # Count words
    words = []
    for msg in df['message']:
        msg = str(msg)
        if msg != '<Media omitted>' and not msg.startswith('http'):
            words.extend([w for w in msg.split() if w.strip()])

    # Count media messages
    num_media = df[df['message'].str.contains('<Media omitted>', na=False, regex=False)].shape[0]

    # Count links
    links = []
    for msg in df['message']:
        links.extend(extractor.find_urls(str(msg)))

    return num_messages, len(words), num_media, len(links)

def most_busy_users(df):
    """Get most active users"""
    user_counts = df['user'].value_counts()
    # Filter out system messages if any remain
    user_counts = user_counts[~user_counts.index.isin(['System', 'group_notification'])]
    x = user_counts.head(10)
    
    # Calculate percentages
    total_messages = len(df)
    if total_messages > 0:
        new_df = round((user_counts / total_messages) * 100, 2).reset_index()
        new_df.columns = ['User', 'Percentage']
    else:
        new_df = pd.DataFrame(columns=['User', 'Percentage'])
    
    return x, new_df

def workcloud(selected_user, df, max_words=150):
    """Generate word cloud (returns None if unavailable)."""
    if not WORDCLOUD_AVAILABLE:
        return None

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Filter out system messages and media omitted
    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]
    
    # Filter out messages that are just links or empty
    temp = temp[temp['message'].str.len() > 0]

    if len(temp) == 0:
        return None

    def clean_text(text):
        text = str(text).lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove emojis
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        # Split and filter words
        words = text.split()
        words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        return ' '.join(words)

    # Apply cleaning
    clean_messages = temp['message'].apply(clean_text)
    all_text = ' '.join(clean_messages.astype(str))
    
    if not all_text.strip():
        return None

    wc = WordCloud(
        width=800,
        height=400,
        max_words=max_words,
        background_color='white',
        colormap='viridis',
        random_state=42,
        collocations=False,
    )
    return wc.generate(all_text)

def most_common_words(selected_user, df):
    """Get most common words"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Filter out system messages and media omitted
    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)]
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]

    words = []
    for msg in temp['message']:
        text = str(msg).lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove emojis
        text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split and filter
        for w in text.split():
            if w not in STOP_WORDS and len(w) > 2:
                words.append(w)

    common = Counter(words).most_common(20)
    return pd.DataFrame(common, columns=['Word', 'Frequency'])

def emojies(selected_user, df):
    """Extract and count emojis"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for msg in df['message']:
        emojis.extend([c for c in str(msg) if c in emoji.EMOJI_DATA])

    counts = Counter(emojis).most_common(15)
    return pd.DataFrame(counts, columns=['Emoji', 'Count'])

def monthly_timelines(selected_user, df):
    """Get monthly timeline data"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Ensure year and month_num exist
    if 'year' not in df.columns or 'month_num' not in df.columns:
        df = add_time_columns(df)

    tl = df.groupby(['year', 'month_num', 'month']).size().reset_index(name='message')
    tl = tl.sort_values(['year', 'month_num'])
    tl['time'] = tl['month'] + " " + tl['year'].astype(str)
    return tl

def daily_timeline(selected_user, df):
    """Get daily timeline data"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Ensure only_date exists
    if 'only_date' not in df.columns:
        df['only_date'] = df['date'].dt.date
        
    return df.groupby('only_date').size().reset_index(name='message').sort_values('only_date')

def week_activity_map(selected_user, df):
    """Get weekday activity"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Ensure day_name exists
    if 'day_name' not in df.columns:
        df['day_name'] = df['date'].dt.day_name()
        
    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    """Get month activity"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Ensure month exists
    if 'month' not in df.columns:
        df['month'] = df['date'].dt.month_name()
        
    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    """Generate activity heatmap data"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Ensure required columns exist
    if 'period' not in df.columns or 'day_name' not in df.columns:
        return pd.DataFrame()

    # Define day order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Filter valid days and convert to categorical
    df_valid = df[df['day_name'].isin(day_order)].copy()
    if len(df_valid) == 0:
        return pd.DataFrame()
    
    df_valid['day_name'] = pd.Categorical(df_valid['day_name'], categories=day_order, ordered=True)

    # Create pivot table
    try:
        pivot = df_valid.pivot_table(index='day_name', columns='period', values='message',
                                     aggfunc='count', fill_value=0, observed=False)
        return pivot
    except:
        return pd.DataFrame()

def add_time_columns(df):
    """Helper to add time columns if missing"""
    if 'year' not in df.columns:
        df["year"] = df["date"].dt.year
    if "month" not in df.columns:
        df["month"] = df["date"].dt.month_name()
    if "month_num" not in df.columns:
        df["month_num"] = df["date"].dt.month
    if "only_date" not in df.columns:
        df["only_date"] = df["date"].dt.date
    if "day_name" not in df.columns:
        df["day_name"] = df["date"].dt.day_name()
    if "hour" not in df.columns:
        df["hour"] = df["date"].dt.hour
    if "minute" not in df.columns:
        df["minute"] = df["date"].dt.minute
        
    def get_period(hour):
        if hour < 4:
            return 'Late Night (0-4)'
        elif hour < 8:
            return 'Early Morning (4-8)'
        elif hour < 12:
            return 'Morning (8-12)'
        elif hour < 16:
            return 'Afternoon (12-16)'
        elif hour < 20:
            return 'Evening (16-20)'
        else:
            return 'Night (20-24)'

    if "period" not in df.columns:
        df['period'] = df['hour'].apply(get_period)
    
    return df

def detect_linguistic_errors(selected_user, df):
    """
    Detects linguistic errors in messages using language_tool_python.
    Returns a DataFrame containing messages and their error metrics.
    """
    global lang_tool
    import streamlit as st
    
    if not LANG_TOOL_AVAILABLE:
        return pd.DataFrame()
        
    if lang_tool is None:
        try:
            with st.spinner("Downloading/Loading LanguageTool (~250MB)... This happens only once and may take a few minutes!"):
                lang_tool = language_tool_python.LanguageTool('en-US')
        except Exception as e:
            st.error(f"Failed to load LanguageTool. Ensure Java is installed. Error: {e}")
            return pd.DataFrame()

    if lang_tool is None:
        return pd.DataFrame()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Filter out system messages and media omitted
    temp = df[~df['user'].str.contains('System|group_notification', na=False, regex=True)].copy()
    temp = temp[~temp['message'].str.contains('<Media omitted>', na=False, regex=False)]
    
    results = []
    
    for idx, row in temp.iterrows():
        msg = str(row['message'])
        
        # skip if just URL, empty, or very short
        if not msg.strip() or msg.startswith('http') or len(msg.strip()) < 3:
            continue
            
        # remove emojis before checking to avoid offset issues
        clean_msg = ''.join([c for c in msg if c not in emoji.EMOJI_DATA])
        
        try:
            matches = lang_tool.check(clean_msg)
        except Exception:
            # Skip on tool failure
            continue
            
        if len(matches) > 0:
            grammar = typo = tense = agreement = other = 0
            
            # Highlight HTML
            html_msg = clean_msg
            offset_shift = 0
            
            # Sort matches by offset to apply HTML tags correctly
            sorted_matches = sorted(matches, key=lambda x: x.offset)
            
            for match in sorted_matches:
                # categorize
                cat = match.category.lower() if match.category else ""
                ruleId = match.ruleId.lower() if match.ruleId else ""
                
                if 'grammar' in cat:
                    if 'tense' in ruleId: tense += 1
                    elif 'agreement' in ruleId: agreement += 1
                    else: grammar += 1
                elif 'typo' in cat or 'misspelling' in cat or 'casing' in cat or 'typographical' in cat:
                    typo += 1
                else:
                    other += 1
                    
                # highlight logic
                start = match.offset + offset_shift
                end = start + match.errorLength
                
                # tooltip message
                tooltip = match.message.replace('"', '&quot;').replace("'", "&#39;")
                
                # We use a custom style for marking
                mark_html = f'<mark title="{tooltip}" style="background-color: #ffcccc; padding: 0 2px; border-radius: 3px; border-bottom: 2px solid red; cursor: help;">{html_msg[start:end]}</mark>'
                
                html_msg = html_msg[:start] + mark_html + html_msg[end:]
                offset_shift += len(mark_html) - match.errorLength
                
            results.append({
                'Date': row['date'],
                'User': row['user'],
                'Original Text': msg,
                'Total Errors': len(matches),
                'Grammar': grammar,
                'Typo': typo,
                'Tense': tense,
                'Agreement': agreement,
                'Other': other,
                'Highlighted Text': html_msg
            })
            
    return pd.DataFrame(results)
