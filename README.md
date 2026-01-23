<a name="readme-top"></a>

<!-- Top Links Bar -->

[![LinkedIn][linkedin-shield]][linkedin-url]
[![Instagram][instagram-shield]][instagram-url]

<!-- PROJECT LOGO -->
<br />

<div align="center">
  <img src="images/logo.png" alt="Logo" width="80" height="80">
  <h1 align="center">Voice Controlled Task Tracker</h1>

  <p align="center">
    A voice-based time tracking system for Python
    <br />
    <a href="https://github.com/foxnoir/voice_controlled_task_tracker"><strong>Explore the project »</strong></a>
    <br />
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#requirements">Requirements</a></li>
        <li><a href="#optional-microphone-support">Optional Microphone Support</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
    </li>
    <li>
      <a href="#commands">Commands</a>
    </li>
    <li>
      <a href="#how-it-works">How It Works</a>
    </li>
    <li>
      <a href="#reminder-system">Reminder System</a>
    </li>
    <li>
      <a href="#statistics">Statistics</a>
    </li>
    <li>
      <a href="#example-output">Example Output</a>
    </li>
    <li>
      <a href="#technical-details">Technical Details</a>
    </li>
  </ol>
</details>

## About The Project

Voice Controlled Task Tracker is a Python-based time tracking system that allows you to track your tasks using voice commands. Simply speak commands to start and stop tracking tasks, and the system automatically generates daily and overall statistics.

**Key Features:**
- Voice-controlled task tracking
- Daily statistics grouped by date
- Automatic data persistence
- English speech recognition
- Audio reminders when no task is active (15 minutes)
- Graceful shutdown handling

<p align="right"><a href="#readme-top">back to top</a></p>

## Installation

**Important:** If you're using a virtual environment (`.venv`), install the packages there!

### Requirements

Install the required packages from [`requirements.txt`](requirements.txt):

```bash
# In virtual environment:
.venv/bin/pip install -r requirements.txt

# Or without venv:
pip install -r requirements.txt
```

The main requirement is:
- `SpeechRecognition>=3.10.0` - For speech recognition functionality

See [`requirements.txt`](requirements.txt) for the complete list.

### Optional Microphone Support

For better microphone support (recommended):

**On macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**On Linux:**
```bash
# Ubuntu/Debian:
sudo apt-get install portaudio19-dev python3-pyaudio

# Or Fedora/RHEL:
sudo yum install portaudio-devel
pip install pyaudio
```

**Note:** The program works without `pyaudio`, but microphone functionality may be limited.

<p align="right"><a href="#readme-top">back to top</a></p>

## Usage

Start the program in the terminal:

```bash
python voice_time_tracker.py
# or
python3 voice_time_tracker.py
```

<p align="right"><a href="#readme-top">back to top</a></p>

## Commands

The program recognizes the following voice commands (in English):

### Start Tracking
- **"Start tracking [task name]"** - Start tracking a task
- **"Start [task name] tracking"** - Alternative format
- **Examples:** "Start tracking work", "Start tracking pause", "Start homework tracking"

### Stop Tracking
- **"End"** - End the current task
- **"Task"** - End the current task (single word)
- **"Stop"** - End the current task
- **"Task end"** - End the current task

### Show Statistics
- **"Show statistics"** - Display current statistics
- **"Show stats"** - Short form
- **"Statistics"** - Alternative command

### Clear Statistics
- **"Clear statistics"** - Delete all tracked data and the data file

### Exit
- **"Exit"** - Quit the program and show final statistics
- **"Quit"** - Alternative exit command
- Or press `Ctrl+C` - Graceful shutdown with statistics

<p align="right"><a href="#readme-top">back to top</a></p>

## How It Works

1. The program runs continuously and listens for voice commands
2. When you say "Start tracking [name]", time tracking begins
3. When you say "End" (or "Task", "Stop"), the current task is ended and saved
4. All data is automatically saved to `tracked_tasks.json`
5. Each task session includes a date tag for daily statistics
6. **Reminder System**: If no task is active for 15 minutes, an audio reminder plays to remind you to start tracking
7. When you exit (Exit or Ctrl+C), final statistics are automatically displayed

**Note:** Reminders only play when no task is currently active. While a task is running, no reminders will be shown, even after hours of tracking.

<p align="right"><a href="#readme-top">back to top</a></p>

## Reminder System

The program includes an intelligent reminder system to help you stay on track:

- **Automatic Reminders**: After 15 minutes of inactivity (no task started or ended), an audio reminder plays
- **Smart Timing**: Reminders only activate when **no task is currently active**
- **Reset on Activity**: The reminder timer resets whenever you start or end a task
- **Audio Notification**: System sounds play on macOS, Linux, and Windows

**Example:**
- You start tracking "work" at 10:00 AM → No reminders while tracking
- You stop tracking at 2:00 PM → Reminder timer starts
- At 2:15 PM → Audio reminder plays: "Reminder: No task tracked recently. Start tracking a task?"
- You start tracking "pause" at 2:20 PM → Timer resets
- You stop tracking "pause" at 2:30 PM → Timer starts again
- At 2:45 PM → Another reminder if no new task started

<p align="right"><a href="#readme-top">back to top</a></p>

## Statistics

The statistics show:
- **Daily Statistics**: Tasks grouped by date with:
  - Time per task (sorted by duration)
  - Percentage distribution
  - Daily total time
  - Number of sessions per day
- **Overall Statistics**:
  - Total time across all days
  - Total number of sessions
  - Total number of days tracked

Statistics are displayed chronologically, with each day showing its own breakdown.

<p align="right"><a href="#readme-top">back to top</a></p>

## Example Output

```
✓ Started tracking: work
  Started at: 14:30:15

✓ Ended tracking: work
  Duration: 45m 30s
  Ended at: 15:15:45

======================================================================
TIME TRACKING STATISTICS
======================================================================

Monday, January 15, 2024 (2024-01-15)
----------------------------------------------------------------------
  work                          45m 30s         (60.0%)
  pause                         30m 15s         (40.0%)

  DAY TOTAL                     1h 15m 45s
  SESSIONS                                 2

======================================================================
OVERALL TOTAL TIME              1h 15m 45s
TOTAL SESSIONS                             2
TOTAL DAYS                                 1
======================================================================
```

<p align="right"><a href="#readme-top">back to top</a></p>

## Technical Details

- **Speech Recognition**: Uses Google Speech Recognition API (free, requires internet connection)
- **Language**: English (`en-US`)
- **Data Storage**: JSON format in `tracked_tasks.json`
- **Date Tracking**: Each task session is tagged with a date (`YYYY-MM-DD`) for daily statistics
- **Automatic Features**:
  - Ambient noise adjustment for better recognition
  - Audio reminders (15 minutes of inactivity when no task is active)
  - Graceful shutdown with Ctrl+C
  - Automatic data normalization for backward compatibility
- **Data Structure**: Each task session includes:
  - Task name
  - Date (YYYY-MM-DD format)
  - Start time (ISO format)
  - End time (ISO format)
  - Duration in seconds
  - Formatted duration string

<p align="right"><a href="#readme-top">back to top</a></p>

[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/tanja-polz-5636401a5/
[twitter-shield]: https://img.shields.io/badge/Twitter-%231DA1F2.svg?style=for-the-badge&logo=Twitter&logoColor=white
[twitter-url]: https://twitter.com/_foxnoir_?lang=de
[instagram-shield]: https://img.shields.io/badge/Instagram-%23E4405F.svg?style=for-the-badge&logo=Instagram&logoColor=white
[instagram-url]: https://www.instagram.com/codeincouture/
