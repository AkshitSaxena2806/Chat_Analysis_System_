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
from urllib.parse import urlparse, parse_qs
import re
import time
import logging

# Suppress warnings
logging.getLogger('katex').setLevel(logging.ERROR)
logging.getLogger('matplotlib').setLevel(logging.ERROR)

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
        margin: 0.5rem;
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
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #075e54;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #666;
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
if 'url_history' not in st.session_state:
    st.session_state.url_history = []
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = False

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/whatsapp--v1.png", width=80)
    st.title("📱 Chat Analysis")
    st.markdown("---")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["📄 Upload File", "🔗 URL Link", "📦 Zip File"],
        help="Select how you want to provide the chat data",
        key="input_method"
    )
    
    uploaded_file = None
    uploaded_zip = None
    url_input = None
    
    if input_method == "📄 Upload File":
        uploaded_file = st.file_uploader(
            "Upload WhatsApp chat (.txt)", 
            type="txt",
            help="Export chat without media from WhatsApp (supports both 12-hour and 24-hour formats)",
            key="file_uploader"
        )
        
    elif input_method == "🔗 URL Link":
        st.markdown("### 🔗 Enter Chat URL")
        st.markdown("Paste a direct link to a WhatsApp chat text file")
        
        # URL input with example
        url_input = st.text_input(
            "URL:",
            placeholder="https://example.com/chat.txt or https://drive.google.com/...",
            value=st.session_state.current_url,
            help="Enter the direct URL to a WhatsApp chat export file",
            key="url_input"
        )
        
        # URL type selector
        url_type = st.radio(
            "URL Type:",
            ["Auto Detect", "Direct Link", "Google Drive", "GitHub", "Pastebin"],
            help="Select the type of URL for better handling",
            key="url_type"
        )
        
        # Advanced URL options
        with st.expander("🔧 Advanced URL Options"):
            custom_filename = st.text_input(
                "Custom filename (optional):",
                placeholder="chat.txt",
                help="Specify a filename for the downloaded content",
                key="custom_filename"
            )
            timeout = st.number_input("Timeout (seconds)", min_value=5, max_value=120, value=30, key="timeout")
            verify_ssl = st.checkbox("Verify SSL", value=True, help="Disable for self-signed certificates", key="verify_ssl")
        
        # URL history
        if st.session_state.url_history:
            st.markdown("### 📜 Recent URLs")
            for i, url in enumerate(st.session_state.url_history[-5:]):
                if st.button(f"🔗 {url[:40]}...", key=f"history_{i}"):
                    st.session_state.current_url = url
                    st.rerun()
        
        # Load button
        load_url_btn = st.button("📥 Load from URL", use_container_width=True, type="primary", key="load_url")
        
    else:  # Zip File
        uploaded_zip = st.file_uploader(
            "Upload Zip file", 
            type="zip",
            help="Zip file containing multiple WhatsApp chat exports",
            key="zip_uploader"
        )
    
    # Advanced options
    with st.expander("⚙️ Analysis Options"):
        max_words = st.slider("Max words in wordcloud", 50, 300, 150, key="max_words")
        show_media = st.checkbox("Include media messages in analysis", value=False, key="show_media")
        min_word_length = st.slider("Minimum word length", 2, 5, 3, key="min_word_length")

# URL Handling Functions
def extract_filename_from_url(url, custom_name=None):
    """Extract filename from URL or use custom name"""
    if custom_name and custom_name.strip():
        return custom_name.strip()
    
    parsed = urlparse(url)
    path = parsed.path
    filename = os.path.basename(path)
    
    # Handle Google Drive links
    if 'drive.google.com' in url:
        if 'file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return f"google_drive_{file_id[:8]}.txt"
        elif 'id=' in url:
            file_id = parse_qs(parsed.query).get('id', ['unknown'])[0]
            return f"google_drive_{file_id[:8]}.txt"
    
    # Handle Pastebin
    if 'pastebin.com' in url:
        if 'raw' not in url:
            paste_id = path.split('/')[-1]
            return f"pastebin_{paste_id}.txt"
    
    # Handle GitHub
    if 'github.com' in url:
        if 'blob' in path:
            filename = path.split('/')[-1]
        return filename or "github_chat.txt"
    
    if not filename or '.' not in filename:
        filename = "downloaded_chat.txt"
    
    return filename

