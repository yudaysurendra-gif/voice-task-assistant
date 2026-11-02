"""
Voice Task Assistant
--------------------
A simple voice-controlled to-do list manager.

Install dependencies:
    pip install SpeechRecognition pyttsx3 pyaudio

Voice commands (examples):
    "add task buy groceries"
    "show tasks"
    "complete task 1"
    "delete task 2"
    "clear all tasks"
    "help"
    "exit"

If no microphone is available, the assistant falls back to typed input.
"""

import json
import os
import re
from datetime import datetime

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

TASK_FILE = "tasks.json"


# ---------------------------------------------------------------- Storage
def load_tasks():
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


# ---------------------------------------------------------------- Speech
engine = None
if pyttsx3:
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
    except Exception:
        engine = None


def speak(text):
    """Print and speak a response."""
    print(f"Assistant: {text}")
    if engine:
        engine.say(text)
        engine.runAndWait()


def listen():
    """Listen from the microphone; fall back to typed input on failure."""
    if sr is None:
        return input("You (type): ").strip().lower()

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("\nListening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        text = recognizer.recognize_google(audio).lower()
        print(f"You: {text}")
        return text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that.")
        return ""
    except (sr.RequestError, OSError):
        # No internet or no microphone -> typed input
        return input("You (type): ").strip().lower()


# ---------------------------------------------------------------- Task logic
def add_task(tasks, title):
    if not title:
        speak("Please tell me what task to add.")
        return
    tasks.append({
        "title": title,
        "done": False,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_tasks(tasks)
    speak(f"Added task: {title}")


def show_tasks(tasks):
    if not tasks:
        speak("Your task list is empty.")
        return
    speak(f"You have {len(tasks)} tasks.")
    for i, t in enumerate(tasks, start=1):
        status = "done" if t["done"] else "pending"
        print(f"  {i}. {t['title']} [{status}]")
    pending = [t["title"] for t in tasks if not t["done"]]
    if pending and engine:
        engine.say("Pending tasks are: " + ", ".join(pending))
        engine.runAndWait()


WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def extract_number(text):
    match = re.search(r"\d+", text)
    if match:
        return int(match.group())
    for word, num in WORD_NUMBERS.items():
        if word in text.split():
            return num
    return None


def complete_task(tasks, command):
    n = extract_number(command)
    if n and 1 <= n <= len(tasks):
        tasks[n - 1]["done"] = True
        save_tasks(tasks)
        speak(f"Marked task {n} as complete.")
    else:
        speak("Please say a valid task number.")


def delete_task(tasks, command):
    n = extract_number(command)
    if n and 1 <= n <= len(tasks):
        removed = tasks.pop(n - 1)
        save_tasks(tasks)
        speak(f"Deleted task: {removed['title']}")
    else:
        speak("Please say a valid task number.")


def clear_tasks(tasks):
    tasks.clear()
    save_tasks(tasks)
    speak("All tasks cleared.")


def show_help():
    speak("You can say: add task, show tasks, complete task number, "
          "delete task number, clear all tasks, or exit.")


# ---------------------------------------------------------------- Command parser
def process_command(tasks, command):
    """Return False when the assistant should stop."""
    if not command:
        return True

    if any(w in command for w in ("exit", "quit", "stop", "goodbye", "bye")):
        speak("Goodbye! Have a productive day.")
        return False

    if command.startswith(("add task", "add a task", "new task", "add")):
        title = re.sub(r"^(add a task|add task|new task|add)\s*", "", command).strip()
        add_task(tasks, title)
    elif "clear" in command:
        clear_tasks(tasks)
    elif "show" in command or "list" in command or "what are my" in command:
        show_tasks(tasks)
    elif "complete" in command or "finish" in command or "done" in command:
        complete_task(tasks, command)
    elif "delete" in command or "remove" in command:
        delete_task(tasks, command)
    elif "help" in command:
        show_help()
    else:
        speak("I did not recognise that command. Say help for options.")
    return True


# ---------------------------------------------------------------- Main loop
def main():
    tasks = load_tasks()
    speak("Hello! I am your voice task assistant. Say help to hear the commands.")
    running = True
    while running:
        command = listen()
        running = process_command(tasks, command)


if __name__ == "__main__":
    main()
