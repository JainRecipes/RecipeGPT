from datetime import datetime, timedelta

def adjust_date_with_offset(date_str):
    date_parts = date_str.split()
    offset_hours = int(date_parts[-1]) // 100  # Extracting hours from the offset
    offset_minutes = int(date_parts[-1]) % 100  # Extracting minutes from the offset
    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    
    date_time_str = " ".join(date_parts[1:3])
    date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S") 
    
    if date_parts[-2] != "-":
        adjusted_date = date_time_obj - offset
    else:
        adjusted_date = date_time_obj + offset
    
    return adjusted_date.strftime("%Y-%m-%d %H:%M:%S")

date_str = "date: 2020-05-18 22:33:18 -0500"
adjusted_date = adjust_date_with_offset(date_str)
print(adjusted_date)
