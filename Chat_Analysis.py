import re
import pandas as pd

def preprocess(data):
    """
    Preprocess WhatsApp chat data - specifically for 24-hour format: DD/MM/YY, HH:MM - 
    """
    
    # Your exact pattern (24-hour format, no AM/PM)
    pattern = r'\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2}\s-\s'
    
    # Split the data
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    
    # Check if we got any data
    if len(messages) == 0 or len(dates) == 0:
        # Try alternative pattern (with 4-digit year)
        pattern = r'\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}\s-\s'
        messages = re.split(pattern, data)[1:]
        dates = re.findall(pattern, data)
        
        if len(messages) == 0 or len(dates) == 0:
            return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame({
        "user_message": messages,
        "date": dates
    })
    
    # Clean the date strings
    df['date'] = df['date'].str.strip()
    
    # Parse dates - try different formats
    try:
        # Try with 2-digit year first (your format)
        df["date"] = pd.to_datetime(
            df["date"],
            format="%d/%m/%y, %H:%M - ",
            errors="coerce"
        )
        
        # If that fails, try with 4-digit year
        if df["date"].isna().all():
            df["date"] = pd.to_datetime(
                df["date"],
                format="%d/%m/%Y, %H:%M - ",
                errors="coerce"
            )
    except:
        # If all else fails, let pandas infer
        df["date"] = pd.to_datetime(df["date"], infer_datetime_format=True, errors="coerce")
    
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
            # Clean user name (remove special characters)
            user = split[1].strip()
            user = re.sub(r'[~ ]', '', user)  # Remove special chars
            users.append(user)
            texts.append(split[2].strip())
        else:
            # Check if it's a system message
            msg_lower = msg.lower()
            if any(word in msg_lower for word in ['added', 'created', 'changed', 'left', 'joined', 'group', 'icon']):
                users.append("group_notification")
            else:
                users.append("group_notification")
            texts.append(msg.strip())
    
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
