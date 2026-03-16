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
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import base64
from io import BytesIO
import emoji
import requests
import validators
from urllib.parse import urlparse
import re

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
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
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
    .url-input {
        border: 2px solid #075e54;
        border-radius: 10px;
        padding: 0.5rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
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
if 'url_processed' not in st.session_state:
    st.session_state.url_processed = False

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/whatsapp--v1.png", width=80)
    st.title("📱 Chat Analysis")
    st.markdown("---")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["📄 Upload File", "🔗 URL Link", "📦 Zip File"],
        help="Select how you want to provide the chat data"
    )
    
    uploaded_file = None
    uploaded_zip = None
    url_input = None
    
    if input_method == "📄 Upload File":
        uploaded_file = st.file_uploader(
            "Upload WhatsApp chat (.txt)", 
            type="txt",
            help="Export chat without media from WhatsApp (supports both 12-hour and 24-hour formats)"
        )
    elif input_method == "🔗 URL Link":
        st.markdown("### Enter URL")
        st.markdown("Paste a direct link to a WhatsApp chat text file")
        url_input = st.text_input(
            "URL:",
            placeholder="https://example.com/chat.txt",
            help="Enter the direct URL to a WhatsApp chat export file"
        )
        
        # URL validation info
        st.markdown("""
        **Supported URL types:**
        - Direct links to .txt files
        - GitHub raw links
        - Google Drive links (must be publicly shared)
        - Any publicly accessible text file
        """)
        
    else:  # Zip File
        uploaded_zip = st.file_uploader(
            "Upload Zip file", 
            type="zip",
            help="Zip file containing multiple WhatsApp chat exports"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        max_words = st.slider("Max words in wordcloud", 50, 300, 150)
        show_media = st.checkbox("Include media messages in wordcloud", value=False)
        timeout = st.number_input("URL timeout (seconds)", min_value=5, max_value=60, value=30)

def extract_filename_from_url(url):
    """Extract filename from URL"""
    parsed = urlparse(url)
    path = parsed.path
    filename = os.path.basename(path)
    if not filename or '.' not in filename:
        filename = "downloaded_chat.txt"
    return filename

def download_from_url(url, timeout=30):
    """Download content from URL"""
    try:
        # Validate URL
        if not validators.url(url):
            return None, "Invalid URL format"
        
        # Send request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text' not in content_type and 'plain' not in content_type:
            # Try to decode anyway
            pass
        
        # Try to decode content
        try:
            content = response.content.decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            try:
                content = response.content.decode('latin-1')
            except:
                return None, "Could not decode file content. Please ensure it's a text file."
        
        return content, None
    except requests.exceptions.Timeout:
        return None, f"Request timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check the URL and try again."
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e.response.status_code} - {e.response.reason}"
    except Exception as e:
        return None, f"Error downloading file: {str(e)}"

def process_chat_file(file_content, filename="uploaded_chat.txt"):
    """Process a single chat file"""
    try:
        df = Chat_Analysis.preprocess(file_content)
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
                    with open(txt_file, 'r', encoding='utf-8') as f:
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

