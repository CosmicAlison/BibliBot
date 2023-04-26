import speech_recognition as sr
import pyttsx3
import time
import serial
import cv2
import numpy as np
from keras.models import load_model
import mysql.connector
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
from scipy.io.wavfile import write

wrong_answer = AudioSegment.from_wav('wrong_answer.wav')
upbeat = AudioSegment.from_wav('happy.wav')

# set serial communication with arduino board
arduino = serial.Serial('COM5', 9600)
time.sleep(2)

# create dictionary storing story titles and ages associated

stories = [
    {
        "title": "king midas and the golden touch",
        "ages": [4, 5, 6, 7, 8]
    },
    {
        "title": "alice in wonderland",
        "ages": [8, 9, 10, 11, 12, 13, 14]

    },
    {
        "title": "winnie the pooh",
        "ages": [7, 8, 9, 10, 11, 12]
    },
    {
        "title": "pinocchio",
        "ages": [5, 6, 7, 8, 9, 10]
    }
]

lessons = [
    {
        "subject": "Level 1 Math",
        "ages": [4, 5],
        "questions": ["Please count from 1 to 20", "What is 8 plus 2", "What is 5 plus 3", "What is 8 minus 6",
                      "What is 10 minus 2"],
        "answers": ["1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20", "10", "8", "2", "8"],
        "explanation": ["Counting from 1 to 20 is 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20",
                        "You can use a pencil to help you, draw 8 sticks which is the number we are starting with" +
                        ", now draw 2 more sticks next to them, count the number of sticks you have drawn." +
                        "This is the result.",
                        "You can use a pencil to help you, draw 5 sticks which is the number we are starting with" +
                        ", now draw 3 more sticks next to them, count the number of sticks you have drawn." +
                        "This is the result.",
                        "You can draw 8 sticks to start with, now cross out 6 of those sticks." +
                        "The number of sticks you are left with is the result.",
                        "You can draw 10 sticks to start with, now cross out 2 of those sticks." +
                        "The number of sticks you are left with is the result."
                        ]
    },
    {
        "subject": "Level 2 Math",
        "ages": [5, 6, 7],
        "questions": ["What is 20 plus 23", "What is 50 minus 12", "What is 3 times 2",
                      "What is 5 times 1", "What is 3 times 0"],
        "answers": ["43", "38", "6", "5", "0"],
        "explanation": ["Write down 20 and then write down 23 below it. Add each column of numbers",
                        "Write down 50 and then write down 12 below it. Subtract each column of numbers",
                        "Practice the multiplication table for 3, 3 times 2 is 6",
                        "Practice the multiplication table for 5, 5 times 1 is 5",
                        "Any number times 0 is equal to 0"]
    }
]
# connect to mysql database

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="robot"
)


# function handles communication with the Arduino
def write_to_board(x):
    arduino.write(x)
    time.sleep(0.05)
    data = arduino.readline()
    return data.decode()


# class objects return frame with face identification result
class childDetection:
    def __init__(self, model, frame):
        self.frame = frame
        self.model = model
        self.firelist = ["ALISON", "NOT ALISON"]

    def process_frame(self):
        # Preprocess the frame
        resized = cv2.resize(frame, (86, 48))

        # Use the model to predict whether there is known child in the frame
        global prediction
        prediction = model.predict(np.expand_dims(resized, axis=0))
        print(
            f"Prediction is: {prediction} and the label is: {[np.argmax(prediction)]}")
        global label
        label = self.firelist[np.argmax(prediction)]

        cv2.putText(frame, label, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return frame


# initialization

# begin text to speech engine
engine = pyttsx3.init()
voice = engine.getProperty('voices')
engine.setProperty('voice', voice[1].id)
# begin speech recognition
listener = sr.Recognizer()

# declare robot name
robot_name = 'robot'


# handle task of listening for user's input
def listen():
    #
    def record_audio(duration, fs=44100):
        print("Recording...")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()
        print("Recording finished.")
        return recording

    def save_audio_to_file(recording, file_path, fs=44100):
        write(file_path, fs, recording)

    def recognize_audio_from_file(file_path):
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)

        try:
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            return text

        except sr.UnknownValueError:
            print("Could not understand audio.")
            speak("Sorry I could not understand you, please say it again")
            listen()
        except sr.RequestError as e:
            print("Error calling the service; {0}".format(e))

    duration = 5
    audio_file_path = "output.wav"

    audio_data = record_audio(duration)
    save_audio_to_file(audio_data, audio_file_path)

    recognized_text = recognize_audio_from_file(audio_file_path)
    if recognized_text:
        print("You said: ", recognized_text)
        return recognized_text



# handle speech creation
def speak(x):
    engine.say(x)
    engine.runAndWait()


