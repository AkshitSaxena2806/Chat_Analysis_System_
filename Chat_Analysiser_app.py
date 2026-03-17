import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import Chat_Analysis
import helper
import zipfile
import os
from pathlib import Path
import tempfile
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import base64
from io import BytesIO
import emoji
from collections import Counter
import calendar

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer Pro", 
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #075e54;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px #cccccc;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .feature-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #075e54;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .metric-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .insight-badge {
        background-color: #075e54;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = "Overall"
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/whatsapp--v1.png", width=80)
    st.title("📱 Chat Analysis")
    st.markdown("---")
    
    # Upload options
    upload_option = st.radio(
        "Choose upload type:",
        ["📄 Single Text File", "📦 Zip File", "🔗 Sample Data"],
        help="Upload a single WhatsApp chat export or multiple chats in a zip file"
    )
    
    uploaded_file = None
    uploaded_zip = None
    
    if upload_option == "📄 Single Text File":
        uploaded_file = st.file_uploader(
            "Upload WhatsApp chat (.txt)", 
            type="txt",
            help="Export chat without media from WhatsApp (supports both 12-hour and 24-hour formats)"
        )
    elif upload_option == "📦 Zip File":
        uploaded_zip = st.file_uploader(
            "Upload Zip file", 
            type="zip",
            help="Zip file containing multiple WhatsApp chat exports"
        )
    else:
        # Sample data option
        st.info("📊 Using sample data for demonstration")
        use_sample = st.button("Load Sample Data")
        if use_sample:
            # Create sample data
            sample_data = """14/07/25, 12:30 - Messages and calls are end-to-end encrypted.
18/07/25, 11:33 - Shweta: Good morning everyone! Today's class is in EEE department.
18/07/25, 11:34 - Shweta: Machine lab at 11:45 AM
21/07/25, 11:17 - Shweta: <Media omitted>
21/07/25, 15:28 - Shweta: Assignment 1 is uploaded on GNUMS. Complete it by Friday.
24/07/25, 12:04 - You changed the group name from "Sem- lll UHV ME" to "UHV ME"
28/07/25, 10:36 - Shweta: How many of you are present today?
28/07/25, 10:37 - Shweta: Come to eee machine lab
31/07/25, 11:52 - Shweta: Where are you all?
31/07/25, 11:54 - Shweta: Come immediately
31/07/25, 11:55 - +91 96912 69907: Ma'am we are here
02/08/25, 09:27 - Sneha Ma'am MU: Good morning students
02/08/25, 09:27 - Sneha Ma'am MU: Are you coming today?
11/08/25, 08:29 - Shweta: Good morning! How many present today?
18/08/25, 11:17 - Shweta: https://youtu.be/ILDy6kYU-xQ?si=PCsReKIkty7o62M0
26/08/25, 15:44 - Shweta: Share the brochure with your friends
16/03/26, 21:34 - Shweta: POLL: Do you use AI like Chatgpt? OPTION: Yes (6 votes) OPTION: No (2 votes)"""
            
            # Create a temporary file-like object
            from io import BytesIO
            uploaded_file = BytesIO(sample_data.encode('utf-8'))
            uploaded_file.name = "sample_chat.txt"
            st.success("Sample data loaded! Click 'Analyze' to continue.")
    
    # Advanced options in expander
    with st.expander("⚙️ Advanced Options", expanded=False):
        max_words = st.slider("Max words in wordcloud", 50, 300, 150)
        min_word_length = st.slider("Minimum word length", 2, 5, 3)
        show_media = st.checkbox("Include media messages in analysis", value=False)
        show_system = st.checkbox("Include system messages", value=False)
        date_range = st.checkbox("Filter by date range", value=False)
    
    # Theme selector
    theme = st.radio("🎨 Theme", ["Light", "Dark"], index=0)
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.rerun()

def process_chat_file(file_content, filename="uploaded_chat.txt"):
    """Process a single chat file"""
    try:
        data = file_content.decode("utf-8", errors="ignore")
        df = Chat_Analysis.preprocess(data)
        return df, None
    except Exception as e:
        return None, f"Error processing {filename}: {str(e)}"