def convert_to_direct_link(url, url_type):
    """Convert various URL types to direct download links"""
    if url_type == "Auto Detect":
        if 'drive.google.com' in url:
            url_type = "Google Drive"
        elif 'github.com' in url:
            url_type = "GitHub"
        elif 'pastebin.com' in url:
            url_type = "Pastebin"
        else:
            url_type = "Direct Link"
    
    parsed = urlparse(url)
    
    if url_type == "Google Drive" or 'drive.google.com' in url:
        # Extract file ID from Google Drive URL
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        elif 'id=' in url:
            file_id = parse_qs(parsed.query).get('id', [None])[0]
            if file_id:
                return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    elif url_type == "GitHub" or 'github.com' in url:
        # Convert GitHub blob to raw
        if 'blob' in url:
            return url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
    
    elif url_type == "Pastebin" or 'pastebin.com' in url:
        # Convert to raw Pastebin
        if 'raw' not in url:
            paste_id = url.split('/')[-1]
            return f"https://pastebin.com/raw/{paste_id}"
    
    return url

def download_from_url(url, timeout=30, verify_ssl=True, url_type="Auto Detect"):
    """Download content from URL with support for various platforms"""
    try:
        # Validate URL
        if not validators.url(url):
            return None, "Invalid URL format"
        
        # Convert to direct link if needed
        direct_url = convert_to_direct_link(url, url_type)
        
        # Custom headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/plain, text/html, application/octet-stream, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        
        # Send request
        with st.spinner("Downloading file..."):
            response = requests.get(
                direct_url, 
                headers=headers, 
                timeout=timeout, 
                verify=verify_ssl,
                allow_redirects=True,
                stream=True
            )
            response.raise_for_status()
        
        # Try to decode content with multiple encodings
        content = None
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                content = response.content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return None, "Could not decode file content with any common encoding"
        
        return content, None
        
    except requests.exceptions.Timeout:
        return None, f"Request timed out after {timeout} seconds"
    except requests.exceptions.SSLError:
        return None, "SSL Error. Try disabling SSL verification in Advanced Options."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check the URL and try again."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None, "File not found (404). Please check the URL."
        elif e.response.status_code == 403:
            return None, "Access forbidden (403). The file might be private."
        else:
            return None, f"HTTP error: {e.response.status_code}"
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
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}" target="_blank">📥 Download {filename}</a>'

