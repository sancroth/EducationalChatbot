date_obj = datetime.strptime(slot_value, "%d/%m/%Y")

today = datetime.today()

min_date = today + 1
max_date = today + timedelta(days=30)

# Check if the date is within the range
if date_obj <= min_date <= max_date: