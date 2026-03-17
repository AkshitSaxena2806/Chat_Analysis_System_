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
import base64
import emoji
from collections import Counter

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer", 
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .main-header h1 {
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        border-radius: 15px;
        padding: 1.8rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(37, 211, 102, 0.3);
        transition: transform 0.3s ease;
        height: 100%;
    }
    .stat-card:hover {
        transform: translateY(-10px);
    }
    .stat-number {
        font-size: 3rem;
        font-weight: bold;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 1.1rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #25D366;
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateX(10px);
    }
    .stButton > button {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 50px;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(37, 211, 102, 0.5);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 50px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .metric-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #25D366;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 15px;
        padding: 1.2rem;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = "Overall"

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/whatsapp--v1.png", width=80)
    st.title("📱 Chat Analysis")
    st.markdown("---")
    
    # Upload section
    st.markdown("### 📤 Upload Chat")
    uploaded_file = st.file_uploader(
        "Choose a WhatsApp chat file",
        type=['txt'],
        help="Export chat without media from WhatsApp"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 Supported Formats", expanded=True):
        st.markdown("""
        **Format 1 (with AM/PM):**
        `05/09/25, 10:21 am - Message`
        
        **Format 2 (24-hour):**
        `14/07/25, 12:30 - Message`
        
        **How to Export:**
        - Android: Chat menu → More → Export Chat → Without Media
        - iPhone: Contact/Group name → Export Chat → Without Media
        """)

# Main header
st.markdown("""
<div class="main-header">
    <h1>💬 WhatsApp Chat Analyzer</h1>
    <p>Transform your conversations into beautiful insights and analytics</p>
</div>
""", unsafe_allow_html=True)

# Process file
if uploaded_file:
    try:
        with st.spinner("🔄 Processing your chat..."):
            # Read file
            bytes_data = uploaded_file.getvalue()
            data = bytes_data.decode("utf-8", errors="ignore")
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📊 Analyzing chat structure...")
            progress_bar.progress(30)
            
            # Preprocess
            df = Chat_Analysis.preprocess(data)
            
            if df.empty:
                st.error("❌ Could not parse the chat file. Please check the format.")
                st.stop()
            
            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.df = df
            st.session_state.analysis_done = True
            
            # Show success message with stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{len(df):,}</div>
                    <div class="metric-label">Total Messages</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                unique_users = len([u for u in df['user'].unique() if u not in ['System', 'group_notification']])
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{unique_users}</div>
                    <div class="metric-label">Active Users</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                date_range = f"{df['date'].min().strftime('%d/%m/%y')} - {df['date'].max().strftime('%d/%m/%y')}"
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value" style="font-size: 1.5rem;">{date_range}</div>
                    <div class="metric-label">Date Range</div>
                </div>
                """, unsafe_allow_html=True)
            
            # User selection
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                users = ['Overall'] + [u for u in sorted(df['user'].unique()) if u not in ['System', 'group_notification']]
                selected_user = st.selectbox(
                    "👤 Select User to Analyze",
                    users,
                    index=0,
                    format_func=lambda x: f"👥 {x}" if x == "Overall" else f"👤 {x}"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                analyze_btn = st.button("🔍 Analyze", use_container_width=True)
            
            if analyze_btn:
                st.session_state.selected_user = selected_user
                
                # Progress for analysis
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Get stats
                status_text.text("📊 Calculating statistics...")
                progress_bar.progress(10)
                num_messages, total_words, num_media, num_links = helper.fetch_stats(selected_user, df)
                
                # Display stats
                st.markdown("## 📈 Overview Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{num_messages:,}</div>
                        <div class="stat-label">Total Messages</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{total_words:,}</div>
                        <div class="stat-label">Total Words</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{num_media}</div>
                        <div class="stat-label">Media Shared</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{num_links}</div>
                        <div class="stat-label">Links Shared</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Quick insights
                progress_bar.progress(20)
                status_text.text("💡 Generating insights...")
                
                st.markdown("## 💡 Quick Insights")
                col1, col2 = st.columns(2)
                
                with col1:
                    week_map = helper.week_activity_map(selected_user, df)
                    month_map = helper.month_activity_map(selected_user, df)
                    
                    # Calculate safely
                    most_active_day = week_map.idxmax() if not week_map.empty else 'N/A'
                    most_active_month = month_map.idxmax() if not month_map.empty else 'N/A'
                    avg_words = (total_words / num_messages) if num_messages > 0 else 0
                    
                    st.markdown(f"""
                    <div class="feature-card">
                        <h4>⏰ Activity Pattern</h4>
                        <p>• <b>Most active day:</b> {most_active_day}</p>
                        <p>• <b>Most active month:</b> {most_active_month}</p>
                        <p>• <b>Avg words/message:</b> {avg_words:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    media_pct = (num_media / num_messages * 100) if num_messages > 0 else 0
                    text_messages = num_messages - num_media if num_messages > 0 else 0
                    
                    st.markdown(f"""
                    <div class="feature-card">
                        <h4>📊 Content Mix</h4>
                        <p>• <b>Media percentage:</b> {media_pct:.1f}%</p>
                        <p>• <b>Text messages:</b> {text_messages:,}</p>
                        <p>• <b>Links shared:</b> {num_links}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Timeline Analysis
                progress_bar.progress(40)
                status_text.text("📅 Creating timelines...")
                
                st.markdown("## 📅 Timeline Analysis")
                tab1, tab2, tab3 = st.tabs(["📊 Monthly", "📆 Daily", "⏰ Hourly"])
                
                with tab1:
                    timeline = helper.monthly_timelines(selected_user, df)
                    if not timeline.empty:
                        fig = px.line(timeline, x='time', y='message',
                                     title='Monthly Message Activity',
                                     labels={'time': 'Month', 'message': 'Messages'})
                        fig.update_traces(line_color='#25D366', line_width=3)
                        fig.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    daily = helper.daily_timeline(selected_user, df)
                    if not daily.empty:
                        fig = px.bar(daily, x='only_date', y='message',
                                    title='Daily Message Activity',
                                    labels={'only_date': 'Date', 'message': 'Messages'})
                        fig.update_traces(marker_color='#25D366')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    if 'hour' in df.columns:
                        hourly = df.groupby('hour').size().reset_index(name='count')
                        all_hours = pd.DataFrame({'hour': range(24)})
                        hourly = pd.merge(all_hours, hourly, on='hour', how='left').fillna(0)
                        
                        fig = px.bar(hourly, x='hour', y='count',
                                    title='Hourly Activity Pattern (24-Hour Format)',
                                    labels={'hour': 'Hour of Day', 'count': 'Messages'})
                        fig.update_traces(marker_color='#25D366')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Peak hour
                        peak_hour = hourly.loc[hourly['count'].idxmax(), 'hour']
                        st.info(f"⏰ **Peak activity time:** {int(peak_hour):02d}:00 ({'AM' if peak_hour < 12 else 'PM'})")
                
                # Activity Heatmap
                progress_bar.progress(60)
                status_text.text("🔥 Generating heatmap...")
                
                st.markdown("## 🔥 Activity Heatmap")
                heatmap_data = helper.activity_heatmap(selected_user, df)
                if not heatmap_data.empty:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt='g',
                               ax=ax, cbar_kws={'label': 'Messages'})
                    plt.title('Weekly Activity Pattern', fontsize=14, fontweight='bold')
                    plt.ylabel('Day of Week')
                    plt.xlabel('Time Period')
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("Not enough data for heatmap")
                
                # User Activity Analysis (for Overall view)
                if selected_user == 'Overall':
                    progress_bar.progress(70)
                    status_text.text("👥 Analyzing user activity...")
                    
                    st.markdown("## 👥 User Activity Analysis")
                    col1, col2 = st.columns(2)
                    
                    busy_users, user_df = helper.most_busy_users(df)
                    
                    with col1:
                        if not busy_users.empty:
                            fig = px.pie(values=busy_users.values, names=busy_users.index,
                                        title='Message Distribution by User')
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if not user_df.empty:
                            st.dataframe(
                                user_df.style.highlight_max(color='#90EE90'),
                                use_container_width=True,
                                height=400
                            )
                
                # Text Analysis
                progress_bar.progress(80)
                status_text.text("📝 Analyzing text content...")
                
                st.markdown("## 📝 Text Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("☁️ Word Cloud")
                    wc = helper.workcloud(selected_user, df, max_words=150)
                    if wc:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.imshow(wc)
                        ax.axis('off')
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("Not enough text data for word cloud")
                
                with col2:
                    st.subheader("📊 Most Common Words")
                    common_words = helper.most_common_words(selected_user, df)
                    if not common_words.empty:
                        fig = px.bar(common_words.head(10), x='Frequency', y='Word',
                                    orientation='h', title='Top 10 Words')
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No common words found")
                
                # Emoji Analysis
                progress_bar.progress(90)
                status_text.text("😊 Analyzing emojis...")
                
                st.markdown("## 😊 Emoji Analysis")
                col1, col2 = st.columns(2)
                
                emoji_df = helper.emojies(selected_user, df)
                
                with col1:
                    if not emoji_df.empty:
                        st.subheader("Top Emojis")
                        st.dataframe(
                            emoji_df.rename(columns={'Emoji': 'Emoji', 'Count': 'Count'}),
                            use_container_width=True,
                            height=400
                        )
                
                with col2:
                    if not emoji_df.empty:
                        top_emojis = emoji_df.head(8)
                        fig = px.pie(values=top_emojis['Count'], names=top_emojis['Emoji'],
                                    title='Top 8 Emojis')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No emojis found")
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis Complete!")
                progress_bar.empty()
                status_text.empty()
                
                # Download section
                st.markdown("---")
                st.markdown("## 📥 Download Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📊 Download Processed Data (CSV)",
                        data=csv,
                        file_name="chat_analysis_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Create report
                    report = f"""WHATSAPP CHAT ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: {selected_user}

STATISTICS
----------
Total Messages: {num_messages:,}
Total Words: {total_words:,}
Media Shared: {num_media}
Links Shared: {num_links}

ACTIVITY SUMMARY
---------------
Most Active Day: {most_active_day}
Most Active Month: {most_active_month}
Average Words/Message: {avg_words:.1f}
Media Percentage: {media_pct:.1f}%

"""
                    st.download_button(
                        label="📄 Download Report (TXT)",
                        data=report,
                        file_name="chat_analysis_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
    
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("Please check your file format and try again.")

else:
    # Welcome screen
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image("https://img.icons8.com/clouds/400/000000/whatsapp.png", width=300)
    
    with col2:
        st.markdown("""
        <div style="padding: 2rem;">
            <h2 style="color: #25D366;">🚀 Get Started</h2>
            <p style="font-size: 1.2rem; line-height: 1.6;">
                Upload your WhatsApp chat export to unlock powerful insights:
            </p>
            <ul style="font-size: 1.1rem; line-height: 2;">
                <li>📊 Message statistics and trends</li>
                <li>📅 Activity timelines and patterns</li>
                <li>🔥 Interactive heatmaps</li>
                <li>👥 User participation analysis</li>
                <li>☁️ Word clouds and text analysis</li>
                <li>😊 Emoji usage tracking</li>
            </ul>
            <div class="info-box">
                <strong>💡 Tip:</strong> Export your chat without media for best results!<br>
                <strong>📌 Supports both:</strong><br>
                • 05/09/25, 10:21 am - Message<br>
                • 14/07/25, 12:30 - Message
            </div>
        </div>
        """, unsafe_allow_html=True)
