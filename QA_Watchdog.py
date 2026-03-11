import pandas as pd
import matplotlib
matplotlib.use('Agg') # <-- ADD THIS LINE! Tells Python to draw silently in the background
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage
import time
import os
import os
import sys

# 🔥 THIS MAKES IT DOUBLE-CLICK PROOF:
# It tells Python: "Change your working directory to the exact folder where this script is saved."
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
from datetime import date
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage
import time
import os
from datetime import date
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
DATA_FOLDER = '2025_Production_Data'
ARCHIVE_FOLDER = 'SPC_Chart_Archives_2025'
HISTORICAL_FILE = f'{DATA_FOLDER}/historical_buns_rejects_3months.csv'
MONTHLY_FILE = f'{DATA_FOLDER}/March_2025.csv'

# We track this so we don't spam the Plant Manager with 10 emails if the encoder hits save 10 times!
last_email_sent_date = None  

def generate_spc_and_email():
    global last_email_sent_date
    today_str = str(date.today()) # Gets your computer's date (e.g., 2026-03-11)
    
    print(f"\n[{time.strftime('%H:%M:%S')}] File change detected! Analyzing data...")

    try:
        # 1. Read the Data
        df_history = pd.read_csv(HISTORICAL_FILE)
        df_month = pd.read_csv(MONTHLY_FILE)

        # 🔥 BULLETPROOF FIX: Force Excel's date column into standard Python dates
        df_month['Date'] = pd.to_datetime(df_month['Date']).dt.date
        today_date_obj = pd.to_datetime(today_str).date()

        # 2. Check if the encoder actually entered data for TODAY
        last_row = df_month.iloc[-1] # Grabs the very bottom row
        csv_bottom_date = last_row['Date']
        
        print(f"DEBUG -> System Clock Today: {today_date_obj}")
        print(f"DEBUG -> CSV Bottom Row Date: {csv_bottom_date}")

        if csv_bottom_date != today_date_obj:
            print("Data saved, but the bottom row is not today's date. Going back to sleep...")
            return

        if last_email_sent_date == today_str:
            print("Already sent the SPC chart for today! Ignoring this save. Going back to sleep...")
            return

        # 3. Calculate SPC Limits
        target_defect = 'Burnt'
        historical_mean = df_history[target_defect].mean()
        historical_std = df_history[target_defect].std()
        UCL = historical_mean + (3 * historical_std)
        today_value = last_row[target_defect]

        # 4. Draw the Chart
        plt.figure(figsize=(10, 5))
        recent_dates = list(df_history.tail(10)['Date']) + list(df_month['Date'].astype(str))
        recent_values = list(df_history.tail(10)[target_defect]) + list(df_month[target_defect])

        plt.plot(recent_dates, recent_values, marker='o', color='blue')
        
        if today_value > UCL:
            plt.plot(str(csv_bottom_date), today_value, marker='o', markersize=12, color='red')

        plt.axhline(historical_mean, color='green', linestyle='--', label=f'Mean ({historical_mean:.0f})')
        plt.axhline(UCL, color='red', linestyle='-', label=f'UCL ({UCL:.0f})')
        plt.title(f'QA Daily Alert: SPC Chart for {target_defect} Buns')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        # 5. Save the Chart to Archive
        chart_filename = f'{ARCHIVE_FOLDER}/SPC_{target_defect}_{today_str}.png'
        plt.savefig(chart_filename)
        plt.close()

        print(f"Chart saved! Sending email...")

        # 6. Send the Email (Make sure your email/password are still correct here!)
        SENDER_EMAIL = "panadero.jovitpaul@gmail.com" 
        APP_PASSWORD = "lugofavilrsqbwzl" 
        RECEIVER_EMAIL = "jpaulmagadan@gmail.com" 

        msg = EmailMessage()
        msg['Subject'] = f"QA Shift Report: SPC Chart for {today_str}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg.set_content(f"Shift completed.\nToday's '{target_defect}' defect count: {today_value}\nUpper Control Limit: {UCL:.1f}\n\nPlease see the attached SPC chart.")

        with open(chart_filename, 'rb') as img:
            msg.add_attachment(img.read(), maintype='image', subtype='png', filename=f'SPC_{today_str}.png')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        
        print("✅ SUCCESS! Email sent to Plant Manager.")
        last_email_sent_date = today_str 

    except Exception as e:
        print(f"❌ Error processing data: {e}")
# --- THE WATCHDOG (Security Guard) ---
class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # We only care if they save the March_2025.csv file
        if "March_2025.csv" in event.src_path:
            # Wait 2 seconds to let Excel finish saving the file completely
            time.sleep(2) 
            generate_spc_and_email()

print("🛡️ QA Watchdog is now running...")
print(f"Watching folder: {DATA_FOLDER}")
print("Waiting for encoders to save data. Press Ctrl+C to stop.")

observer = Observer()
# Tell the observer to watch the 2025_Production_Data folder
observer.schedule(MyHandler(), path=DATA_FOLDER, recursive=False)
observer.start()
try:
    while True:
        time.sleep(1) # Keeps the script running forever
except KeyboardInterrupt:
    print("\nStopping the Watchdog...")
    observer.stop()
except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    input("Press Enter to close this window...") # Keeps the black box open so you can read the error!

observer.join()

