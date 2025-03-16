from datetime import datetime, timedelta, timezone,date
import playsound
from gtts import gTTS
import pytz
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import time
import speech_recognition as sr
import sys
import subprocess



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]    #SCOPES CONSTANT for google calendar
DAYS=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]    #constant containing the days of the week
MONTHS=["january","february","march","april","may","june","july","august","september","october","november","december"]  #constant containing the months of the year
DAY_EXTENSIONS = ["nd", "rd", "th", "st"]  # constant containing the terminations of numbers
CALNDAR_STRS = ["what do i have", "do i have plans", "am i busy", "do i have"]
NOTE_STRS = ["write a note","write something","make a note", "write me something"]
EXIT_STRS=["quit the program","exit the program"]
CALCULATOR_STRS=["open the calculator"]


def speak(text):              # done:speak function using gtts
    tts = gTTS(text=text, lang="en")
    filename = "voice.mp3"
    tts.save(filename)
    playsound.playsound(filename)


def get_audio():           # done:ffunction that hears and listens the user
    recognize = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            recognize.adjust_for_ambient_noise(source, duration=1)
            recognize.pause_threshold = 3
            print("Listening... You have up to 10 seconds to start speaking.")

            audio = recognize.listen(source, timeout=10, phrase_time_limit=7)

            print("Processing your input...")
            said = recognize.recognize_google(audio)
            print(f"You said: {said}")
            
        except Exception as e:
            print("Exception"+str(e))    
    return said


def password_required():       #function for authentification of the user
   speak("You need a pasword to continue")
   print("You need a pasword to continue")
   text=get_audio()
   i=3
   while "happy" not in text:
  
     speak("Incorrect password"+str(i)+"more tries left")
     print("Incorrect password"+str(i)+"more tries left")
     i=i-1
     text=get_audio()
     if i==0:
         speak("You cant try anymore.Program exits...")
         sys.exit()
   speak("Hello sir. How are you doing today")  
   print("Hello sir. How are you doing today")  
   text=get_audio()

   if "good" in text:
     speak("Very good sir,how can I help you?")
     print("Very good sir,how can I help you?")

  
def authenticate_google():    #function for authetnicating with google calendar
    creds = None
    # Token file for access and refresh tokens
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                speak("Credentials file is missing. Please add credentials.json and try again.")
                sys.exit()

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for reuse
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
    try:
        service = build("calendar", "v3", credentials=creds)
        print("Google Calendar service initialized.")
        return service
    except HttpError as e:
        print(f"Google API Error: {e}")
        sys.exit()


def get_events(day, service):   #function for getting the events from google calendar            
    # Ensure the 'day' parameter is a valid date object
    if not isinstance(day, date):
        print("Invalid date passed to get_events.")
        speak("I could not understand the date.")
        return

    # Define time range for the specified day
    start_of_day = datetime.combine(day, datetime.min.time())
    end_of_day = datetime.combine(day, datetime.max.time())
    utc = pytz.UTC
    start_of_day = start_of_day.astimezone(utc)
    end_of_day = end_of_day.astimezone(utc)

    # Query Google Calendar for events within the specified time range
    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        if not events:
            print(f"No events found for {day}.")
            speak(f"No events found for {day}.")
            return

        print(f"Events on {day}:")
        if len(events) == 1:
            speak("You have only one event on this day")
        else:    
            speak(f"You have  {len(events)} events on this day")
        speak(f"Events on {day}:")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event["summary"]
            print(f"{start}: {summary}")
            start_time = str(start.split("T")[1].split("-")[0])
            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + "am"
            else: 
                start_time = start_time + "pm"   
            speak(event["summary"] + "at" + start_time)    
    except HttpError as e:
        print(f"An error occurred while fetching events: {e}")
        speak("I could not fetch events at this moment.")


def get_date(text):      #function for getting and process the date inpout from the user
    text = text.lower()
    today = date.today()
    
    if "today" in text:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENSIONS:
                if word.endswith(ext) and word[:-len(ext)].isdigit():
                    day = int(word[:-len(ext)])
                    break

   
    if month < today.month and month != -1:
        year += 1
    if day < today.day and month == -1 and day != -1:
        month = today.month + 1
    
   
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        days_until = day_of_week - current_day_of_week
        if days_until < 0:
            days_until += 7
        if "next" in text:
            days_until += 7
        return today + timedelta(days=days_until)

    
    if month == -1:
        month = today.month
    if day == -1:
        day = today.day

    
    try:
        return date(year, month, day)
    except ValueError as e:
        print(f"Invalid date generated: {e}")
        return None


def note(text):
    date_variable = datetime.now()
    filename = str(date_variable).replace(":", "-") + "note.txt"
    with open(filename, "w") as f:
        f.write(text)
    app_name = "TextEdit"
    subprocess.run(["open", "-a", app_name,filename])    


def calculator():
    try: 
        app_name = "Calculator"
        subprocess.run(["open", "-a", app_name])  
        print("Calculator opened successfully!")
    except Exception as e:
        print(f"An error occurred while opening the calculator: {e}")


def get_final_date(text):
    for phrase in CALNDAR_STRS:
        if phrase.lower() in text.lower():
            date_variable = get_date(text)
            if date_variable:
                get_events(date_variable, service)
                return True
           
                    
 

def get_note(text):
    for phrase in NOTE_STRS:
        if phrase in text:
            speak("What would you like me to write?")
            print("What would you like me to write?") 
            note_text=get_audio().lower()
            note(note_text)
            speak("I've made a note of that.")
            print("I've made a note of that.")
            return True


def get_calculator(text):
    for phrase in CALCULATOR_STRS:
        if phrase in text:  
            calculator()
            return True


def exit_program(text):
    for phrase in EXIT_STRS:
        if phrase in text:
           speak("The program will shut down")
           print("the program will shut down")
           sys.exit()
           return True


service=authenticate_google()

def main():
    password_required()

    i = 0
    j = 0

    while True:

        if (i != 0):
            speak("What else can I do")
            print("What else can i do")
        i = i + 1

        try:
            text = get_audio()
            handled = False 

            if get_final_date(text):
                handled = True
            elif get_note(text):
                handled = True
            elif get_calculator(text):
                handled = True
            elif exit_program(text):
                handled = True

            if handled == False:
                raise ValueError("")

        except ValueError:
            i = 0
            j = j + 1
            if j == 5:
                sys.exit()
            speak("Didn't understand, can you try again?")
            print("Didn't understand, can you try again?")

main()            