def process_zip_file(zip_file):
    """Process all text files in a zip file"""
    dfs = []
    errors = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_file.getvalue())
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(tmpdir)
            txt_files = list(Path(tmpdir).rglob("*.txt"))
            
            if not txt_files:
                return None, ["No text files found in the zip archive"]
            
            for txt_file in txt_files:
                try:
                    with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                        data = f.read()
                    df = Chat_Analysis.preprocess(data)
                    if not df.empty:
                        dfs.append(df)
                    else:
                        errors.append(f"{txt_file.name}: Empty or invalid format")
                except Exception as e:
                    errors.append(f"{txt_file.name}: {str(e)}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        return combined_df, errors
    else:
        return None, errors

def create_download_link(val, filename):
    """Create a download link for data"""
    b64 = base64.b64encode(val.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download {filename}</a>'

def export_analysis(df, selected_user):
    """Export analysis results to text"""
    num, words, media, links = helper.fetch_stats(selected_user, df)
    
    export_text = f"""WHATSAPP CHAT ANALYSIS REPORT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: {selected_user}

📊 BASIC STATISTICS
------------------
Total Messages: {num}
Total Words: {words}
Media Shared: {media}
Links Shared: {links}

📈 ACTIVITY SUMMARY
------------------
Most Active Day: {helper.week_activity_map(selected_user, df).idxmax() if not helper.week_activity_map(selected_user, df).empty else 'N/A'}
Most Active Month: {helper.month_activity_map(selected_user, df).idxmax() if not helper.month_activity_map(selected_user, df).empty else 'N/A'}

"""
    return export_text

def get_conversation_summary(df, selected_user):
    """Generate AI-like conversation summary"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    total_msgs = len(df)
    unique_days = df['only_date'].nunique()
    avg_per_day = total_msgs / unique_days if unique_days > 0 else 0
    
    # Get top users
    top_users = df['user'].value_counts().head(3)
    
    # Get common topics (simplified)
    all_text = ' '.join(df[~df['message'].str.contains('<Media omitted>')]['message'].astype(str))
    words = all_text.lower().split()
    word_freq = Counter(words).most_common(5)
    
    summary = f"""
    ### 📋 Conversation Summary
    
    - **Total Messages**: {total_msgs:,} messages over {unique_days} days
    - **Average Activity**: {avg_per_day:.1f} messages per day
    - **Most Active Users**: {', '.join([f"{user} ({count} msgs)" for user, count in top_users.items()])}
    - **Common Topics**: {', '.join([word for word, _ in word_freq if len(word) > 3][:5])}
    """
    return summary

# NEW FEATURE: Response Time Analysis
def analyze_response_times(df):
    """Analyze average response times between users"""
    df_sorted = df.sort_values('date')
    df_sorted['next_user'] = df_sorted['user'].shift(-1)
    df_sorted['time_diff'] = df_sorted['date'].shift(-1) - df_sorted['date']
    
    # Filter for reasonable response times (less than 1 hour)
    responses = df_sorted[
        (df_sorted['user'] != df_sorted['next_user']) & 
        (df_sorted['time_diff'] < pd.Timedelta(hours=1))
    ]
    
    if len(responses) > 0:
        avg_response = responses['time_diff'].mean()
        return avg_response
    return None

# NEW FEATURE: Message Length Analysis
def analyze_message_lengths(df, selected_user):
    """Analyze message length patterns"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    df['message_length'] = df['message'].str.len()
    df['word_count'] = df['message'].str.split().str.len()
    
    return df[['message_length', 'word_count']].describe()

# NEW FEATURE: Active Hours Heatmap (Hour vs Day)
def create_detailed_heatmap(df, selected_user):
    """Create hour vs day heatmap"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    # Create pivot table
    heatmap_data = df.pivot_table(
        index='day_name',
        columns='hour',
        values='message',
        aggfunc='count',
        fill_value=0
    )
    
    # Ensure all hours are present
    for hour in range(24):
        if hour not in heatmap_data.columns:
            heatmap_data[hour] = 0
    
    heatmap_data = heatmap_data[sorted(heatmap_data.columns)]
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)
    
    return heatmap_data

# NEW FEATURE: Conversation Starter Analysis
def analyze_conversation_starters(df):
    """Identify who starts conversations most often"""
    df = df.sort_values('date')
    df['new_conversation'] = (
        (df['user'] != df['user'].shift(1)) & 
        (df['date'] - df['date'].shift(1) > pd.Timedelta(hours=12))
    )
    
    starters = df[df['new_conversation']]['user'].value_counts()
    return starters

# NEW FEATURE: Sentiment Analysis (Simplified)
def simple_sentiment_analysis(df, selected_user):
    """Simple sentiment analysis based on keywords"""
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    
    positive_words = ['good', 'great', 'awesome', 'excellent', 'happy', 'thanks', 'thank', 'perfect', 'love', 'best']
    negative_words = ['bad', 'worst', 'terrible', 'awful', 'sad', 'sorry', 'problem', 'issue', 'difficult', 'hate']
    
    sentiments = []
    for msg in df['message']:
        msg_lower = msg.lower()
        pos_count = sum(1 for word in positive_words if word in msg_lower)
        neg_count = sum(1 for word in negative_words if word in msg_lower)
        
        if pos_count > neg_count:
            sentiments.append('Positive')
        elif neg_count > pos_count:
            sentiments.append('Negative')
        else:
            sentiments.append('Neutral')
    
    df['sentiment'] = sentiments
    return df['sentiment'].value_counts()

# Main content
st.markdown('<h1 class="main-header">💬 WhatsApp Chat Analyzer Pro</h1>', unsafe_allow_html=True)

# Process uploaded file
if uploaded_file or uploaded_zip:
    df = None
    errors = None
    
    if uploaded_file:
        with st.spinner("🔄 Processing chat file..."):
            df, errors = process_chat_file(uploaded_file.getvalue(), uploaded_file.name)
    elif uploaded_zip:
        with st.spinner("🔄 Processing zip file (this may take a moment)..."):
            df, errors = process_zip_file(uploaded_zip)
    
    if errors:
        if isinstance(errors, list):
            for error in errors:
                st.warning(f"⚠️ {error}")
        else:
            st.warning(f"⚠️ {errors}")
    
    if df is not None and not df.empty:
        st.session_state.df = df
        st.session_state.analysis_done = True
        
        # Get unique users
        users = df["user"].unique().tolist()
        if "group_notification" in users and not show_system:
            users.remove("group_notification")
        
        users.sort()
        users.insert(0, "Overall")
        
        # Date range filter
        if date_range and not df.empty:
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
            with col2:
                end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
            
            # Filter dataframe
            df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
        
        # User selection
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_user = st.selectbox(
                "👤 Select User for Analysis",
                users,
                index=0
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("🔍 Analyze", use_container_width=True)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📥 Export Report", use_container_width=True):
                report = export_analysis(df, selected_user)
                st.markdown(create_download_link(report, "chat_analysis_report.txt"), unsafe_allow_html=True)
        
        if analyze_btn:
            st.session_state.selected_user = selected_user
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Basic Statistics
            status_text.text("Calculating statistics...")
            progress_bar.progress(10)
            num, words, media, links = helper.fetch_stats(selected_user, df)
            
            # Display stats in beautiful cards
            st.markdown("## 📊 Overview Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{num:,}</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{words:,}</div>
                    <div class="stat-label">Total Words</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{media}</div>
                    <div class="stat-label">Media Shared</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{links}</div>
                    <div class="stat-label">Links Shared</div>
                </div>
                """, unsafe_allow_html=True)
            
            progress_bar.progress(20)
            
            # NEW: Conversation Summary
            st.markdown("## 📋 Conversation Summary")
            summary = get_conversation_summary(df, selected_user)
            st.markdown(summary)
            
            progress_bar.progress(25)
            
            # NEW: Sentiment Analysis
            st.markdown("## 😊 Sentiment Analysis")
            sentiment_counts = simple_sentiment_analysis(df, selected_user)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(sentiment_counts.reset_index().rename(columns={'index': 'Sentiment', 'sentiment': 'Count'}))
            with col2:
                fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                            title='Message Sentiment Distribution',
                            color_discrete_map={'Positive': '#4CAF50', 'Neutral': '#FFC107', 'Negative': '#F44336'})
                st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(30)
            
            # Timeline Analysis
            st.markdown("## 📈 Timeline Analysis")
            tab1, tab2, tab3, tab4 = st.tabs(["📅 Monthly", "📆 Daily", "⏰ Hourly", "🔥 Detailed Heatmap"])
            
            with tab1:
                mt = helper.monthly_timelines(selected_user, df)
                if mt is not None and not mt.empty:
                    fig = px.line(mt, x='time', y='message', 
                                 title='Message Activity Over Time',
                                 labels={'time': 'Month-Year', 'message': 'Number of Messages'})
                    fig.update_traces(line_color='#075e54', line_width=3)
                    fig.update_layout(
                        showlegend=False,
                        xaxis_tickangle=-45,
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                daily_timeline = helper.daily_timeline(selected_user, df)
                if daily_timeline is not None and not daily_timeline.empty:
                    fig = px.bar(daily_timeline, x='only_date', y='message',
                                title='Daily Message Count',
                                labels={'only_date': 'Date', 'message': 'Messages'})
                    fig.update_traces(marker_color='#25D366')
                    fig.update_layout(
                        xaxis_tickangle=-45,
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("⏰ Hourly Activity Pattern (24-Hour Format)")
                if 'hour' in df.columns:
                    hourly_activity = df.groupby('hour').count()['message'].reset_index()
                    hourly_activity.columns = ['hour', 'message_count']
                    
                    # Create a complete hour range (0-23)
                    all_hours = pd.DataFrame({'hour': range(24)})
                    hourly_activity = pd.merge(all_hours, hourly_activity, on='hour', how='left').fillna(0)
                    
                    # Convert hour to string for better display
                    hourly_activity['hour_label'] = hourly_activity['hour'].apply(lambda x: f"{int(x):02d}:00")
                    
                    fig = px.bar(hourly_activity, x='hour_label', y='message_count',
                                title='Messages by Hour of Day (24h format)',
                                labels={'hour_label': 'Hour of Day', 'message_count': 'Number of Messages'})
                    fig.update_traces(marker_color='#128C7E')
                    fig.update_xaxes(tickangle=45)
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Find peak hours
                    peak_hour = hourly_activity.loc[hourly_activity['message_count'].idxmax(), 'hour']
                    peak_count = hourly_activity['message_count'].max()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"📊 **Peak activity hour**: {int(peak_hour):02d}:00 ({'AM' if peak_hour < 12 else 'PM'})")
                    with col2:
                        st.info(f"📈 **Messages at peak hour**: {int(peak_count):,}")
            
            with tab4:
                st.subheader("🔥 Detailed Activity Heatmap (Hour vs Day)")
                detailed_heatmap = create_detailed_heatmap(df, selected_user)
                if not detailed_heatmap.empty:
                    fig, ax = plt.subplots(figsize=(16, 8))
                    sns.heatmap(detailed_heatmap, cmap='YlOrRd', annot=True, fmt='g', 
                               ax=ax, cbar_kws={'label': 'Message Count'}, linewidths=0.5)
                    plt.title('Message Activity: Hour of Day vs Day of Week', fontsize=16, fontweight='bold', pad=20)
                    plt.xlabel('Hour of Day (24h format)', fontsize=12)
                    plt.ylabel('Day of Week', fontsize=12)
                    st.pyplot(fig)
                    plt.close()
            
            progress_bar.progress(50)
            
            # Activity Heatmap (Original)
            st.markdown("## 🔥 Weekly Activity Pattern")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if user_heatmap is not None and not user_heatmap.empty:
                fig, ax = plt.subplots(figsize=(14, 6))
                sns.heatmap(user_heatmap, cmap='YlOrRd', annot=True, fmt='g', ax=ax, 
                           cbar_kws={'label': 'Message Count'}, linewidths=0.5)
                plt.title('Weekly Activity Pattern by Time Period', fontsize=16, fontweight='bold', pad=20)
                plt.ylabel('Day of Week', fontsize=12)
                plt.xlabel('Time Period', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.yticks(rotation=0)
                st.pyplot(fig)
                plt.close()
            
            progress_bar.progress(60)
            
            # User Activity Analysis
            if selected_user == 'Overall':
                st.markdown("## 👥 User Activity Analysis")
                col1, col2 = st.columns(2)
                
                x, new_df = helper.most_busy_users(df)
                
                with col1:
                    fig = px.pie(values=x.values, names=x.index, 
                                title='Message Distribution by User',
                                color_discrete_sequence=px.colors.qualitative.Set3)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("User Contribution Percentage")
                    st.dataframe(
                        new_df.style.highlight_max(axis=0, color='#90EE90'),
                        use_container_width=True,
                        height=400
                    )
                
                # NEW: Conversation Starters
                st.markdown("### 🗣️ Conversation Starters")
                starters = analyze_conversation_starters(df)
                if not starters.empty:
                    fig = px.bar(x=starters.values, y=starters.index, orientation='h',
                                title='Who Starts Conversations Most Often',
                                labels={'x': 'Number of Conversations Started', 'y': 'User'})
                    st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(70)
            
            # NEW: Message Length Analysis
            st.markdown("## 📏 Message Length Analysis")
            length_stats = analyze_message_lengths(df, selected_user)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Message Character Length")
                st.dataframe(length_stats[['message_length']].round(1))
            with col2:
                st.subheader("Word Count per Message")
                st.dataframe(length_stats[['word_count']].round(1))
            
            progress_bar.progress(75)
            
            # NEW: Response Time Analysis
            st.markdown("## ⏱️ Response Time Analysis")
            avg_response = analyze_response_times(df)
            if avg_response:
                minutes = avg_response.total_seconds() / 60
                st.info(f"⏱️ **Average response time**: {minutes:.1f} minutes")
                
                # Quick response rate
                quick_responses = df[
                    (df['user'] != df['user'].shift(-1)) & 
                    (df['date'].shift(-1) - df['date'] < pd.Timedelta(minutes=5))
                ].shape[0]
                
                st.info(f"⚡ **Quick responses (<5 min)**: {quick_responses} messages")
            else:
                st.info("Not enough data for response time analysis")
            
            progress_bar.progress(80)
            
            # Text Analysis
            st.markdown("## 📝 Text Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("☁️ Word Cloud")
                wc = helper.workcloud(selected_user, df, max_words=max_words)
                if wc is not None:
                    fig, ax = plt.subplots(figsize=(12, 8))
                    ax.imshow(wc)
                    ax.axis("off")
                    st.pyplot(fig)
                    plt.close()
            
            with col2:
                st.subheader("📊 Most Common Words")
                most_common_df = helper.most_common_words(selected_user, df)
                if most_common_df is not None and not most_common_df.empty:
                    fig = px.bar(most_common_df.head(15), x='Frequency', y='Word',
                               orientation='h',
                               title=f'Top 15 Common Words (min {min_word_length} chars)',
                               labels={'Word': 'Words', 'Frequency': 'Frequency'},
                               color='Frequency',
                               color_continuous_scale='viridis')
                    fig.update_layout(
                        yaxis={'categoryorder':'total ascending'},
                        height=500,
                        xaxis_title="Frequency",
                        yaxis_title=""
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(90)
            
            # Emoji Analysis
            st.markdown("## 😊 Emoji Analysis")
            col1, col2 = st.columns(2)
            
            emoji_df = helper.emojies(selected_user, df)
            
            with col1:
                if emoji_df is not None and not emoji_df.empty:
                    st.subheader("Emoji Usage Stats")
                    # Display emojis properly with HTML to ensure they render
                    emoji_display = emoji_df.copy()
                    emoji_display['Emoji with Name'] = emoji_display['Emoji'].apply(
                        lambda x: f"{x}  ({emoji.demojize(x).replace(':', '').replace('_', ' ')})"
                    )
                    display_df = emoji_display[['Emoji with Name', 'Count']].rename(
                        columns={'Emoji with Name': 'Emoji', 'Count': 'Count'}
                    )
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        height=400
                    )
            
            with col2:
                if emoji_df is not None and not emoji_df.empty:
                    st.subheader("Top Emojis")
                    top_emojis = emoji_df.head(8)
                    
                    # Create pie chart with emoji labels
                    fig = go.Figure(data=[go.Pie(
                        labels=top_emojis['Emoji'],
                        values=top_emojis['Count'],
                        texttemplate='%{label}<br>%{percent}',
                        textposition='inside',
                        hole=0.3
                    )])
                    fig.update_layout(
                        title='Top 8 Emojis Distribution',
                        height=400,
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(95)
            
            # NEW: Activity Insights
            st.markdown("## 💡 Key Insights")
            
            # Calculate various insights
            total_days = df['only_date'].nunique()
            msgs_per_day = num / total_days if total_days > 0 else 0
            media_percent = (media / num * 100) if num > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Messages per Day", f"{msgs_per_day:.1f}")
            with col2:
                st.metric("Media Percentage", f"{media_percent:.1f}%")
            with col3:
                st.metric("Unique Days Active", total_days)
            
            # Most active period
            if 'period' in df.columns:
                top_period = df['period'].value_counts().idxmax()
                st.info(f"🌟 **Most active time period**: {top_period}")
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis Complete!")
            progress_bar.empty()
            status_text.empty()
            
            # Download section
            st.markdown("## 📥 Download Results")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Download Analysis Report", use_container_width=True):
                    report = export_analysis(df, selected_user)
                    st.markdown(create_download_link(report, "chat_analysis_report.txt"), unsafe_allow_html=True)
            
            with col2:
                if st.button("📁 Download Processed Data (CSV)", use_container_width=True):
                    csv = df.to_csv(index=False)
                    st.markdown(create_download_link(csv, "processed_chat_data.csv"), unsafe_allow_html=True)

elif not st.session_state.analysis_done:
    # Welcome screen
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image("https://img.icons8.com/clouds/400/000000/whatsapp.png", width=300)
    
    with col2:
        st.markdown("""
        ## 🎉 Welcome to WhatsApp Chat Analyzer Pro!
        
        ### ✨ New Features Added:
        - 📋 **Conversation Summary** - Quick overview of chat activity
        - 😊 **Sentiment Analysis** - Positive/Neutral/Negative message classification
        - 🔥 **Detailed Heatmap** - Hour vs Day activity visualization
        - ⏱️ **Response Time Analysis** - Average response times between users
        - 📏 **Message Length Analysis** - Character and word count statistics
        - 🗣️ **Conversation Starters** - Who initiates conversations most often
        - 💡 **Key Insights** - Automated takeaways from your data
        
        ### Features:
        - 📊 **Comprehensive Statistics** - Message counts, word counts, media sharing
        - 📈 **Interactive Timelines** - Monthly, daily, and hourly activity patterns
        - 🔥 **Activity Heatmaps** - Visualize when chats are most active
        - 👥 **User Analysis** - Compare participant activity
        - ☁️ **Word Clouds** - See frequently used words
        - 😊 **Emoji Analysis** - Track emoji usage
        - 📥 **Export Results** - Download reports and processed data
        
        ### Time Format Support:
        - ✅ **12-hour format** (e.g., 13/03/22, 8:30 PM)
        - ✅ **24-hour format** (e.g., 13/03/22, 20:30)
        
        ### Getting Started:
        1. Upload your WhatsApp chat export
        2. Select a user or view overall analysis
        3. Click "Analyze" to see insights!
        """)
