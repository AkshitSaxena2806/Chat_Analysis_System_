import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import Chat_Analysis
import helper
import zipfile
import os
from pathlib import Path
import tempfile

st.set_page_config(page_title="Chat Analysis System", layout="wide")

st.sidebar.title("Chat Analysis")

# Add option for single file or zip file upload
upload_option = st.sidebar.radio("Choose upload type:", ["Single Text File", "Zip File"])

uploaded_file = None
uploaded_zip = None

if upload_option == "Single Text File":
    uploaded_file = st.sidebar.file_uploader("Upload WhatsApp chat (.txt)", type="txt")
else:
    uploaded_zip = st.sidebar.file_uploader("Upload Zip file containing WhatsApp chats", type="zip")

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
            # Extract all files
            z.extractall(tmpdir)
            
            # Find all .txt files
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
        # Combine all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        return combined_df, errors
    else:
        return None, errors

# Main processing logic
if uploaded_file or uploaded_zip:
    df = None
    errors = None
    
    if uploaded_file:
        df, errors = process_chat_file(uploaded_file.getvalue(), uploaded_file.name)
    elif uploaded_zip:
        with st.spinner("Processing zip file..."):
            df, errors = process_zip_file(uploaded_zip)
    
    if errors:
        if isinstance(errors, list):
            for error in errors:
                st.warning(error)
        else:
            st.warning(errors)
    
    if df is not None and not df.empty:
        # Get unique users
        users = df["user"].unique().tolist()
        if "group_notification" in users:
            users.remove("group_notification")
        
        users.sort()
        users.insert(0, "Overall")
        
        selected_user = st.sidebar.selectbox("Select User", users)
        
        if st.sidebar.button("Show Analysis"):
            st.title("📊 Chat Analysis System")
            
            # Basic Statistics
            num, words, media, links = helper.fetch_stats(selected_user, df)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Messages", num)
            c2.metric("Total Words", words)
            c3.metric("Media Shared", media)
            c4.metric("Links Shared", links)
            
            # Monthly Timeline
            st.subheader("📅 Monthly Timeline")
            mt = helper.monthly_timelines(selected_user, df)
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(mt["time"], mt["message"], color='green', marker='o', linewidth=2)
            plt.xticks(rotation=90)
            plt.xlabel("Time")
            plt.ylabel("Number of Messages")
            plt.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            # Daily Timeline
            st.subheader("📆 Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df) if hasattr(helper, 'daily_timeline') else None
            if daily_timeline is not None:
                fig, ax = plt.subplots(figsize=(15, 6))
                ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black', linewidth=1)
                plt.xticks(rotation=90)
                plt.xlabel("Date")
                plt.ylabel("Number of Messages")
                plt.grid(True, alpha=0.3)
                st.pyplot(fig)
            
            # Activity Map (Weekly and Monthly)
            st.subheader("🗺️ Activity Map")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Most Busy Day**")
                busy_day = helper.week_activity_map(selected_user, df) if hasattr(helper, 'week_activity_map') else None
                if busy_day is not None:
                    fig, ax = plt.subplots()
                    ax.bar(busy_day.index, busy_day.values, color='purple')
                    plt.xticks(rotation=45)
                    plt.xlabel("Day")
                    plt.ylabel("Message Count")
                    st.pyplot(fig)
            
            with col2:
                st.markdown("**Most Busy Month**")
                busy_month = helper.month_activity_map(selected_user, df) if hasattr(helper, 'month_activity_map') else None
                if busy_month is not None:
                    fig, ax = plt.subplots()
                    ax.bar(busy_month.index, busy_month.values, color='orange')
                    plt.xticks(rotation=45)
                    plt.xlabel("Month")
                    plt.ylabel("Message Count")
                    st.pyplot(fig)
            
            # Weekly Activity Heatmap
            st.subheader("🔥 Weekly Activity Heatmap")
            user_heatmap = helper.activity_heatmap(selected_user, df) if hasattr(helper, 'activity_heatmap') else None
            if user_heatmap is not None:
                fig, ax = plt.subplots(figsize=(12, 6))
                sns.heatmap(user_heatmap, cmap='YlOrRd', annot=True, fmt='g', ax=ax)
                plt.xlabel("Period")
                plt.ylabel("Day")
                st.pyplot(fig)
            
            # Weekly Activity (Bar Chart) - Your existing
            st.subheader("📊 Weekly Activity")
            wd = helper.day_timelines(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(wd["day_name"], wd["message"], color='skyblue')
            plt.xticks(rotation=45)
            plt.xlabel("Day")
            plt.ylabel("Message Count")
            st.pyplot(fig)
            
            # Most Busy Users (Group Level)
            if selected_user == 'Overall':
                st.subheader("👥 Most Busy Users")
                x, new_df = helper.most_busy_users(df)
                col1, col2 = st.columns(2)
                
                with col1:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.bar(x.index, x.values, color='red')
                    plt.xticks(rotation=90)
                    plt.xlabel("Users")
                    plt.ylabel("Message Count")
                    st.pyplot(fig)
                
                with col2:
                    st.dataframe(new_df, use_container_width=True)
            
            # Word Cloud
            st.subheader("☁️ Word Cloud")
            wc = helper.workcloud(selected_user, df)
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(wc)
            ax.axis("off")
            st.pyplot(fig)
            
            # Most Common Words
            st.subheader("📝 Most Common Words")
            most_common_df = helper.most_common_words(selected_user, df) if hasattr(helper, 'most_common_words') else None
            if most_common_df is not None:
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.barh(most_common_df[0][:20], most_common_df[1][:20], color='teal')
                plt.xlabel("Frequency")
                plt.ylabel("Words")
                plt.gca().invert_yaxis()
                st.pyplot(fig)
            
            # Emoji Analysis
            st.subheader("😊 Emoji Analysis")
            col1, col2 = st.columns(2)
            
            emoji_df = helper.emojies(selected_user, df)
            
            with col1:
                st.dataframe(emoji_df, use_container_width=True)
            
            with col2:
                if not emoji_df.empty:
                    fig, ax = plt.subplots()
                    # Show top 5 emojis in pie chart
                    top_emojis = emoji_df.head(5)
                    ax.pie(top_emojis[top_emojis.columns[1]], 
                          labels=top_emojis[top_emojis.columns[0]], 
                          autopct="%0.2f%%")
                    st.pyplot(fig)

    elif df is None and not errors:
        st.error("Could not process the file(s). Please check the format.")
else:
    st.info("👈 Please upload a WhatsApp chat file (.txt) or a zip file containing chat files to begin analysis.")
    
    # Instructions
    with st.expander("📖 How to export WhatsApp chat"):
        st.markdown("""
        ### Export WhatsApp Chat (Without Media)
        
        **Android:**
        1. Open individual or group chat
        2. Tap on three dots (menu) → More → Export Chat
        3. Choose "Without Media"
        4. Save the .txt file
        
        **iPhone:**
        1. Open individual or group chat
        2. Tap on contact name/group subject
        3. Scroll down and tap "Export Chat"
        4. Choose "Without Media"
        5. Save the .txt file
        
        ### Upload Options
        - **Single File**: Upload one .txt file for analysis
        - **Zip File**: Upload multiple chat exports in a zip file for combined analysis
        """)
