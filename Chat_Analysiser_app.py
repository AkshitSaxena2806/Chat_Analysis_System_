import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import Chat_Analysis
import helper
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import emoji

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer", 
    page_icon="💬",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Apply theme based on session state
if 'dark_mode' in st.session_state and st.session_state.dark_mode:
    # Note: Streamlit's native dark theme is applied via config.toml or user settings
    # Our custom CSS will handle the visual styling
    pass

# Custom CSS with Dark Mode Support
st.markdown("""
<style>
    :root {
        --primary-gradient: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        --bg-color: #f8f9fa;
        --card-bg: white;
        --text-color: #212529;
        --shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    [data-theme="dark"] {
        --bg-color: #0e1117;
        --card-bg: #1a1f2e;
        --text-color: #fafafa;
        --shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    
    .main-header {
        background: var(--primary-gradient);
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
        background: var(--primary-gradient);
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
        background: var(--card-bg);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border-left: 5px solid #25D366;
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
        color: var(--text-color);
    }
    .feature-card h4 {
        color: #25D366;
        margin-top: 0;
    }
    .feature-card:hover {
        transform: translateX(10px);
    }
    .stButton > button {
        background: var(--primary-gradient);
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
        background-color: var(--bg-color);
        padding: 0.5rem;
        border-radius: 50px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .metric-container {
        background: linear-gradient(135deg, var(--bg-color) 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow);
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
        background: var(--primary-gradient);
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        font-size: 0.9rem;
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
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Sidebar
with st.sidebar:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://img.icons8.com/color/96/000000/whatsapp--v1.png", width=80)
    
    st.title("📱 Chat Analysis")
    st.markdown("---")
    
    # Theme Toggle
    st.markdown("### 🎨 Appearance")
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📤 Upload Chat")
    uploaded_file = st.file_uploader("Choose a WhatsApp chat file", type=['txt'])
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
    else:
        st.info("📁 Please upload a WhatsApp chat export file")
    
    st.markdown("---")
    
    with st.expander("📖 Supported Formats", expanded=True):
        st.markdown("""
        **Format 1 (with AM/PM):**  
        `05/09/25, 10:21 am - Message`

        **Format 2 (24-hour):**  
        `14/07/25, 12:30 - Message`

        **How to Export:**  
        Android: Chat menu → More → Export Chat → Without Media  
        iPhone: Contact/Group name → Export Chat → Without Media
        """)
    
    st.markdown("---")
    st.markdown("### 🛠️ About")
    st.markdown("""
    **WhatsApp Chat Analyzer**  
    Version 2.0  
    
    Transform your conversations into beautiful insights and analytics.
    """)

# Main header
st.markdown('<div class="main-header"><h1>💬 WhatsApp Chat Analyzer</h1><p>Transform your conversations into beautiful insights and analytics</p></div>', unsafe_allow_html=True)

# Main content
if uploaded_file:
    try:
        with st.spinner("🔄 Processing your chat..."):
            # Read and decode file
            bytes_data = uploaded_file.getvalue()
            data = bytes_data.decode("utf-8", errors="ignore")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📊 Analyzing chat structure...")
            progress_bar.progress(30)

            # Preprocess data
            df = Chat_Analysis.preprocess(data)
            
            if df.empty:
                st.error("❌ Could not parse the chat file. Please check the format.")
                st.stop()
            
            # Filter out system messages
            df = df[~df['user'].str.contains('System', na=False)]
            
            if len(df) == 0:
                st.error("❌ No valid messages found in the chat file.")
                st.stop()

            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            progress_bar.empty()
            status_text.empty()

            st.session_state.df = df
            st.session_state.analysis_done = True

            # Quick stats
            st.markdown("## 📊 Quick Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'<div class="metric-container"><div class="metric-value">{len(df):,}</div><div class="metric-label">Total Messages</div></div>', unsafe_allow_html=True)
            
            with col2:
                unique_users = len([u for u in df['user'].unique() if u not in ['System', 'group_notification']])
                st.markdown(f'<div class="metric-container"><div class="metric-value">{unique_users}</div><div class="metric-label">Active Users</div></div>', unsafe_allow_html=True)
            
            with col3:
                start_date = df['date'].min().strftime('%d/%m/%y')
                end_date = df['date'].max().strftime('%d/%m/%y')
                st.markdown(f'<div class="metric-container"><div class="metric-value" style="font-size:1.5rem;">{start_date}<br>{end_date}</div><div class="metric-label">Date Range</div></div>', unsafe_allow_html=True)
            
            with col4:
                days = (df['date'].max() - df['date'].min()).days
                st.markdown(f'<div class="metric-container"><div class="metric-value">{days}</div><div class="metric-label">Total Days</div></div>', unsafe_allow_html=True)

            # User selection
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                users = ['Overall'] + [u for u in sorted(df['user'].unique()) if u not in ['System', 'group_notification']]
                selected_user = st.selectbox("👤 Select User to Analyze", users, index=0,format_func=lambda x: f"👥 {x}" if x == "Overall" else f"👤 {x}")
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                analyze_btn = st.button("🔍 Analyze Now", use_container_width=True)

            if analyze_btn:
                st.session_state.selected_user = selected_user
                
                # Progress tracking for analysis
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 1. Statistics
                status_text.text("📊 Calculating statistics...")
                progress_bar.progress(10)
                num, words, media, links = helper.fetch_stats(selected_user, df)

                st.markdown("## 📈 Overview Statistics")
                cols = st.columns(4)
                for i, (val, label) in enumerate([(num, "Total Messages"), (words, "Total Words"),(media, "Media Shared"), (links, "Links Shared")]):
                    with cols[i]:
                        st.markdown(f'<div class="stat-card"><div class="stat-number">{val:,}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

                # 2. Quick insights
                progress_bar.progress(20)
                status_text.text("💡 Generating insights...")
                
                week_map = helper.week_activity_map(selected_user, df)
                month_map = helper.month_activity_map(selected_user, df)
                
                most_day = week_map.idxmax() if not week_map.empty else 'N/A'
                most_month = month_map.idxmax() if not month_map.empty else 'N/A'
                avg_words = (words / num) if num > 0 else 0
                media_pct = (media / num * 100) if num > 0 else 0
                text_msg = num - media if num > 0 else 0

                st.markdown("## 💡 Quick Insights")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="feature-card">
                        <h4>⏰ Activity Pattern</h4>
                        <p>• <b>Most active day:</b> {most_day}</p>
                        <p>• <b>Most active month:</b> {most_month}</p>
                        <p>• <b>Avg words/message:</b> {avg_words:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="feature-card">
                        <h4>📊 Content Mix</h4>
                        <p>• <b>Media percentage:</b> {media_pct:.1f}%</p>
                        <p>• <b>Text messages:</b> {text_msg:,}</p>
                        <p>• <b>Links shared:</b> {links}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # 3. Timeline Analysis
                progress_bar.progress(40)
                status_text.text("📅 Creating timelines...")
                st.markdown("## 📅 Timeline Analysis")
                
                tab1, tab2, tab3 = st.tabs(["📊 Monthly Timeline", "📆 Daily Timeline", "⏰ Hourly Activity"])

                with tab1:
                    tl = helper.monthly_timelines(selected_user, df)
                    if not tl.empty:
                        fig = px.line(tl, x='time', y='message', title='Monthly Message Activity')
                        fig.update_traces(line_color='#25D366', line_width=3)
                        fig.update_layout(
                            showlegend=False, 
                            height=400,
                            xaxis_title="Month",
                            yaxis_title="Messages"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Not enough data for monthly timeline")

                with tab2:
                    daily = helper.daily_timeline(selected_user, df)
                    if not daily.empty:
                        fig = px.bar(daily, x='only_date', y='message', title='Daily Message Activity')
                        fig.update_traces(marker_color='#25D366')
                        fig.update_layout(
                            height=400,
                            xaxis_title="Date",
                            yaxis_title="Messages"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Not enough data for daily timeline")

                with tab3:
                    if 'hour' in df.columns:
                        hourly_data = []
                        for hour in range(24):
                            if selected_user != 'Overall':
                                count = len(df[(df['user'] == selected_user) & (df['hour'] == hour)])
                            else:
                                count = len(df[df['hour'] == hour])
                            hourly_data.append({'hour': hour, 'count': count})
                        
                        hourly_df = pd.DataFrame(hourly_data)
                        
                        fig = px.bar(hourly_df, x='hour', y='count', title='Hourly Activity (24-hour format)')
                        fig.update_traces(marker_color='#25D366')
                        fig.update_layout(
                            height=400,
                            xaxis_title="Hour of Day",
                            yaxis_title="Messages",
                            xaxis=dict(tickmode='linear', tick0=0, dtick=2)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Peak hour
                        peak_hour = hourly_df.loc[hourly_df['count'].idxmax(), 'hour']
                        peak_count = hourly_df['count'].max()
                        st.info(f"⏰ **Peak activity time:** {int(peak_hour):02d}:00 - {int(peak_hour):02d}:59 ({peak_count:,} messages)")

                # 4. Activity Heatmap
                progress_bar.progress(60)
                status_text.text("🔥 Generating heatmap...")
                st.markdown("## 🔥 Activity Heatmap")
                
                heat = helper.activity_heatmap(selected_user, df)
                if not heat.empty:
                    fig, ax = plt.subplots(figsize=(14, 6))
                    sns.heatmap(heat, cmap='YlOrRd', annot=True, fmt='g', ax=ax,cbar_kws={'label': 'Number of Messages'}, linewidths=0.5)
                    plt.title('Weekly Activity Pattern', fontsize=14, fontweight='bold', pad=20)
                    plt.ylabel('Day of Week', fontsize=12)
                    plt.xlabel('Time Period', fontsize=12)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                
                # 5. User Analysis (Only for Overall) - moved outside else block
                if selected_user == 'Overall':
                    progress_bar.progress(70)
                    status_text.text("👥 Analyzing user activity...")
                    st.markdown("## 👥 User Activity Analysis")
                    
                    col1, col2 = st.columns(2)
                    busy_users, user_percentages = helper.most_busy_users(df)
                    
                    with col1:
                        if not busy_users.empty:
                            fig = px.pie(
                                values=busy_users.values, 
                                names=busy_users.index, 
                                title='Message Distribution by User',
                                hole=0.3
                            )
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            fig.update_layout(height=500)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if not user_percentages.empty:
                            st.subheader("📊 User Activity Percentage")
                            styled_df = user_percentages.style.background_gradient(cmap='Greens', subset=['Percentage'])
                            st.dataframe(styled_df, use_container_width=True, height=500)

                # 6. Text Analysis
                progress_bar.progress(80)
                status_text.text("📝 Analyzing text content...")
                st.markdown("## 📝 Text Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("☁️ Word Cloud")
                    wc = helper.workcloud(selected_user, df)
                    if wc:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.imshow(wc, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                        plt.close()
                    else:
                        # Fallback: if wordcloud lib isn't available, show a treemap "cloud"
                        fallback_words = helper.most_common_words(selected_user, df)
                        if fallback_words is not None and not fallback_words.empty:
                            top = fallback_words.head(50).copy()
                            fig = px.treemap(
                                top,
                                path=["Word"],
                                values="Frequency",
                                title="Word Cloud (Fallback)",
                                color="Frequency",
                                color_continuous_scale="Greens",
                            )
                            fig.update_layout(height=420, margin=dict(t=50, l=10, r=10, b=10))
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Not enough text data for word cloud")
                
                with col2:
                    st.subheader("📊 Most Common Words")
                    common_words = helper.most_common_words(selected_user, df)
                    if not common_words.empty:
                        fig = px.bar(common_words.head(10),x='Frequency',y='Word',orientation='h',title='Top 10 Most Used Words',color='Frequency', color_continuous_scale='Greens')
                        fig.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            height=500,
                            xaxis_title="Frequency",
                            yaxis_title="Word"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No common words found")

                # 7. Emoji Analysis
                progress_bar.progress(90)
                status_text.text("😊 Analyzing emoji usage...")
                st.markdown("## 😊 Emoji Analysis")
                
                col1, col2 = st.columns(2)
                emoji_df = helper.emojies(selected_user, df)
                
                with col1:
                    if not emoji_df.empty:
                        st.subheader("📋 Top Emojis")
                        
                        # Create a display version with emoji and count
                        display_df = emoji_df.copy()
                        display_df['Emoji with Name'] = display_df['Emoji'] + '  '  # Add space for better display
                        
                        # Style the dataframe
                        styled_emoji = display_df.style.background_gradient(cmap='Blues', subset=['Count'])
                        st.dataframe(styled_emoji, use_container_width=True, height=500)
                    else:
                        st.info("No emojis found in messages")
                
                with col2:
                    if not emoji_df.empty:
                        st.subheader("🥧 Emoji Distribution")
                        top_emojis = emoji_df.head(8)  # Top 8 for better visualization
                        
                        fig = px.pie(
                            values=top_emojis['Count'], 
                            names=top_emojis['Emoji'], 
                            title='Top 8 Emojis Used',
                            hole=0.3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No emoji data available")

                # 7.5 Interactive Comparison Tool (New Feature)
                if len(df['user'].unique()) >= 2:
                    st.markdown("## 🔍 Compare Users")
                    st.markdown("Select two users to compare their activity patterns")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        user1 = st.selectbox(
                            "First User",
                            [u for u in sorted(df['user'].unique()) if u not in ['System', 'group_notification']],
                            key="user1"
                        )
                    with col2:
                        user2 = st.selectbox(
                            "Second User",
                            [u for u in sorted(df['user'].unique()) if u not in ['System', 'group_notification']]
                            ,key="user2"
                        )
                    
                    if user1 and user2 and user1 != user2:
                        # Create comparison data
                        comp_data = {
                            'Metric': ['Total Messages', 'Total Words', 'Media Shared', 'Links Shared', 'Avg Words/Message'],
                            user1: [],
                            user2: []
                        }
                        
                        for user in [user1, user2]:
                            num, words, media, links = helper.fetch_stats(user, df)
                            avg_words = words / num if num > 0 else 0
                            if user == user1:
                                comp_data[user] = [num, words, media, links, f"{avg_words:.1f}"]
                            else:
                                comp_data[user2] = [num, words, media, links, f"{avg_words:.1f}"]
                        
                        comp_df = pd.DataFrame(comp_data)
                        st.dataframe(comp_df, use_container_width=True)
                        
                        # Visual comparison
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            name=user1,
                            x=comp_df['Metric'],
                            y=[float(comp_df[user1].iloc[i]) if i < 4 else comp_df[user1].iloc[i] for i in range(5)],
                            marker_color='#25D366'
                        ))
                        fig.add_trace(go.Bar(
                            name=user2,
                            x=comp_df['Metric'],
                            y=[float(comp_df[user2].iloc[i]) if i < 4 else comp_df[user2].iloc[i] for i in range(5)],
                            marker_color='#128C7E'
                        ))
                        fig.update_layout(
                            barmode='group',
                            height=500,
                            title=f"Comparison: {user1} vs {user2}",
                            xaxis_title="Metric",
                            yaxis_title="Value"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # 8. Additional Insights (New Section)
                progress_bar.progress(95)
                status_text.text("🎯 Generating additional insights...")
                st.markdown("## 🎯 Additional Insights")

                # Ensure these exist even if earlier sections changed
                week_map = helper.week_activity_map(selected_user, df)
                month_map = helper.month_activity_map(selected_user, df)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Message length analysis
                    st.subheader("📏 Message Length Distribution")
                    
                    if selected_user != 'Overall':
                        user_df = df[df['user'] == selected_user]
                    else:
                        user_df = df
                    
                    # Calculate message lengths (excluding media)
                    text_messages = user_df[~user_df['message'].str.contains('<Media omitted>', na=False)]
                    if len(text_messages) > 0:
                        text_messages['msg_length'] = text_messages['message'].str.len()
                        
                        # Create bins for message lengths
                        bins = [0, 10, 25, 50, 100, 200, 500, 1000, float('inf')]
                        labels = ['0-10', '11-25', '26-50', '51-100', '101-200', '201-500', '501-1000', '1000+']
                        
                        text_messages['length_category'] = pd.cut(text_messages['msg_length'], bins=bins, labels=labels)
                        length_dist = text_messages['length_category'].value_counts().sort_index()
                        
                        fig = px.bar(
                            x=length_dist.index, 
                            y=length_dist.values,
                            title='Message Length Distribution',
                            labels={'x': 'Message Length (characters)', 'y': 'Count'},
                            color=length_dist.values,
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No text messages to analyze")
                
                with col2:
                    # Busiest days analysis
                    st.subheader("📅 Busiest Days")
                    
                    if not week_map.empty:
                        week_df = week_map.reset_index()
                        week_df.columns = ['Day', 'Messages']
                        
                        # Reorder days
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        week_df['Day'] = pd.Categorical(week_df['Day'], categories=day_order, ordered=True)
                        week_df = week_df.sort_values('Day')
                        
                        fig = px.bar(
                            week_df,
                            x='Day',
                            y='Messages',
                            title='Messages by Day of Week',
                            color='Messages',
                            color_continuous_scale='Reds'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No weekday data available")

                # 9. Busiest Months
                st.markdown("## 📊 Monthly Activity Patterns")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if not month_map.empty:
                        month_df = month_map.reset_index()
                        month_df.columns = ['Month', 'Messages']
                        
                        fig = px.bar(
                            month_df,
                            x='Month',
                            y='Messages',
                            title='Messages by Month',
                            color='Messages',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Year-over-year comparison if multiple years
                    if 'year' in df.columns:
                        year_counts = df['year'].value_counts().sort_index()
                        
                        if len(year_counts) > 1:
                            year_df = year_counts.reset_index()
                            year_df.columns = ['Year', 'Messages']
                            
                            fig = px.bar(
                                year_df,
                                x='Year',
                                y='Messages',
                                title='Messages by Year',
                                color='Messages',
                                color_continuous_scale='Purples'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info(f"Data available only for {int(year_counts.index[0])}")
                    else:
                        st.info("Year data not available")

                # 10. Conversation Flow Analysis (for Overall only)
                if selected_user == 'Overall' and len(df['user'].unique()) >= 2:
                    st.markdown("## 💬 Conversation Flow Analysis")
                    
                    # Get top users for flow analysis
                    top_users = df['user'].value_counts().head(5).index.tolist()
                    
                    # Create flow data
                    flow_data = []
                    for i in range(len(df) - 1):
                        current_user = df.iloc[i]['user']
                        next_user = df.iloc[i + 1]['user']
                        
                        if current_user in top_users and next_user in top_users and current_user != next_user:
                            flow_data.append({
                                'From': current_user,
                                'To': next_user
                            })
                    
                    if flow_data:
                        flow_df = pd.DataFrame(flow_data)
                        flow_counts = flow_df.groupby(['From', 'To']).size().reset_index(name='Count')
                        flow_counts = flow_counts.sort_values('Count', ascending=False).head(10)
                        
                        st.subheader("🔄 Top Conversation Flows")
                        st.dataframe(flow_counts, use_container_width=True)
                        
                        # Simple chord diagram alternative - sunburst
                        fig = px.sunburst(
                            flow_counts,
                            path=['From', 'To'],
                            values='Count',
                            title='Conversation Flow Between Users'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Not enough conversation flow data")

                # 11. Linguistic Error Detection
                progress_bar.progress(98)
                status_text.text("🔍 Detecting linguistic errors...")
                st.markdown("## 🔍 Linguistic Error Analysis")
                
                try:
                    error_df = helper.detect_linguistic_errors(selected_user, df)
                    
                    if not error_df.empty:
                        # Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        total_errors = error_df['Total Errors'].sum()
                        grammar_err = error_df['Grammar'].sum() + error_df['Tense'].sum() + error_df['Agreement'].sum()
                        typos = error_df['Typo'].sum()
                        avg_errors = total_errors / len(error_df) if len(error_df) > 0 else 0
                        
                        with col1:
                            st.markdown(f'<div class="metric-container"><div class="metric-value">{total_errors}</div><div class="metric-label">Total Errors</div></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div class="metric-container"><div class="metric-value">{grammar_err}</div><div class="metric-label">Grammar Issues</div></div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown(f'<div class="metric-container"><div class="metric-value">{typos}</div><div class="metric-label">Typos/Spelling</div></div>', unsafe_allow_html=True)
                        with col4:
                            st.markdown(f'<div class="metric-container"><div class="metric-value">{avg_errors:.2f}</div><div class="metric-label">Errors/Message</div></div>', unsafe_allow_html=True)
                            
                        st.markdown("### 📝 Highlighted Messages")
                        st.info("Hover over the highlighted text to see the error details.")
                        
                        # Display highlighted text
                        messages_with_errors = error_df[error_df['Total Errors'] > 0]
                        if not messages_with_errors.empty:
                            for _, row in messages_with_errors.head(20).iterrows(): # Show top 20
                                st.markdown(f"**{row['User']}** ({row['Date']}): {row['Highlighted Text']}", unsafe_allow_html=True)
                            if len(messages_with_errors) > 20:
                                st.caption(f"Showing first 20 out of {len(messages_with_errors)} messages with errors.")
                        else:
                            st.success("No linguistic errors found in these messages!")
                            
                        # 12. Error Tagging & Annotation Tool
                        st.markdown("---")
                        st.markdown("## 🏷️ Error Tagging & Annotation Tool")
                        st.markdown("Manually tag messages for your linguistic study. The table below is interactive.")
                        
                        # Prepare tagging dataframe
                        tagging_df = error_df[['Date', 'User', 'Original Text']].copy()
                        tagging_df['Error Type'] = "None"
                        tagging_df['Notes'] = ""
                        
                        categories = ["None", "Grammar", "Vocabulary", "Code-mixing", "Pragmatic error", "Spelling", "Other"]
                        
                        edited_df = st.data_editor(
                            tagging_df,
                            column_config={
                                "Error Type": st.column_config.SelectboxColumn(
                                    "Error Type",
                                    help="Select the category of the linguistic error",
                                    width="medium",
                                    options=categories,
                                ),
                                "Notes": st.column_config.TextColumn(
                                    "Notes",
                                    help="Add manual notes or corrections",
                                    width="large",
                                ),
                            },
                            hide_index=True,
                            use_container_width=True,
                            num_rows="dynamic"
                        )
                        
                        # Download button for annotated data
                        csv_annotated = edited_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📋 Download Annotated Dataset (CSV)",
                            data=csv_annotated,
                            file_name=f"annotated_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
                    else:
                        st.warning("LanguageTool is not available or failed to initialize. Please check requirements.")
                except Exception as e:
                    st.error(f"Error during linguistic analysis: {e}")

                # 13. Message Search Tool (New Interactive Feature)
                st.markdown("---")
                st.markdown("## 🔎 Search Messages")
                st.markdown("Search for specific keywords or phrases in the chat history")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_query = st.text_input(
                        "Enter search term",
                        placeholder="Type a word or phrase to search...",
                        help="Search through all messages"
                    )
                with col2:
                    search_user = st.selectbox(
                        "Filter by user",
                        ['All'] + [u for u in sorted(df['user'].unique()) if u not in ['System', 'group_notification']],
                        key="search_user"
                    )
                
                if search_query:
                    # Filter messages
                    search_df = df.copy()
                    
                    # Apply user filter if selected
                    if search_user != 'All':
                        search_df = search_df[search_df['user'] == search_user]
                    
                    # Search in messages (case-insensitive)
                    mask = search_df['message'].str.contains(search_query, case=False, na=False)
                    results = search_df[mask]
                    
                    if len(results) > 0:
                        st.success(f"Found {len(results)} matching message(s)")
                        
                        # Display results with pagination
                        page_size = st.selectbox("Results per page", [10, 20, 50, 100], index=1)
                        total_pages = (len(results) - 1) // page_size + 1
                        
                        if total_pages > 1:
                            page = st.slider("Page", 1, total_pages, 1)
                            start_idx = (page - 1) * page_size
                            end_idx = start_idx + page_size
                            page_results = results.iloc[start_idx:end_idx]
                        else:
                            page_results = results
                        
                        # Highlight search term
                        def highlight_term(msg):
                            import re
                            pattern = re.compile(re.escape(search_query), re.IGNORECASE)
                            return pattern.sub(lambda m: f'<mark style="background-color: yellow; padding: 2px;">{m.group()}</mark>', str(msg))
                        
                        for idx, row in page_results.iterrows():
                            highlighted_msg = highlight_term(row['message'])
                            st.markdown(
                                f"""<div class="feature-card" style="margin-bottom: 10px;">
                                    <small><b>{row['user']}</b> | {row['date'].strftime('%d/%m/%y %I:%M %p')}</small><br>
                                    {highlighted_msg}
                                </div>""",
                                unsafe_allow_html=True
                            )
                        
                        # Download search results
                        csv_results = results.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📥 Download {len(results)} Search Results (CSV)",
                            data=csv_results,
                            file_name=f"search_results_{search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info(f"No messages found containing '{search_query}'")

                # Final progress update
                progress_bar.progress(100)
                status_text.text("✅ Analysis Complete!")
                
                # Clear progress indicators after a delay
                st.empty()
                progress_bar.empty()
                status_text.empty()

                # Download section
                st.markdown("---")
                st.markdown("## 📥 Download Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Download processed data as CSV
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📊 Download Processed Data (CSV)",
                        data=csv_data,
                        file_name=f"whatsapp_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Generate and download summary report
                    report = f"""WHATSAPP CHAT ANALYSIS REPORT
================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User Analyzed: {selected_user}

STATISTICS
----------
Total Messages: {num:,}
Total Words: {words:,}
Media Shared: {media}
Links Shared: {links}
Average Words/Message: {avg_words:.1f}
Media Percentage: {media_pct:.1f}%

ACTIVITY SUMMARY
---------------
Most Active Day: {most_day}
Most Active Month: {most_month}
Total Conversation Days: {days}

CONTENT ANALYSIS
---------------
Text Messages: {text_msg:,}
Media Messages: {media}
Links Shared: {links}

Top 5 Users (Overall):
"""
                    
                    if selected_user == 'Overall':
                        top_users_list = df['user'].value_counts().head(5)
                        for user, count in top_users_list.items():
                            report += f"  • {user}: {count} messages ({count/len(df)*100:.1f}%)\n"
                    
                    report += """
================================
End of Report
"""
                    
                    st.download_button(
                        label="📄 Download Report (TXT)",
                        data=report,
                        file_name=f"whatsapp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col3:
                    # Download emoji summary if available
                    if not emoji_df.empty:
                        emoji_csv = emoji_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="😊 Download Emoji Data (CSV)",
                            data=emoji_csv,
                            file_name=f"emoji_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info("No emoji data to download")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.exception(e)  # This will show the full error trace for debugging
        st.info("Please check your file format and try again. Make sure the file is a valid WhatsApp chat export.")

else:
    # Welcome screen when no file is uploaded
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image("https://img.icons8.com/clouds/400/000000/whatsapp.png", width=300)
    
    with col2:
        st.markdown("""
        <div style="padding: 2rem;">
            <h2 style="color: #25D366;">🚀 Get Started</h2>
            <p style="font-size: 1.2rem;">Upload your WhatsApp chat export to unlock powerful insights:</p>
            <ul style="font-size: 1.1rem; line-height: 2;">
                <li>📊 Message statistics and trends</li>
                <li>📅 Activity timelines and patterns</li>
                <li>🔥 Interactive heatmaps</li>
                <li>👥 User participation analysis</li>
                <li>☁️ Word clouds and text analysis</li>
                <li>😊 Emoji usage tracking</li>
                <li>📏 Message length distribution</li>
                <li>💬 Conversation flow analysis</li>
            </ul>
            <div class="info-box">
                <strong>💡 Tip:</strong> Export your chat without media for best results!<br>
                <strong>📌 Supports both formats:</strong><br>
                • 05/09/25, 10:21 am - Message<br>
                • 14/07/25, 12:30 - Message<br>
                <br>
                <strong>📊 Sample Data:</strong> Your uploaded files show this works with real WhatsApp exports!
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show sample preview of what's supported
    st.markdown("---")
    st.markdown("### 📋 Supported Chat Format Examples")
    
    sample_data = pd.DataFrame({
        'Format': ['With AM/PM', '24-hour', 'With Special Characters'],
        'Example': [
            '05/09/25, 10:21 am - Silky Di: <Media omitted>',
            '14/07/25, 12:30 - Sneha Ma\'am MU added you',
            '27/08/24, 19:32 - ~ Lucky porwal created group "B_tech, mechanical 2st sem English"'
        ]
    })
    
    st.dataframe(sample_data, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>Made with ❤️ using Streamlit | WhatsApp Chat Analyzer v2.0</p>
    <p>© 2024 - All rights reserved</p>
</div>
""", unsafe_allow_html=True)
