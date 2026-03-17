import re
import pandas as pd
from datetime import datetime

def preprocess(data):
    """
    Preprocess WhatsApp chat data - supports multiple formats including 24-hour format
    """
    
    # Try multiple date-time patterns
    patterns = [
        # 24-hour format: 14/07/25, 12:30 - 
        r'\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2}\s-\s',
        # 12-hour format with AM/PM: 14/07/25, 12:30 PM - 
        r'\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2}\s[APap][Mm]\s-\s',
        # With 4-digit year: 14/07/2025, 12:30 - 
        r'\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}\s-\s',
    ]
    
    df = None
    
    # Try each pattern until one works
    for pattern in patterns:
        messages = re.split(pattern, data)[1:]
        dates = re.findall(pattern, data)
        
        if len(messages) > 0 and len(dates) > 0 and len(messages) == len(dates):
            df = pd.DataFrame({
                "user_message": messages,
                "date": dates
            })
            break
    
    # If no pattern matched, try fallback method
    if df is None or len(df) == 0:
        return fallback_preprocess(data)
    
    # Clean dates
    df['date'] = df['date'].str.strip()
    
    # Try to parse dates with different formats
    date_parsed = False
    date_formats = [
        ('%d/%m/%y, %H:%M - ', False),      # 24-hour with 2-digit year
        ('%d/%m/%Y, %H:%M - ', False),      # 24-hour with 4-digit year
        ('%d/%m/%y, %I:%M %p - ', True),    # 12-hour with 2-digit year
        ('%d/%m/%Y, %I:%M %p - ', True),    # 12-hour with 4-digit year
    ]
    
    for fmt, has_ampm in date_formats:
        try:
            df["date"] = pd.to_datetime(
                df["date"],
                format=fmt,
                errors="coerce"
            )
            if df["date"].notna().any():
                date_parsed = True
                break
        except:
            continue
    
    # If still no valid dates, let pandas infer (FIXED: removed infer_datetime_format)
    if not date_parsed or df["date"].isna().all():
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['date'])
    
    if len(df) == 0:
        return fallback_preprocess(data)
    
    # Extract user and message
    users = []
    texts = []
    
    for msg in df["user_message"]:
        # Pattern for "user: message"
        split = re.split(r"^([^:]+):\s", msg)
        if len(split) > 2:
            # Clean user name
            user = split[1].strip()
            user = re.sub(r'[~ @]', '', user)
            users.append(user if user else "unknown")
            texts.append(split[2].strip())
        else:
            # System message
            msg_lower = msg.lower()
            if any(word in msg_lower for word in ['added', 'created', 'changed', 'left', 'joined', 'group', 'icon']):
                users.append("System")
            else:
                users.append("System")
            texts.append(msg.strip())
    
    df["user"] = users
    df["message"] = pd.Series(texts).astype(str)
    df.drop(columns=["user_message"], inplace=True)
    
    # Add time-based columns
    df = add_time_columns(df)
    
    return df

def fallback_preprocess(data):
    """Fallback preprocessing - line by line parsing"""
    lines = data.strip().split('\n')
    
    dates = []
    users = []
    messages = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to find date pattern
        date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?:\s[APap][Mm])?)\s-\s(.*)$', line)
        if date_match:
            date_str = date_match.group(1)
            content = date_match.group(2)
            
            # Parse date
            try:
                if 'PM' in date_str or 'AM' in date_str:
                    date = pd.to_datetime(date_str, format='%d/%m/%y, %I:%M %p', errors='coerce')
                else:
                    date = pd.to_datetime(date_str, format='%d/%m/%y, %H:%M', errors='coerce')
                
                if pd.notna(date):
                    # Extract user if exists
                    if ': ' in content:
                        user, msg = content.split(': ', 1)
                        users.append(user.strip())
                        messages.append(msg.strip())
                    else:
                        users.append("System")
                        messages.append(content)
                    dates.append(date)
            except:
                continue
    
    if len(dates) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame({
        'date': dates,
        'user': users,
        'message': messages
    })
    
    # Add time columns
    df = add_time_columns(df)
    
    return df

def add_time_columns(df):
    """Add time-based columns to dataframe"""
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month_name()
    df["month_num"] = df["date"].dt.month
    df["only_date"] = df["date"].dt.date
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    
    # Add period column for heatmap (using text labels to avoid font issues)
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
    
    df['period'] = df['hour'].apply(get_period)
    
    return df