# read ultrasonic data
while True:
    # request arduino board to conduct a sweep and send ultrasonic data to python script
    line = write_to_board(b'a')

    # if data received saying an object was found closer than 40 metres open camera
    if int(line) <= 40:
        print("Distance:" + line)

        if __name__ == "__main__":
            # Start capturing the camera feed
            cap = cv2.VideoCapture(0)
            # Load the trained model
            model = load_model(r'\face_2.h5')

            count = 0
            while count < 10:
                ret, frame = cap.read()
                # Initialize the class
                face = childDetection(model, frame)
                if ret:
                    processed_frame = face.process_frame()
                    cv2.imshow("Face Detection", processed_frame)
                    print(label)
                    count = count + 1

            if label == "ALISON":
                child_name = "Alison"

                mycursor = mydb.cursor()

                # get age of identified child
                sql = "SELECT age FROM child WHERE child_name ='" + child_name + "'"

                mycursor.execute(sql)

                age = str(mycursor.fetchone())
                age.replace('(', '')
                age.replace(')', '')
                age.replace(',', '')
                print(age)

                arduino.write(b'd')
                speak("Hello Alison. Would you like to have a lesson or read a story?")
                words = listen()

                # loop through story dictionary looking for story
                if words == "story":
                    # check individual story
                    for x in stories:
                        # check ages array of each story (stores appropriate ages for story)
                        ages = x["ages"]
                        if 6 in ages:
                        # if age of child is found in the age range for each story

                            story_title = x["title"]
                            break

                    try:
                        mycursor = mydb.cursor()

                        # get the body of the appropriate story from the database
                        sql = "SELECT body FROM story WHERE title ='" + story_title + "'"

                        mycursor.execute(sql)
                        # store retrieved story and start reading it
                        story = mycursor.fetchone()[0]
                        story = story.replace('\n', ' ')
                        speak(story)

                    except:
                        speak("Story not found for your age range.")

                elif words == "lesson":
                    # loop through each lesson
                    for x in lessons:
                        ages = x["ages"]
                        if 6 in ages:
                            lesson_title = x["subject"]
                            lesson_questions = x["questions"]
                            lesson_answers = x["answers"]
                            lesson_explanations = x["explanation"]
                            break

                    # set child's last activity as lesson and their last lesson as the subject title
                    try:
                        mycursor = mydb.cursor()
                        sql = "UPDATE child SET last_lesson = %s WHERE child_name = %s"
                        val = (lesson_title, "Alison")
                        mycursor.execute(sql, val)
                        mydb.commit()

                        count = 0
                        correct_answers = 0
                        # start asking lesson questions
                        for y in lesson_questions:
                            speak(y)
                            # listen for answer
                            answer = listen()
                            # if child's answer corresponds the correct answer say that
                            if answer == lesson_answers[count]:
                                speak("Correct")
                                # increment the value of correct answers
                                correct_answers = correct_answers + 1
                            else:
                                # if the answer is wrong provide an explanation to retrieve the correct answer
                                speak(lesson_explanations[count])
                                # tell arduino to shake head
                                play(wrong_answer)
                                arduino.write(b'b')
                            # increment the count variable for the question number
                            count = count + 1
                        # tell the student the amount of questions they got right and tell arduino to dance
                        speak("Well done, you got " + str(correct_answers) + " out of five questions correct.")
                        arduino.write(b'c')

                        play(upbeat)

                    except:
                        speak("Lesson not found for your age range")

            else:
                # if the child's face could not be identified get details of person found
                arduino.write(b'd')
                speak("Hello Friend. What is your name?")
                child_name = listen()
                speak("Nice to meet you" + str(child_name) + ". How old are you?")
                age = listen()

                mycursor = mydb.cursor()
                # get age of identified child
                # add new child to table with provided details
                sql = "INSERT into child (child_name, age) VALUES (%s, %s)"
                val = (child_name, 4)

                mycursor.execute(sql, val)
                mydb.commit()

                # ask child if they would like to have a lesson or a story
                speak("Would you like to have a lesson or read a story?")
                # wait for the person's choice
                words = listen()
                # loop through story dictionary looking for story
                if words == "story":
                    # check individual story
                    for x in stories:
                        # check ages array of each story (stores appropriate ages for story)
                        for i in x["ages"]:
                            # if age of child is found in the age range for each story
                            if int(i) == 9:
                                mycursor = mydb.cursor()

                                # store title of the chosen story
                                chosen_story = x["title"]

                                # get the body of the appropriate story from the database
                                sql = "SELECT body FROM story WHERE title ='" + chosen_story + "'"

                                mycursor.execute(sql)
                                # store retrieved story and start reading it
                                story = mycursor.fetchone()[0]
                                story = story.replace('\n', ' ')
                                speak(story)

                                # set having a story as last activity and last story as the story title
                                sql = "UPDATE child SET last_activity = %s WHERE child_name = %s"
                                val = ("story", child_name)
                                mycursor.execute(sql, val)
                                mydb.commit()

                elif words == "lesson":
                    # loop through each lesson
                    for x in lessons:
                        # check ages in lesson and compare with child's age
                        for i in x["ages"]:
                            # loop until a lesson that matches age range is found
                            if int(i) == 6:
                                lesson_title = x["subject"]
                                lesson_questions = x["questions"]
                                lesson_answers = x["answers"]
                                lesson_explanations = x["explanation"]
                                break
                    # set child's last activity as lesson and their last lesson as the subject title
                    try:
                        mycursor = mydb.cursor()
                        sql = "UPDATE child SET last_lesson = %s WHERE child_name = %s"
                        val = (lesson_title, child_name)
                        mycursor.execute(sql, val)
                        mydb.commit()

                        count = 0
                        correct_answers = 0
                        # start asking lesson questions
                        for y in lesson_questions:
                            speak(y)
                            # listen for answer
                            answer = listen()
                            # if child's answer corresponds the correct answer say that
                            if answer == lesson_answers[count]:
                                speak("Correct")
                                # increment the value of correct answers
                                correct_answers = correct_answers + 1
                            else:
                                # if the answer is wrong provide an explanation to retrieve the correct answer
                                speak(lesson_explanations[count])
                                # tell arduino to shake head
                                play(wrong_answer)
                                arduino.write(b'b')
                            # increment the count variable for the question number
                            count = count + 1
                        # tell the student the amount of questions they got right and tell arduino to dance
                        speak("Well done, you got " + str(correct_answers) + " out of five questions correct.")
                        play(upbeat)
                        arduino.write(b'c')

                    except:
                        speak("Lesson not found for your age range")

    else:
        # if object not found wait one minute and search again
        time.sleep(60)
        print("Object not found")
