import re
import pandas as pd
from datetime import datetime

def preprocess(data):
    """
    Preprocess WhatsApp chat data - handles both formats:
    1. 24-hour with AM/PM: 05/09/25, 10:21 am - Message
    2. 24-hour without AM/PM: 14/07/25, 12:30 - Message
    """
    
    # Try multiple patterns
    patterns = [
        # Format 1: With AM/PM and special space character
        r'(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})[ \s]?([APap][Mm]?)?\s-\s',
        
        # Format 2: Without AM/PM (your first file format)
        r'(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s',
        
        # Alternative patterns
        r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\]\s',
        r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}:\s'
    ]
    
    lines = data.strip().split('\n')
    dates = []
    messages = []
    users = []
    texts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        matched = False
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                # Extract date part and message part
                date_part = match.group(0).strip()
                message_part = line[len(date_part):].strip()
                
                # Clean date part
                date_part = re.sub(r'[ ]', ' ', date_part)  # Replace special space
                date_part = date_part.replace(' - ', '').strip()
                
                # Parse date
                try:
                    # Try different date formats
                    date = None
                    
                    # Try with AM/PM
                    if 'am' in date_part.lower() or 'pm' in date_part.lower():
                        # Remove any special characters
                        date_clean = re.sub(r'[ ]', ' ', date_part)
                        date_formats = [
                            '%d/%m/%y, %I:%M %p',
                            '%d/%m/%Y, %I:%M %p',
                            '%d/%m/%y, %I:%M%p',
                            '%d/%m/%Y, %I:%M%p'
                        ]
                        for fmt in date_formats:
                            try:
                                date = datetime.strptime(date_clean, fmt)
                                break
                            except:
                                continue
                    
                    # Try without AM/PM (24-hour format)
                    if date is None:
                        date_clean = re.sub(r'[ ]', ' ', date_part)
                        date_formats = [
                            '%d/%m/%y, %H:%M',
                            '%d/%m/%Y, %H:%M',
                            '%d/%m/%y %H:%M',
                            '%d/%m/%Y %H:%M'
                        ]
                        for fmt in date_formats:
                            try:
                                date = datetime.strptime(date_clean, fmt)
                                break
                            except:
                                continue
                    
                    if date:
                        dates.append(date)
                        
                        # Extract user and message
                        if ': ' in message_part:
                            user, msg = message_part.split(': ', 1)
                            users.append(user.strip())
                            texts.append(msg.strip())
                        else:
                            # System message
                            msg_lower = message_part.lower()
                            if any(word in msg_lower for word in ['added', 'created', 'changed', 'left', 'joined', 'group', 'icon', 'deleted']):
                                users.append("System")
                            else:
                                users.append("System")
                            texts.append(message_part)
                        
                        matched = True
                        break
                except:
                    continue
        
        if not matched:
            # Handle multi-line messages (append to last message)
            if dates and texts:
                texts[-1] = texts[-1] + "\n" + line
    
    if len(dates) == 0:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'user': users,
        'message': texts
    })
    
    # Add time-based columns
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
    
    # Add period column for heatmap
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
