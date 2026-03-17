import re
import pandas as pd

def preprocess(data):
    """
    Preprocess WhatsApp chat data supporting both 12-hour and 24-hour time formats
    """
    
    # Try multiple date-time patterns
    patterns = [
        # 12-hour format with AM/PM
        r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APap][Mm]\s-\s',
        # 24-hour format
        r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s',
        # Alternative formats
        r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\]\s',
        r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}:\s'
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
    
    # If no pattern matched, return empty DataFrame
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    # Try to parse dates with different formats
    date_formats = [
        '%d/%m/%y, %H:%M - ',        # 24-hour: 13/03/22, 20:30 - 
        '%d/%m/%Y, %H:%M - ',        # 24-hour with 4-digit year
        '%d/%m/%y, %I:%M %p - ',     # 12-hour: 13/03/22, 8:30 PM - 
        '%d/%m/%Y, %I:%M %p - ',     # 12-hour with 4-digit year
        '[%d/%m/%y, %H:%M:%S] ',     # Alternative format with seconds
        '%Y-%m-%d %H:%M:%S: '        # ISO format
    ]
    
    # Try each date format
    for fmt in date_formats:
        try:
            df["date"] = pd.to_datetime(
                df["date"],
                format=fmt,
                errors="coerce"
            )
            # If we got valid dates, break
            if df["date"].notna().any():
                break
        except:
            continue
    
    # If still no valid dates, let pandas infer the format (new recommended approach)
    if df["date"].isna().all():
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['date'])
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Extract user and message
    users = []
    texts = []
    
    for msg in df["user_message"]:
        # Pattern for "user: message"
        split = re.split(r"^([^:]+):\s", msg)
        if len(split) > 2:
            users.append(split[1])
            texts.append(split[2])
        else:
            users.append("group_notification")
            texts.append(msg)
    
    df["user"] = users
    df["message"] = pd.Series(texts).astype(str)
    df.drop(columns=["user_message"], inplace=True)
    
    # Add time-based columns
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month_name()
    df["month_num"] = df["date"].dt.month
    df["only_date"] = df["date"].dt.date
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    
    # Add period column for heatmap
    def get_period(hour):
        if hour >= 0 and hour < 4:
            return 'Late Night (0-4)'
        elif hour >= 4 and hour < 8:
            return 'Early Morning (4-8)'
        elif hour >= 8 and hour < 12:
            return 'Morning (8-12)'
        elif hour >= 12 and hour < 16:
            return 'Afternoon (12-16)'
        elif hour >= 16 and hour < 20:
            return 'Evening (16-20)'
        else:
            return 'Night (20-24)'
    
    df['period'] = df['hour'].apply(get_period)
    
    return df
