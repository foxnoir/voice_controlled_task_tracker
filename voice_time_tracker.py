#!/usr/bin/env python3
"""
Voice-based Task Tracking System
Start tasks with voice commands like "Start tracking work" or "Start tracking Pause"
End tasks with "end" or "task end"
Automatically generates statistics when program exits
"""

import sys

try:
    import speech_recognition as sr  # type: ignore
except ImportError:
    print("Error: speech_recognition package not found!")
    print("Please install it with: pip install SpeechRecognition")
    print("Or install all requirements: pip install -r requirements.txt")
    sys.exit(1)

# pyaudio is optional - speech_recognition can work without it
try:
    import pyaudio  # type: ignore  # noqa: F401

    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("Warning: pyaudio not installed. Microphone access may be limited.")
    print("To install: brew install portaudio && pip install pyaudio")

import json
import os
import signal
import subprocess
import threading
import platform
from datetime import datetime, timedelta
from collections import defaultdict

# Constants
DEFAULT_REMINDER_INTERVAL_MINUTES = 15
DATA_FILE = "tracked_tasks.json"
LISTEN_TIMEOUT = 8
PHRASE_TIME_LIMIT = 20
REMINDER_CHECK_INTERVAL = 60  # seconds


class VoiceTimeTracker:
    def __init__(self, reminder_interval_minutes=DEFAULT_REMINDER_INTERVAL_MINUTES):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tasks = []  # List of task sessions
        self.current_task = None
        self.current_task_start = None
        self.running = True
        self.data_file = DATA_FILE

        # Reminder system - only when no task is active
        self.reminder_interval = timedelta(minutes=reminder_interval_minutes)
        self.last_task_activity = (
            datetime.now()
        )  # Last time a task was started or ended
        self.reminder_timer = None
        self.reminder_thread = None

        # Load existing data
        self.load_data()

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Start reminder thread
        self.start_reminder_thread()

        print("Voice Time Tracker initialized!")
        print(
            f"Reminder: Audio reminder after {reminder_interval_minutes} minutes when no task is active"
        )
        print("Commands:")
        print("  - 'Start tracking [task name]' or 'Start [task name] tracking'")
        print("  - 'End', 'Task', or 'Stop' to stop current task")
        print("  - 'Show statistics' (or 'stats') to see current stats")
        print("  - 'Clear statistics' to delete all tracked data")
        print("  - 'Exit' or Ctrl+C to quit and show final statistics")
        print("\nListening for commands...\n")

    def play_reminder_sound(self):
        """Play a reminder sound"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Play a system sound on macOS using afplay
                subprocess.run(
                    ["afplay", "/System/Library/Sounds/Glass.aiff"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif platform.system() == "Linux":
                # Play a beep on Linux
                subprocess.run(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Windows - use winsound
                try:
                    import winsound

                    winsound.Beep(1000, 500)  # 1000 Hz for 500 ms
                except ImportError:
                    # Fallback: print bell character
                    print("\a", end="", flush=True)
        except Exception:
            # If sound playback fails, just print a visual reminder
            print("\a", end="", flush=True)

    def start_reminder_thread(self):
        """Start background thread for reminder notifications"""

        def reminder_loop():
            while self.running:
                try:
                    # Only check for reminders if NO task is currently active
                    if not self.current_task:
                        # Calculate time since last task activity (start or end)
                        time_since_activity = datetime.now() - self.last_task_activity

                        # Check if reminder interval has passed
                        if time_since_activity >= self.reminder_interval:
                            print(
                                "\n🔔 Reminder: No task tracked recently. Start tracking a task?\n"
                            )
                            self.play_reminder_sound()
                            # Reset activity time after reminder to avoid repeated sounds
                            self.last_task_activity = datetime.now()

                    # Sleep before checking again
                    threading.Event().wait(REMINDER_CHECK_INTERVAL)
                except Exception:
                    # Continue running even if there's an error
                    continue

        self.reminder_thread = threading.Thread(target=reminder_loop, daemon=True)
        self.reminder_thread.start()

    def update_task_activity(self):
        """Update the last task activity timestamp (when task starts or ends)"""
        self.last_task_activity = datetime.now()

    def _extract_task_name(self, text_lower: str) -> str:
        """Extract task name from various command formats"""
        if "start tracking" in text_lower:
            return text_lower.replace("start tracking", "").strip()

        # Handle "start [task] tracking"
        if "tracking" in text_lower:
            parts = text_lower.split("tracking")
            if len(parts) > 1:
                return parts[0].replace("start", "").strip()

        # Fallback: remove both words
        return text_lower.replace("start", "").replace("tracking", "").strip()

    def load_data(self):
        """Load existing tracking data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])

                    # Normalize old data: add "date" field if missing
                    for task_session in self.tasks:
                        if "date" not in task_session:
                            start_time = datetime.fromisoformat(task_session["start"])
                            task_session["date"] = start_time.strftime("%Y-%m-%d")

                    # Save normalized data back to file
                    if self.tasks:
                        self.save_data()

                    print(f"Loaded {len(self.tasks)} previous task sessions.")
            except Exception as e:
                print(f"Error loading data: {e}")
                self.tasks = []

    def save_data(self):
        """Save tracking data to JSON file"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"tasks": self.tasks}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")

    def listen_for_command(self):
        """Listen for voice command using microphone"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening... (speak now)")
                audio = self.recognizer.listen(
                    source, timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT
                )

            # Try to recognize speech - English only
            try:
                text = self.recognizer.recognize_google(audio, language="en-US")
                print(f"Recognized: {text}")
                return text.lower()
            except sr.UnknownValueError:
                print("Could not understand audio. Please try again.")
                return None
            except sr.RequestError as e:
                print(f"Error with speech recognition service: {e}")
                return None

        except sr.WaitTimeoutError:
            print("No speech detected. Listening again...")
            return None
        except Exception as e:
            print(f"Error listening: {e}")
            return None

    def parse_command(self, text):
        """Parse voice command and execute appropriate action"""
        if not text:
            return

        text_lower = text.lower()

        # Start tracking commands - flexible matching
        # Accept: "start tracking [task]", "start [task] tracking", "track [task]"
        if "start" in text_lower and "tracking" in text_lower:
            task_name = self._extract_task_name(text_lower)
            if task_name:
                self.start_task(task_name)
            else:
                print("Please specify a task name. Example: 'Start tracking homework'")
        # Handle "track [task]" as alternative start command
        elif text_lower.startswith("track ") and "tracking" not in text_lower:
            task_name = text_lower.replace("track", "").strip()
            if (
                task_name and len(task_name.split()) <= 3
            ):  # Limit to prevent false matches
                self.start_task(task_name)

        # End tracking commands - more flexible
        # Accept: "end", "task end", "stop", "task stop", just "task" alone
        elif (
            "end" in text_lower
            or ("task" in text_lower and ("end" in text_lower or "stop" in text_lower))
            or text_lower.strip() == "task"
            or text_lower.strip() == "stop"
        ):
            self.end_task()

        # Clear statistics command
        elif "clear" in text_lower and "statistics" in text_lower:
            self.clear_statistics()

        # Show statistics - accept singular and plural
        elif (
            "statistics" in text_lower
            or "statistic" in text_lower
            or "statistik" in text_lower
            or "stats" in text_lower
        ):
            self.show_statistics()

        # Exit command
        elif "exit" in text_lower or "beenden" in text_lower or "quit" in text_lower:
            self.running = False

        else:
            print(f"Unknown command: {text}")
            print(
                "Try: 'Start tracking [task name]', 'End'/'Task', 'Show statistics', or 'Exit'"
            )

    def start_task(self, task_name):
        """Start tracking a new task"""
        if self.current_task:
            print(f"Already tracking: {self.current_task}. Ending it first...")
            self.end_task()

        self.current_task = task_name
        self.current_task_start = datetime.now()
        self.update_task_activity()  # Update task activity time when task starts
        print(f"\n✓ Started tracking: {task_name}")
        print(f"  Started at: {self.current_task_start.strftime('%H:%M:%S')}\n")

    def end_task(self):
        """End current task and save it"""
        if not self.current_task:
            print("No active task to end.")
            return

        end_time = datetime.now()
        duration = end_time - self.current_task_start

        task_session = {
            "task": self.current_task,
            "date": end_time.strftime(
                "%Y-%m-%d"
            ),  # YYYY-MM-DD format for daily statistics
            "start": self.current_task_start.isoformat(),
            "end": end_time.isoformat(),
            "duration_seconds": int(duration.total_seconds()),
            "duration_formatted": str(duration),
        }

        self.tasks.append(task_session)
        self.save_data()
        self.update_task_activity()  # Update task activity time when task ends

        print(f"\n✓ Ended tracking: {self.current_task}")
        print(f"  Duration: {self.format_duration(duration)}")
        print(f"  Ended at: {end_time.strftime('%H:%M:%S')}\n")

        self.current_task = None
        self.current_task_start = None

    def format_duration(self, duration):
        """Format duration in a human-readable way"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def show_statistics(self):
        """Show current statistics grouped by day"""
        if not self.tasks:
            print("\nNo tasks tracked yet.\n")
            return

        # Group tasks by date
        tasks_by_date = defaultdict(list)
        for task_session in self.tasks:
            date = task_session.get(
                "date",
                datetime.fromisoformat(task_session["start"]).strftime("%Y-%m-%d"),
            )
            tasks_by_date[date].append(task_session)

        # Sort dates chronologically
        sorted_dates = sorted(tasks_by_date.keys())

        print("\n" + "=" * 70)
        print("TIME TRACKING STATISTICS")
        print("=" * 70)

        overall_total_time = timedelta()

        # Show statistics for each day
        for date in sorted_dates:
            day_tasks = tasks_by_date[date]

            # Calculate statistics for this day
            task_times = defaultdict(int)
            day_total_time = timedelta()

            for task_session in day_tasks:
                task_name = task_session["task"]
                duration = timedelta(seconds=task_session["duration_seconds"])
                task_times[task_name] += duration.total_seconds()
                day_total_time += duration
                overall_total_time += duration

            # Format date for display
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_display = date_obj.strftime("%A, %B %d, %Y")

            print(f"\n{date_display} ({date})")
            print("-" * 70)

            # Sort tasks by time spent for this day
            sorted_tasks = sorted(task_times.items(), key=lambda x: x[1], reverse=True)

            for task_name, seconds in sorted_tasks:
                duration = timedelta(seconds=int(seconds))
                percentage = (
                    (seconds / day_total_time.total_seconds() * 100)
                    if day_total_time.total_seconds() > 0
                    else 0
                )
                print(
                    f"  {task_name:28s} {self.format_duration(duration):15s} ({percentage:5.1f}%)"
                )

            print(f"\n  {'DAY TOTAL':28s} {self.format_duration(day_total_time):15s}")
            print(f"  {'SESSIONS':28s} {len(day_tasks):15d}")

        # Overall totals
        print("\n" + "=" * 70)
        print(
            f"{'OVERALL TOTAL TIME':28s} {self.format_duration(overall_total_time):15s}"
        )
        print(f"{'TOTAL SESSIONS':28s} {len(self.tasks):15d}")
        print(f"{'TOTAL DAYS':28s} {len(sorted_dates):15d}")
        print("=" * 70 + "\n")

    def clear_statistics(self):
        """Clear all statistics by deleting the data file"""
        try:
            # Clear in-memory data
            self.tasks = []
            self.current_task = None
            self.current_task_start = None

            # Delete the data file
            if os.path.exists(self.data_file):
                os.remove(self.data_file)
                print("\n✓ All statistics cleared! Data file deleted.\n")
            else:
                print("\n✓ Statistics cleared! (No data file found)\n")
        except Exception as e:
            print(f"\n✗ Error clearing statistics: {e}\n")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\nShutting down...")
        if self.current_task:
            print(f"Ending current task: {self.current_task}")
            self.end_task()
        self.running = False

    def run(self):
        """Main loop"""
        while self.running:
            try:
                command = self.listen_for_command()
                if command:
                    self.parse_command(command)
            except KeyboardInterrupt:
                self.signal_handler(None, None)
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                continue

        # Show final statistics
        print("\n" + "=" * 60)
        print("FINAL STATISTICS")
        print("=" * 60)
        self.show_statistics()
        print("Thank you for using Voice Time Tracker!")


def main():
    """Main entry point"""
    print("Initializing Voice Time Tracker...")

    # Check if PyAudio is available (required for microphone access)
    if not HAS_PYAUDIO:
        print("\n" + "=" * 60)
        print("ERROR: PyAudio is required for microphone input!")
        print("=" * 60)
        print("\nTo install PyAudio on macOS:")
        print("  1. Install PortAudio: brew install portaudio")
        print("  2. Install PyAudio: pip install pyaudio")
        print("\nOr run both commands together:")
        print("  brew install portaudio && pip install pyaudio")
        print("=" * 60 + "\n")
        sys.exit(1)

    # Check if microphone is available
    try:
        mic = sr.Microphone()
        with mic as source:  # noqa: F841
            # Just checking if microphone is accessible
            pass
    except Exception as e:
        print(f"Error: Microphone not available: {e}")
        print("Please check your microphone connection and permissions.")
        print(
            "On macOS, ensure the app has microphone permissions in System Preferences."
        )
        sys.exit(1)

    tracker = VoiceTimeTracker()
    tracker.run()


if __name__ == "__main__":
    main()
