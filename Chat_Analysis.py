import re
import pandas as pd

def preprocess(data):
    # Android WhatsApp format with AM/PM
    pattern = r"\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2}\s[ap]m\s-\s"

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    if len(messages) == 0:
        return pd.DataFrame()

    df = pd.DataFrame({
        "user_message": messages,
        "date": dates
    })

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d/%m/%y, %I:%M %p - ",
        errors="coerce"
    )

    users = []
    texts = []

    for msg in df["user_message"]:
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

    # Add all necessary columns
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month_name()
    df["month_num"] = df["date"].dt.month
    df["only_date"] = df["date"].dt.date  # Fixed: changed from only_dates to only_date
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    
    # Add period column for heatmap
    def get_period(hour):
        if hour == 23 or hour == 0 or hour == 1:
            return 'Late Night'
        elif hour == 2 or hour == 3 or hour == 4:
            return 'Early Morning'
        elif hour >= 5 and hour <= 11:
            return 'Morning'
        elif hour >= 12 and hour <= 16:
            return 'Afternoon'
        elif hour >= 17 and hour <= 19:
            return 'Evening'
        else:
            return 'Night'
    
    df['period'] = df['hour'].apply(get_period)
    
    return df