"""
    return export_text

# Main content
st.markdown('<h1 class="main-header">💬 WhatsApp Chat Analyzer Pro</h1>', unsafe_allow_html=True)

# Process based on input method
df = None
errors = None
source_info = ""

if input_method == "🔗 URL Link" and url_input:
    if st.sidebar.button("📥 Load from URL", use_container_width=True):
        with st.spinner("🔄 Downloading from URL..."):
            content, error = download_from_url(url_input, timeout=timeout)
            
            if error:
                st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
            else:
                # Preview the content
                with st.expander("📄 Preview downloaded content"):
                    preview_lines = content.split('\n')[:10]
                    preview = '\n'.join(preview_lines)
                    st.text(preview + ("\n..." if len(content.split('\n')) > 10 else ""))
                
                # Process the content
                filename = extract_filename_from_url(url_input)
                df, error = process_chat_file(content, filename)
                
                if error:
                    st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="success-box">✅ Successfully loaded chat from URL: {filename}</div>', unsafe_allow_html=True)
                    source_info = f"Source: {url_input}"
                    st.session_state.url_processed = True

elif uploaded_file:
    with st.spinner("🔄 Processing chat file..."):
        content = uploaded_file.getvalue().decode("utf-8")
        df, errors = process_chat_file(content, uploaded_file.name)
        if df is not None:
            source_info = f"File: {uploaded_file.name}"

elif uploaded_zip:
    with st.spinner("🔄 Processing zip file (this may take a moment)..."):
        df, errors = process_zip_file(uploaded_zip)
        if df is not None:
            source_info = f"Zip file: {uploaded_zip.name}"

# Display errors if any
if errors:
    if isinstance(errors, list):
        for error in errors:
            st.markdown(f'<div class="error-box">⚠️ {error}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-box">⚠️ {errors}</div>', unsafe_allow_html=True)

# Main analysis section
if df is not None and not df.empty:
    st.session_state.df = df
    st.session_state.analysis_done = True
    
    # Show source info
    if source_info:
        st.info(f"📁 {source_info}")
    
    # Display basic info about the chat
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Messages", f"{len(df):,}")
    with col2:
        st.metric("Date Range", f"{df['only_date'].min()} to {df['only_date'].max()}")
    with col3:
        unique_users = len(df[df['user'] != 'group_notification']['user'].unique())
        st.metric("Active Users", unique_users)
    
    # Get unique users
    users = df["user"].unique().tolist()
    if "group_notification" in users:
        users.remove("group_notification")
    
    users.sort()
    users.insert(0, "Overall")
    
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
        
        progress_bar.progress(30)
        
        # Timeline Analysis
        st.markdown("## 📈 Timeline Analysis")
        tab1, tab2, tab3 = st.tabs(["📅 Monthly Timeline", "📆 Daily Timeline", "⏰ Hourly Activity"])
        
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
                
                # Show top 3 active hours
                st.write("**Top 3 Most Active Hours:**")
                top_hours = hourly_activity.nlargest(3, 'message_count')[['hour', 'message_count']]
                for idx, row in top_hours.iterrows():
                    hour = int(row['hour'])
                    st.write(f"• {hour:02d}:00 - {hour:02d}:59 ({'AM' if hour < 12 else 'PM'}): {int(row['message_count']):,} messages")
        
        progress_bar.progress(50)
        
        # Activity Heatmap
        st.markdown("## 🔥 Activity Heatmap")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        if user_heatmap is not None and not user_heatmap.empty:
            fig, ax = plt.subplots(figsize=(14, 6))
            sns.heatmap(user_heatmap, cmap='YlOrRd', annot=True, fmt='g', ax=ax, 
                       cbar_kws={'label': 'Message Count'}, linewidths=0.5)
            plt.title('Weekly Activity Pattern', fontsize=16, fontweight='bold', pad=20)
            plt.ylabel('Day of Week', fontsize=12)
            plt.xlabel('Time Period', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            st.pyplot(fig)
            plt.close()
        
        progress_bar.progress(70)
        
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
        
        progress_bar.progress(85)
        
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
                           title='Top 15 Common Words',
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
        
        progress_bar.progress(95)
        
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
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis Complete!")
        progress_bar.empty()
        status_text.empty()
        
        # Add download section
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
        
        ### Features:
        - 📊 **Comprehensive Statistics** - Message counts, word counts, media sharing
        - 📈 **Interactive Timelines** - Monthly, daily, and hourly activity patterns
        - 🔥 **Activity Heatmaps** - Visualize when chats are most active
        - 👥 **User Analysis** - Compare participant activity
        - ☁️ **Word Clouds** - See frequently used words
        - 😊 **Emoji Analysis** - Track emoji usage
        - 🔗 **URL Support** - Analyze chats directly from URLs
        - 📥 **Export Results** - Download reports and processed data
        
        ### Input Methods:
        - ✅ **Upload File** - Upload local .txt file
        - ✅ **URL Link** - Paste direct link to chat file
        - ✅ **Zip File** - Upload multiple chats in zip
        
        ### Time Format Support:
        - ✅ **12-hour format** (e.g., 13/03/22, 8:30 PM)
        - ✅ **24-hour format** (e.g., 13/03/22, 20:30)
        
        ### Getting Started:
        1. Export your WhatsApp chat (without media)
        2. Choose input method from sidebar
        3. Upload file, paste URL, or upload zip
        4. Select user and click "Analyze"
        """)
        
        with st.expander("📖 Detailed Instructions"):
            st.markdown("""
            ### Step-by-Step Guide
            
            **Method 1: Upload File**
            1. Export chat from WhatsApp
            2. Click "Browse files" and select the .txt file
            3. Click "Analyze" to start
            
            **Method 2: URL Link**
            1. Upload your chat file to a cloud service
            2. Get a direct download link
            3. Paste the URL and click "Load from URL"
            4. Click "Analyze" to start
            
            **Method 3: Zip File**
            1. Collect multiple chat exports
            2. Compress them into a zip file
            3. Upload the zip file
            4. All chats will be combined for analysis
            
            **Supported URL types:**
            - Direct file links
            - GitHub raw content
            - Google Drive (must be publicly shared)
            - Any publicly accessible text file
            """)
