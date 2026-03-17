import re
import pandas as pd
from datetime import datetime

def preprocess(data):
    """
    Preprocess WhatsApp chat data – supports:
      1) 05/09/25, 10:21 am - Message
      2) 14/07/25, 12:30 - Message
      3) 27/08/24, 19:32 - ~ Lucky porwal created group
    """
    lines = data.strip().split('\n')
    dates = []
    users = []
    messages = []

    # Patterns to match the beginning of a chat line
    date_patterns = [
        # with AM/PM and possible special space
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})[ \s]?([APap][Mm]?)?\s-\s(.*)$',
        # without AM/PM
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s(.*)$',
        # with special characters in username
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s(.+?):\s(.*)$'
    ]

    current_message = ""
    current_date = None
    current_user = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        matched = False
        for pattern in date_patterns:
            match = re.match(pattern, line)
            if match:
                # Save previous message if any
                if current_message and current_date:
                    dates.append(current_date)
                    users.append(current_user)
                    messages.append(current_message.strip())

                groups = match.groups()
                
                # Handle different pattern structures
                if len(groups) == 4:  # Pattern with user and message
                    date_str = f"{groups[0]}, {groups[1]}"
                    if groups[2]:  # AM/PM present
                        date_str += f" {groups[2]}"
                    message_part = groups[3]
                elif len(groups) == 3:  # Pattern without AM/PM
                    date_str = f"{groups[0]}, {groups[1]}"
                    message_part = groups[2]
                else:
                    continue

                # Clean possible special space
                date_str = re.sub(r'[ ]', ' ', date_str)

                # Try different date formats
                date = None
                date_formats = [
                    '%d/%m/%y, %I:%M %p',
                    '%d/%m/%Y, %I:%M %p',
                    '%d/%m/%y, %H:%M',
                    '%d/%m/%Y, %H:%M',
                ]
                for fmt in date_formats:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue

                if date:
                    current_date = date

                    # Extract user and message
                    if ': ' in message_part:
                        user, msg = message_part.split(': ', 1)
                        current_user = user.strip()
                        current_message = msg.strip()
                    else:
                        # System message
                        msg_lower = message_part.lower()
                        if any(word in msg_lower for word in
                               ['added', 'created', 'changed', 'left', 'joined',
                                'group', 'icon', 'deleted', 'messages and calls']):
                            current_user = "System"
                        else:
                            current_user = "System"
                        current_message = message_part

                    matched = True
                    break

        if not matched and current_message:
            # Continuation of previous message
            current_message += "\n" + line

    # Append the last message
    if current_message and current_date:
        dates.append(current_date)
        users.append(current_user)
        messages.append(current_message.strip())

    if len(dates) == 0:
        return pd.DataFrame()

    df = pd.DataFrame({
        'date': dates,
        'user': users,
        'message': messages
    })

    # Remove system messages for cleaner analysis
    df = df[~df['user'].str.contains('System', na=False)]
    
    # Reset index
    df = df.reset_index(drop=True)
    
    # Add time-based columns
    df = add_time_columns(df)
    return df

def add_time_columns(df):
    """Add time-based columns for analysis"""
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month_name()
    df["month_num"] = df["date"].dt.month
    df["only_date"] = df["date"].dt.date
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute

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
