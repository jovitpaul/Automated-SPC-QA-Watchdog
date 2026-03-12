import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, date
import smtplib
from email.message import EmailMessage

print("1. Generating plant data...")
# --- 1. GENERATE THE DATA LOCALLY ON YOUR LAPTOP ---
np.random.seed(42)
categories = ['Underweight', 'Overweight', 'Deformed', 'Burnt', 'Pale', 'Slicing_Defect', 'Poor_Seed', 'Blisters', 'Foreign_Mat', 'Packaging']
avg_rejects = [50, 30, 80, 40, 40, 60, 20, 50, 2, 100]

# Historical Data
dates = pd.date_range(start=date.today() - timedelta(days=89), end=date.today() - timedelta(days=1))
historical_data = []
for d in dates:
    record = {'Date': d.strftime('%Y-%m-%d')}
    for i, cat in enumerate(categories):
        record[cat] = np.random.poisson(avg_rejects[i])
    historical_data.append(record)
df_history = pd.DataFrame(historical_data)

# Today's Data (With the anomaly)
today_record = {'Date': date.today().strftime('%Y-%m-%d')}
for i, cat in enumerate(categories):
    today_record[cat] = 185 if cat == 'Burnt' else np.random.poisson(avg_rejects[i])
df_today = pd.DataFrame([today_record])


print("2. Calculating SPC Limits...")
# --- 2. CALCULATE SPC FOR 'Burnt' BUNS ---
target_defect = 'Burnt'
historical_mean = df_history[target_defect].mean()
historical_std = df_history[target_defect].std()
UCL = historical_mean + (3 * historical_std)
LCL = max(0, historical_mean - (3 * historical_std))

today_value = df_today[target_defect].values[0]


print("3. Drawing and Saving the Chart...")
# --- 3. DRAW AND SAVE THE CHART (Invisibly) ---
plt.figure(figsize=(10, 5))
recent_dates = list(df_history.tail(14)['Date']) + list(df_today['Date'])
recent_values = list(df_history.tail(14)[target_defect]) + list(df_today[target_defect])

plt.plot(recent_dates, recent_values, marker='o', color='blue')
if today_value > UCL:
    plt.plot(df_today['Date'].values[0], today_value, marker='o', markersize=12, color='red')

plt.axhline(historical_mean, color='green', linestyle='--', label=f'Mean ({historical_mean:.0f})')
plt.axhline(UCL, color='red', linestyle='-', label=f'UCL ({UCL:.0f})')
plt.title(f'QA Alert: SPC Chart for {target_defect} Buns')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

# SAVE THE IMAGE TO YOUR DESKTOP FOLDER
chart_filename = 'daily_spc_alert.png'
plt.savefig(chart_filename)
plt.close() # Close it so it doesn't pop up on the screen!


print("4. Sending the Email...")
# --- 4. SEND THE AUTOMATED EMAIL ---

# ⚠️ CHANGE THESE THREE LINES! ⚠️
SENDER_EMAIL = "Your email here" 
APP_PASSWORD = "Your password here" # No spaces!
RECEIVER_EMAIL = "another email here" # You can send it to yourself as a test

# Create the email message
msg = EmailMessage()
msg['Subject'] = f"🚨 QA ALERT: {target_defect} limits exceeded!"
msg['From'] = "Your email here"
msg['To'] = "another email here"
msg.set_content(f"Warning: The {target_defect} defect count today was {today_value}, which exceeds the Upper Control Limit of {UCL:.1f}.\n\nPlease see the attached SPC chart and investigate the production line.")

# Attach the image we just saved
with open(chart_filename, 'rb') as img:
    msg.add_attachment(img.read(), maintype='image', subtype='png', filename=chart_filename)

# Connect to Gmail and Send
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ SUCCESS! Check your email inbox!")
except Exception as e:
    print("❌ Failed to send email. Error:", e)

