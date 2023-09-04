import tkinter as tk
from tkinter import ttk
import winsound
from datetime import datetime
import json
import pandas as pd
import re

class CountdownTimer:
    def __init__(self, root): # Initialize the CountdownTimer class
        self.root = root # Root window for the tkinter application
        self.root.protocol('WM_DELETE_WINDOW', self.destroy_root)
        self.root.title("Countdown Timer")

        self.running = False # A flag to indicate if the timer is running
        # Load records for the last day worked before today and if there's any data logged for today 
        self.records_file = 'records.csv'
        self.load_config_data_from_file()
        self.today_recorded, self.last_worked_recorded = self.get_last_records()

        # initialize session parameters
        self.session_completed = 0
        self.session_already_counted = 0

        # initialize a variable to know if the settings are already opened
        self.child_window = False
        
        # Contents of the left frame
        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20)

        # Countdown timer
        self.label_countdown_timer = tk.Label(self.left_frame, font=("Helvetica", 48))
        self.label_countdown_timer.grid(row=0, column=0, padx=10, pady=10)

        # Contents of the right frame
        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20)
        # accumulated today, progress bar, daily goal and yesterday's accumulated
        self.label_accumulated = tk.Label(self.right_frame, font=("Helvetica", 48))
        self.label_accumulated.grid(row=0, column=0, padx=10, pady=10)
        self.progress_bar_max_size = 100
        self.progress_bar = ttk.Progressbar(self.right_frame, orient="horizontal", length=self.progress_bar_max_size, mode="determinate")
        self.progress_bar.grid(row=1, column=0, padx=10, pady=10)
        self.label_goal = tk.Label(self.right_frame, font=("Helvetica", 18))
        self.label_goal.grid(row=2, column=0, padx=10, pady=10)
        self.label_yesterday = tk.Label(self.right_frame, font=("Helvetica", 18))
        self.label_yesterday.grid(row=3, column=0, padx=10, pady=10)

        # Contents of the bottom frame
        self.bottom_frame = tk.Frame(self.left_frame)
        self.bottom_frame.grid(row=1, column=0, padx=20, pady=20)

        # Create start, pause, reset, and settings buttons with associated images and commands
        self.start_img = tk.PhotoImage(file="images\\start.png")
        self.button_start = tk.Button(self.bottom_frame, image=self.start_img, command=self.start_timer)
        self.button_start.grid(row=0, column=0, padx=5, pady=5)
        self.pause_img = tk.PhotoImage(file="images\\pause.png")
        self.button_pause = tk.Button(self.bottom_frame, image=self.pause_img, command=self.pause_timer)
        self.button_pause.grid(row=0, column=1, padx=5, pady=5)
        self.button_pause["state"] = "disable"

        self.reset_img = tk.PhotoImage(file="images\\reset.png")
        self.button_reset = tk.Button(self.bottom_frame, image=self.reset_img, command=self.reset_timer)
        self.button_reset.grid(row=0, column=2, padx=5, pady=5)

        self.settings_img = tk.PhotoImage(file="images\\settings.png")
        self.button_settings = tk.Button(self.bottom_frame, image=self.settings_img, command=self.open_settings)
        self.button_settings.grid(row=0, column=4, padx=5, pady=5)

        self.reset_UI()


    def destroy_root(self):
        self.pause_timer()
        self.root.destroy()


    def reset_UI(self):
        # reset the countdown timer label
        minutes, seconds = divmod(self.countdown_from, 60)
        self.label_countdown_timer.config(text="{:02}:{:02}".format(minutes, seconds))
        
        # reset the accumulated today label
        hours, rest = divmod(self.today_recorded, 3600)
        minutes, _ = divmod(rest, 60)
        self.label_accumulated.config(text="{:02}h:{:02}".format(hours, minutes))

        # reset the progress bar
        self.progress_bar["value"] = self.progress_bar_max_size*self.today_recorded/self.daily_goal

        # reset the accumulated yesterday label
        hours, rest = divmod(self.last_worked_recorded, 3600)
        minutes, _ = divmod(rest, 60)
        self.label_yesterday.config(text="Yesterday {:02}h:{:02}".format(hours, minutes))

        # reset the goal label
        hours, rest = divmod(self.daily_goal, 3600)
        minutes, _ = divmod(rest, 60)
        self.label_goal.config(text="Goal {:02}h:{:02}".format(hours, minutes))


    def set_new_day_in_records(self):
        df = pd.read_csv('records.csv', names=['datetime', 'value'])
        new_row = {'datetime': datetime.now().strftime('%d-%m-%Y %H:%M'), 'value': 0}
        df = pd.concat((df, pd.DataFrame(new_row, index=[0])), ignore_index = True)
        df.reset_index()
        df.to_csv('records.csv', index=False, header=False)


    def update_last_record(self):
        df = pd.read_csv('records.csv', names=['datetime', 'value'])
        # Get the last entry from the DataFrame
        df.loc[df['datetime'] == df.iloc[-1]['datetime'], 'value'] = self.today_recorded
        df.to_csv('records.csv', index=False, header=False)


    def get_last_records(self):
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv('records.csv', names=['datetime', 'value'])
        # Convert the 'datetime' column to datetime objects
        df['datetime'] = pd.to_datetime(df['datetime'], format='%d-%m-%Y %H:%M')

        # Get the last entry from the DataFrame
        last_entry = df.iloc[-1]

        # Get today's date
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Check if the last entry is for today
        if last_entry['datetime'].date() == today.date():
            # Filter entries for today and the day before
            today_entries = df[df['datetime'].dt.date == today.date()]
            last_worked_day_entry = df.iloc[-2]

            # return the entries for today and yesterday
            return int(today_entries['value']), int(last_worked_day_entry['value']) 
        else:
            self.set_new_day_in_records()
            return 0, int(last_entry['value'])


    def load_config_data_from_file(self):
        with open('config.json', 'r') as fp:
            data = json.load(fp)

        self.countdown_from = data.get('countdown_from')
        self.daily_goal = data.get('daily_goal')


    def save_config_data_to_file(self):
        data = {
            'countdown_from': self.countdown_from,
            'daily_goal': self.daily_goal,
            }
        with open('config.json', 'w') as f:
            json.dump(data, f)


    def start_timer(self):
        self.running = True
        
        # Disable start & reset and enable pause button
        self.button_start["state"] = "disable"
        self.button_reset["state"] = "disable"
        self.button_pause["state"] = "normal"
        
        self.countdown()


    def pause_timer(self):
        self.running = False

        # Update accumulated time label & progress bar and the csv record for today
        self.update_daily_elapsed()
        
        # Disable pause and enable start & reset button
        self.button_start["state"] = "normal"
        self.button_reset["state"] = "normal"
        self.button_pause["state"] = "disable"
        

    def reset_timer(self):

        # Set countdown to default
        self.reset_UI()
        # Disable pause and enable start & reset button
        self.button_start["state"] = "normal"
        self.button_reset["state"] = "normal"
        self.button_pause["state"] = "disable"


    def update_daily_elapsed(self):
        # reset the accumulated today label
        to_count = self.session_completed - self.session_already_counted
        self.session_already_counted = self.session_completed
        self.today_recorded += to_count
        hours, rest = divmod(self.today_recorded, 3600)
        minutes, _ = divmod(rest, 60)
        self.label_accumulated.config(text="{:02}h:{:02}".format(hours, minutes))

        # reset the progress bar
        self.progress_bar["value"] = self.progress_bar_max_size*self.today_recorded/self.daily_goal

        # update the csv file
        self.update_last_record()


    def update_session_elapsed(self):
        minutes, seconds = divmod(self.countdown_from - self.session_completed, 60)
        self.label_countdown_timer.config(text="{:02}:{:02}".format(minutes, seconds))


    def open_settings(self):
        if not self.child_window:
            self.child_window = True
            self.pause_timer()

            self.settings_window = tk.Toplevel(self.root)
            self.settings_window.protocol('WM_DELETE_WINDOW', self.destroy_settings)
            self.settings_window.title("Settings")

            # Contents of the left frame
            self.main_frame = tk.Frame(self.settings_window)
            self.main_frame.grid(row=0, column=0, padx=0, pady=0)

            # Create a label to display the validation result
            result_label = tk.Label(self.main_frame, text="", font=("Helvetica", 12))
            result_label.grid(row=0, column=0, padx=5, pady=5)

            label_daily_goal = tk.Label(self.main_frame, text="Daily Goal (HH:MM)")
            label_daily_goal.grid(row=1, column=0, padx=5, pady=5)

            entry_daily_goal = tk.Entry(self.main_frame)
            hours,rest = divmod(self.daily_goal,3600)
            minutes,seconds = divmod(rest,60)
            entry_daily_goal.insert(0, "{:02}:{:02}".format(hours, minutes))
            entry_daily_goal.grid(row=2, column=0, padx=5, pady=5)

            label_countdown_from = tk.Label(self.main_frame, text="Countdown from (MM:SS)")
            label_countdown_from.grid(row=3, column=0, padx=5, pady=5)

            entry_countdown_from = tk.Entry(self.main_frame)
            minutes,seconds = divmod(self.countdown_from,60)
            entry_countdown_from.insert(0, "{:02}:{:02}".format(minutes, seconds))
            entry_countdown_from.grid(row=4, column=0, padx=5, pady=5)

            button_save = tk.Button(self.main_frame, text="Save", 
                                    command=lambda: self.save_settings(entry_daily_goal.get(), entry_countdown_from.get(), 
                                                                    result_label))
            button_save.grid(row=5, column=0, padx=5, pady=5)
        else:
            self.settings_window.lift()


    def validate_time_entry(self, input_text):
        # Regular expression pattern for HH (0-99) and MM (0-59)
        pattern = r'^(?:[0-9]|[0-9][0-9]):[0-5]\d$'
        return re.match(pattern, input_text) is not None


    def save_settings(self, daily_goal, countdown_from, result_label):
        if self.validate_time_entry(daily_goal) and self.validate_time_entry(countdown_from):
            result_label.config(text="Values updated", fg="green")
        else:
            result_label.config(text="Invalid time format, accept only (0-99:0-59)", fg="red")

        h,m = daily_goal.split(':')
        self.daily_goal = int(h)*3600 + int(m)*60
        m,s = countdown_from.split(':')
        self.countdown_from = int(m)*60 + int(s)
        self.save_config_data_to_file()
        self.reset_timer()


    def destroy_settings(self):
        self.child_window = False
        self.settings_window.destroy()


    def countdown(self):
        if self.running and (self.countdown_from - self.session_completed > 0):
            self.session_completed += 1
            self.update_session_elapsed()
            self.root.after(1000, self.countdown)
        elif self.running and self.session_completed >= self.countdown_from:
            # update the daily elapsed
            self.pause_timer()
            # enable reset and disable start & pause button
            self.button_start["state"] = "disable"
            self.button_reset["state"] = "normal"
            self.button_pause["state"] = "disable"

            self.session_completed = 0
            self.session_already_counted = 0

            self.root.focus_force()
            self.root.lift()
            self.label_countdown_timer.config(text="Time's up!")
            winsound.Beep(1000, 1000)
            self.running = False





if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownTimer(root)
    root.mainloop()
