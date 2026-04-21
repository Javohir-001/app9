#!/usr/bin/env python3
"""
Pomodoro Timer (Terminal)
A 25/5 minute work-break timer that runs in the terminal, plays a beep sound,
tracks how many pomodoros you've completed, and saves daily stats.
"""

import time
import os
import json
from datetime import datetime, date
from typing import Dict, List
import threading
import sys

STATS_FILE = "pomodoro_stats.json"

class PomodoroTimer:
    def __init__(self, work_duration: int = 25, break_duration: int = 5):
        self.work_duration = work_duration * 60  # Convert to seconds
        self.break_duration = break_duration * 60
        self.current_session = 0
        self.total_pomodoros_today = 0
        self.stats = self.load_stats()
        self.running = False
        self.paused = False
        self.start_time = None
        self.paused_time = 0
        self.session_type = "work"  # "work" or "break"
        
    def load_stats(self) -> Dict:
        """Load pomodoro statistics from file."""
        if not os.path.exists(STATS_FILE):
            return {}
        
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_stats(self) -> None:
        """Save pomodoro statistics to file."""
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def get_today_stats(self) -> Dict:
        """Get or create today's statistics."""
        today = date.today().isoformat()
        
        if today not in self.stats:
            self.stats[today] = {
                'pomodoros_completed': 0,
                'total_work_time': 0,
                'total_break_time': 0,
                'sessions': []
            }
        
        return self.stats[today]
    
    def update_stats(self, session_type: str, duration: int) -> None:
        """Update statistics after a session."""
        today_stats = self.get_today_stats()
        
        if session_type == "work":
            today_stats['pomodoros_completed'] += 1
            today_stats['total_work_time'] += duration
            self.total_pomodoros_today += 1
        else:
            today_stats['total_break_time'] += duration
        
        # Add session record
        session_record = {
            'type': session_type,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        today_stats['sessions'].append(session_record)
        
        self.save_stats()
    
    def play_beep(self, count: int = 3) -> None:
        """Play beep sound to signal session end."""
        try:
            for _ in range(count):
                # Try different methods for beep sound
                if sys.platform == "win32":
                    import winsound
                    winsound.Beep(1000, 500)  # Frequency, Duration in ms
                elif sys.platform == "darwin":
                    os.system('afplay /System/Library/Sounds/Ping.aiff')
                else:
                    # Linux/Unix
                    os.system('echo -e "\a"')
                    time.sleep(0.5)
                
                if count > 1:
                    time.sleep(0.3)
        except Exception:
            # Fallback: print visual notification
            print("\a" * count)  # Bell character
    
    def format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def display_progress(self, elapsed: int, total: int, session_type: str) -> None:
        """Display progress bar and time."""
        # Clear current line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        
        # Calculate progress
        progress = elapsed / total
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = '=' * filled_length + '-' * (bar_length - filled_length)
        
        remaining = total - elapsed
        time_str = self.format_time(remaining)
        
        if session_type == "work":
            emoji = "  "
            label = "WORK"
        else:
            emoji = "  "
            label = "BREAK"
        
        sys.stdout.write(f"{emoji} [{label}] {time_str} [{bar}] {progress*100:.0f}%")
        sys.stdout.flush()
    
    def countdown(self, duration: int, session_type: str) -> bool:
        """Run countdown timer for specified duration."""
        self.start_time = time.time()
        elapsed = 0
        
        while elapsed < duration and self.running:
            if not self.paused:
                self.display_progress(elapsed, duration, session_type)
                time.sleep(1)
                elapsed += 1
            else:
                time.sleep(0.1)
                # Adjust start time to account for pause duration
                self.start_time += 0.1
        
        # Clear the progress line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
        
        return self.running  # Return True if completed normally
    
    def start_pomodoro(self) -> None:
        """Start a complete pomodoro cycle (work + break)."""
        self.running = True
        self.current_session += 1
        
        print(f"\n{'='*50}")
        print(f"POMODORO SESSION #{self.current_session}")
        print(f"{'='*50}")
        print(f"Work: {self.work_duration//60} min | Break: {self.break_duration//60} min")
        print("Controls: [p] Pause, [r] Resume, [q] Quit")
        print("-" * 50)
        
        # Work session
        print(f"\nStarting work session...")
        self.session_type = "work"
        
        # Wait for user to start
        input("Press Enter to begin work session...")
        
        work_completed = self.countdown(self.work_duration, "work")
        
        if work_completed:
            print(f"\nWork session completed! ")
            self.play_beep(3)
            self.update_stats("work", self.work_duration)
            
            print(f"Pomodoros completed today: {self.total_pomodoros_today}")
            
            # Ask if user wants to take a break
            take_break = input("\nTake a break? (Y/n): ").strip().lower()
            
            if take_break != 'n':
                # Break session
                print(f"\nStarting break session...")
                self.session_type = "break"
                
                input("Press Enter to begin break session...")
                
                break_completed = self.countdown(self.break_duration, "break")
                
                if break_completed:
                    print(f"\nBreak completed! ")
                    self.play_beep(2)
                    self.update_stats("break", self.break_duration)
                    print("Ready for another pomodoro?")
        
        self.running = False
    
    def run_continuous(self) -> None:
        """Run continuous pomodoro sessions."""
        print(f"\n{'='*50}")
        print("CONTINUOUS POMODORO MODE")
        print(f"{'='*50}")
        print("Press Ctrl+C to stop at any time")
        print("-" * 50)
        
        try:
            session_count = 0
            while True:
                session_count += 1
                
                print(f"\nSession #{session_count}")
                
                # Work session
                print(f"\nWork session ({self.work_duration//60} min)...")
                self.session_type = "work"
                
                work_completed = self.countdown(self.work_duration, "work")
                
                if not work_completed:
                    break
                
                print(f"\nWork completed! ")
                self.play_beep(3)
                self.update_stats("work", self.work_duration)
                
                # Break session
                print(f"\nBreak session ({self.break_duration//60} min)...")
                self.session_type = "break"
                
                break_completed = self.countdown(self.break_duration, "break")
                
                if not break_completed:
                    break
                
                print(f"\nBreak completed! ")
                self.play_beep(2)
                self.update_stats("break", self.break_duration)
                
                print(f"Ready for next session...")
                time.sleep(2)
        
        except KeyboardInterrupt:
            print(f"\n\nPomodoro session stopped by user.")
            self.running = False
    
    def show_stats(self) -> None:
        """Display pomodoro statistics."""
        print(f"\n{'='*50}")
        print("POMODORO STATISTICS")
        print(f"{'='*50}")
        
        if not self.stats:
            print("No pomodoro sessions recorded yet.")
            return
        
        # Show today's stats
        today = date.today().isoformat()
        if today in self.stats:
            today_stats = self.stats[today]
            print(f"\nToday ({today}):")
            print(f"  Pomodoros completed: {today_stats['pomodoros_completed']}")
            print(f"  Total work time: {today_stats['total_work_time'] // 60} min")
            print(f"  Total break time: {today_stats['total_break_time'] // 60} min")
            
            if today_stats['sessions']:
                print(f"  Sessions today: {len(today_stats['sessions'])}")
        
        # Show weekly stats
        print(f"\nLast 7 days:")
        week_total = 0
        week_work_time = 0
        
        for i in range(7):
            check_date = (date.today() - datetime.timedelta(days=i)).isoformat()
            if check_date in self.stats:
                day_stats = self.stats[check_date]
                week_total += day_stats['pomodoros_completed']
                week_work_time += day_stats['total_work_time']
        
        print(f"  Total pomodoros: {week_total}")
        print(f"  Total work time: {week_work_time // 60} min")
        print(f"  Daily average: {week_total // 7 if week_total > 0 else 0} pomodoros")
        
        # Show all-time stats
        all_time_total = sum(stats['pomodoros_completed'] for stats in self.stats.values())
        all_time_work = sum(stats['total_work_time'] for stats in self.stats.values())
        
        print(f"\nAll time:")
        print(f"  Total pomodoros: {all_time_total}")
        print(f"  Total work time: {all_time_work // 60} min ({all_time_work // 3600}h {all_time_work % 3600 // 60}m)")
        print(f"  Days tracked: {len(self.stats)}")
    
    def customize_timer(self) -> None:
        """Customize timer durations."""
        print(f"\n{'='*50}")
        print("CUSTOMIZE TIMER")
        print(f"{'='*50}")
        
        try:
            work_min = int(input(f"Work duration (minutes) [current: {self.work_duration//60}]: ") or str(self.work_duration//60))
            break_min = int(input(f"Break duration (minutes) [current: {self.break_duration//60}]: ") or str(self.break_duration//60))
            
            if work_min > 0 and work_min <= 120 and break_min > 0 and break_min <= 60:
                self.work_duration = work_min * 60
                self.break_duration = break_min * 60
                print(f"Timer updated: {work_min} min work, {break_min} min break")
            else:
                print("Invalid durations! Using defaults.")
        
        except ValueError:
            print("Invalid input! Using defaults.")

def main_menu():
    """Main menu for pomodoro timer."""
    timer = PomodoroTimer()
    
    while True:
        print(f"\n{'='*50}")
        print("POMODORO TIMER")
        print(f"{'='*50}")
        print("1. Start Single Pomodoro")
        print("2. Start Continuous Mode")
        print("3. View Statistics")
        print("4. Customize Timer")
        print("5. Exit")
        
        choice = input(f"\nSelect option (1-5): ").strip()
        
        if choice == '1':
            timer.start_pomodoro()
        elif choice == '2':
            timer.run_continuous()
        elif choice == '3':
            timer.show_stats()
        elif choice == '4':
            timer.customize_timer()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

def main():
    """Main function."""
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