def export_analysis(df, selected_user):
    """Export analysis results to text"""
    num, words, media, links = helper.fetch_stats(selected_user, df)
    
    export_text = f"""WHATSAPP CHAT ANALYSIS REPORT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: {selected_user}

📊 BASIC STATISTICS
------------------
Total Messages: {num:,}
Total Words: {words:,}
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

# Handle file upload
if input_method == "📄 Upload File" and uploaded_file is not None:
    with st.spinner("🔄 Processing chat file..."):
        content = uploaded_file.getvalue().decode("utf-8")
        df, errors = process_chat_file(content, uploaded_file.name)
        if df is not None:
            source_info = f"File: {uploaded_file.name}"
            st.session_state.df = df
            st.session_state.analysis_done = True
            st.markdown(f'<div class="success-box">✅ Successfully loaded: {uploaded_file.name}</div>', unsafe_allow_html=True)

# Handle URL loading
elif input_method == "🔗 URL Link" and url_input and 'load_url_btn' in locals() and load_url_btn:
    with st.spinner("🔄 Processing URL..."):
        # Add to history
        if url_input not in st.session_state.url_history:
            st.session_state.url_history.append(url_input)
        
        # Download from URL
        content, error = download_from_url(
            url_input, 
            timeout=timeout if 'timeout' in locals() else 30, 
            verify_ssl=verify_ssl if 'verify_ssl' in locals() else True,
            url_type=url_type if 'url_type' in locals() else "Auto Detect"
        )
        
        if error:
            st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
        else:
            # Show preview
            with st.expander("📄 Preview downloaded content", expanded=False):
                lines = content.split('\n')
                preview_lines = lines[:10]
                preview = '\n'.join(preview_lines)
                st.text(f"First 10 lines of {len(lines)} total lines:")
                st.code(preview, language='text')
            
            # Process the content
            filename = extract_filename_from_url(url_input, custom_filename if 'custom_filename' in locals() else None)
            df, error = process_chat_file(content, filename)
            
            if error:
                st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box">✅ Successfully loaded chat from: {filename}</div>', unsafe_allow_html=True)
                source_info = f"URL: {url_input}"
                st.session_state.df = df
                st.session_state.analysis_done = True
                st.session_state.url_processed = True

# Handle zip file
elif input_method == "📦 Zip File" and uploaded_zip is not None:
    with st.spinner("🔄 Processing zip file (this may take a moment)..."):
        df, errors = process_zip_file(uploaded_zip)
        if df is not None:
            source_info = f"Zip file: {uploaded_zip.name}"
            st.session_state.df = df
            st.session_state.analysis_done = True
            st.markdown(f'<div class="success-box">✅ Successfully loaded zip file with {len(df)} messages</div>', unsafe_allow_html=True)

# Display errors if any
if errors:
    if isinstance(errors, list):
        for error in errors:
            st.markdown(f'<div class="error-box">⚠️ {error}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-box">⚠️ {errors}</div>', unsafe_allow_html=True)

# Main analysis section - Always show if data is loaded
if st.session_state.df is not None and not st.session_state.df.empty:
    df = st.session_state.df
    
    # Display basic info about the chat
    st.markdown("## 📊 Chat Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Messages", f"{len(df):,}")
    with col2:
        date_range = f"{df['only_date'].min()} to {df['only_date'].max()}"
        st.metric("Date Range", date_range)
    with col3:
        unique_users = len(df[df['user'] != 'group_notification']['user'].unique())
        st.metric("Active Users", unique_users)
    with col4:
        total_days = (pd.to_datetime(df['only_date'].max()) - pd.to_datetime(df['only_date'].min())).days
        st.metric("Total Days", f"{total_days} days")
    
    # Get unique users
    users = df["user"].unique().tolist()
    if "group_notification" in users:
        users.remove("group_notification")
    
    users.sort()
    users.insert(0, "Overall")
    
    # User selection and analyze button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_user = st.selectbox(
            "👤 Select User for Analysis",
            users,
            index=0,
            key="user_selector"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🔍 Analyze Now", use_container_width=True, type="primary", key="analyze_btn")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📥 Export Raw Data", use_container_width=True, key="export_btn"):
            csv = df.to_csv(index=False)
            st.markdown(create_download_link(csv, "raw_chat_data.csv"), unsafe_allow_html=True)
    
    # Perform analysis when button is clicked
    if analyze_btn:
        st.session_state.selected_user = selected_user
        st.session_state.show_analysis = True
    
    # Show analysis results
    if st.session_state.show_analysis:
        selected_user = st.session_state.selected_user
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Basic Statistics
        status_text.text("📊 Calculating statistics...")
        progress_bar.progress(10)
        num, words, media, links = helper.fetch_stats(selected_user, df)
        
        # Display stats in beautiful cards
        st.markdown("## 📈 Statistics")
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
        st.markdown("## 📅 Timeline Analysis")
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
            report = export_analysis(df, selected_user)
            st.markdown(create_download_link(report, "chat_analysis_report.txt"), unsafe_allow_html=True)
        
        with col2:
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
        - 🔗 **Smart URL Support** - Paste any chat link (Google Drive, GitHub, Pastebin, etc.)
        - 📥 **Export Results** - Download reports and processed data
        
        ### URL Features:
        - ✅ **Google Drive** - Automatically converts to direct download
        - ✅ **GitHub** - Converts blob to raw content
        - ✅ **Pastebin** - Fetches raw paste content
        - ✅ **Direct Links** - Works with any public .txt file
        - ✅ **URL History** - Remembers recent URLs
        
        ### Getting Started:
        1. Export your WhatsApp chat (without media)
        2. Choose input method from sidebar
        3. Upload file, paste URL, or upload zip
        4. Click "Analyze Now" to see insights!
        """)
