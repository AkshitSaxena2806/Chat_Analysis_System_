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
    .insight-box {
        background-color: #f0f2f6;
        border-left: 5px solid #075e54;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = "Overall"

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/whatsapp--v1.png", width=80)
    st.title("📱 Chat Analysis")
    st.markdown("---")
    
    # Upload options
    upload_option = st.radio(
        "Choose upload type:",
        ["📄 Single Text File", "📦 Zip File"],
        help="Upload a single WhatsApp chat export or multiple chats in a zip file"
    )
    
    uploaded_file = None
    uploaded_zip = None
    
    if upload_option == "📄 Single Text File":
        uploaded_file = st.file_uploader(
            "Upload WhatsApp chat (.txt)", 
            type="txt",
            help="Export chat without media from WhatsApp"
        )
    else:
        uploaded_zip = st.file_uploader(
            "Upload Zip file", 
            type="zip",
            help="Zip file containing multiple WhatsApp chat exports"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        show_stopwords = st.checkbox("Show stopwords", value=False)
        max_words = st.slider("Max words in wordcloud", 100, 500, 200)
        color_theme = st.selectbox(
            "Color theme",
            ["Default", "Dark", "Light", "Colorful"]
        )

def process_chat_file(file_content, filename="uploaded_chat.txt"):
    """Process a single chat file"""
    try:
        data = file_content.decode("utf-8")
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
                st.markdown("""
                <div class="stat-card">
                    <div class="stat-number">{}</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                """.format(num), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="stat-card">
                    <div class="stat-number">{}</div>
                    <div class="stat-label">Total Words</div>
                </div>
                """.format(words), unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div class="stat-card">
                    <div class="stat-number">{}</div>
                    <div class="stat-label">Media Shared</div>
                </div>
                """.format(media), unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                <div class="stat-card">
                    <div class="stat-number">{}</div>
                    <div class="stat-label">Links Shared</div>
                </div>
                """.format(links), unsafe_allow_html=True)
            
            # Quick insights
            st.markdown("## 💡 Quick Insights")
            with st.container():
                avg_words_per_msg = round(words/num if num>0 else 0, 2)
                media_percentage = round((media/num)*100 if num>0 else 0, 2)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="insight-box">
                        <h4>📝 Message Style</h4>
                        <p>• Average words per message: <b>{avg_words_per_msg}</b></p>
                        <p>• Media percentage: <b>{media_percentage}%</b></p>
                        <p>• Links shared: <b>{links}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="insight-box">
                        <h4>⏰ Activity Summary</h4>
                        <p>• Most active day: <b>{helper.week_activity_map(selected_user, df).idxmax() if not helper.week_activity_map(selected_user, df).empty else "N/A"}</b></p>
                        <p>• Most active month: <b>{helper.month_activity_map(selected_user, df).idxmax() if not helper.month_activity_map(selected_user, df).empty else "N/A"}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            
            progress_bar.progress(30)
            
            # Timeline Analysis
            st.markdown("## 📈 Timeline Analysis")
            tab1, tab2, tab3 = st.tabs(["Monthly Timeline", "Daily Timeline", "Hourly Activity"])
            
            with tab1:
                mt = helper.monthly_timelines(selected_user, df)
                if mt is not None and not mt.empty:
                    fig = px.line(mt, x='time', y='message', 
                                 title='Message Activity Over Time',
                                 labels={'time': 'Month-Year', 'message': 'Number of Messages'})
                    fig.update_traces(line_color='#075e54', line_width=3)
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                daily_timeline = helper.daily_timeline(selected_user, df)
                if daily_timeline is not None and not daily_timeline.empty:
                    fig = px.bar(daily_timeline, x='only_date', y='message',
                                title='Daily Message Count',
                                labels={'only_date': 'Date', 'message': 'Messages'})
                    fig.update_traces(marker_color='#25D366')
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                if 'hour' in df.columns:
                    hourly_activity = df.groupby('hour').count()['message'].reset_index()
                    fig = px.bar(hourly_activity, x='hour', y='message',
                                title='Hourly Activity Pattern',
                                labels={'hour': 'Hour of Day', 'message': 'Messages'})
                    fig.update_traces(marker_color='#128C7E')
                    st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(50)
            
            # Activity Heatmap
            st.markdown("## 🔥 Activity Heatmap")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if user_heatmap is not None and not user_heatmap.empty:
                fig, ax = plt.subplots(figsize=(12, 6))
                sns.heatmap(user_heatmap, cmap='YlOrRd', annot=True, fmt='g', ax=ax, cbar_kws={'label': 'Message Count'})
                plt.title('Weekly Activity Pattern', fontsize=16, fontweight='bold')
                plt.ylabel('Day of Week')
                plt.xlabel('Time Period')
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
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("User Contribution Percentage")
                    st.dataframe(
                        new_df.style.highlight_max(axis=0, color='#90EE90'),
                        use_container_width=True
                    )
            
            progress_bar.progress(85)
            
            # Text Analysis
            st.markdown("## 📝 Text Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("☁️ Word Cloud")
                wc = helper.workcloud(selected_user, df, max_words=max_words)
                if wc is not None:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.imshow(wc)
                    ax.axis("off")
                    st.pyplot(fig)
                    plt.close()
            
            with col2:
                st.subheader("📊 Most Common Words")
                most_common_df = helper.most_common_words(selected_user, df)
                if most_common_df is not None and not most_common_df.empty:
                    fig = px.bar(most_common_df.head(15), x=1, y=0,
                               orientation='h',
                               title='Top 15 Common Words',
                               labels={0: 'Words', 1: 'Frequency'})
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(95)
            
            # Emoji Analysis
            st.markdown("## 😊 Emoji Analysis")
            col1, col2 = st.columns(2)
            
            emoji_df = helper.emojies(selected_user, df)
            
            with col1:
                if emoji_df is not None and not emoji_df.empty:
                    st.subheader("Emoji Usage Stats")
                    st.dataframe(
                        emoji_df.rename(columns={0: 'Emoji', 1: 'Count'}),
                        use_container_width=True
                    )
            
            with col2:
                if emoji_df is not None and not emoji_df.empty:
                    st.subheader("Top Emojis")
                    top_emojis = emoji_df.head(8)
                    fig = px.pie(values=top_emojis[1], names=top_emojis[0],
                                title='Top 8 Emojis Distribution')
                    st.plotly_chart(fig, use_container_width=True)
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis Complete!")
            progress_bar.empty()
            status_text.empty()
            
            # Add download section
            st.markdown("## 📥 Download Results")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Download Analysis Report"):
                    report = export_analysis(df, selected_user)
                    st.markdown(create_download_link(report, "chat_analysis_report.txt"), unsafe_allow_html=True)
            
            with col2:
                if st.button("📁 Download Processed Data (CSV)"):
                    csv = df.to_csv(index=False)
                    st.markdown(create_download_link(csv, "processed_chat_data.csv"), unsafe_allow_html=True)

elif not st.session_state.analysis_done:
    # Welcome screen
    col1, col2 = st.columns([1, 1])
    
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
        - 📥 **Export Results** - Download reports and processed data
        
        ### Getting Started:
        1. Export your WhatsApp chat (without media)
        2. Upload the .txt file or zip multiple chats
        3. Select a user or view overall analysis
        4. Click "Analyze" to see insights!
        
        ### How to Export:
        - **Android**: Chat menu → More → Export Chat → Without Media
        - **iPhone**: Contact/Group name → Export Chat → Without Media
        """)
        
        with st.expander("📖 Detailed Instructions"):
            st.markdown("""
            ### Step-by-Step Guide
            
            **Android:**
            1. Open the WhatsApp chat you want to analyze
            2. Tap on the three dots in the top right
            3. Select "More" → "Export Chat"
            4. Choose "Without Media"
            5. Save the .txt file to your device
            
            **iPhone:**
            1. Open the WhatsApp chat
            2. Tap on the contact name or group subject
            3. Scroll down and tap "Export Chat"
            4. Choose "Without Media"
            5. Save the .txt file
            
            **Tips:**
            - For group chats, all participants will be analyzed
            - You can upload multiple chats in a zip file for combined analysis
            - Media files are not included to keep the analysis lightweight
            """)
