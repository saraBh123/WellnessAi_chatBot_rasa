#rasa run -m models --endpoints endpoints.yml --port 5002 --credentials credentials.yml
import requests
import speech_recognition as sr
import subprocess
from gtts import gTTS 
import pyttsx3
import time

bot_message = ""
message = ""

# creating Speak() function to giving Speaking power
# to our voice assistant
def Speak(audio):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume',1.0)
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    else:
        engine.setProperty('voice', voices[0].id)
    
    engine.say(audio)
    engine.runAndWait()

r = requests.post('http://localhost:5002/webhooks/rest/webhook', json={'message':'hello'})

print('Bot says :', end=' ')
for i in r.json():
    bot_message = i['text']
    print(f"{bot_message}")
   
Speak(bot_message)

while bot_message not in ["Bye", "thanks"]:
    r =sr.Recognizer()
    with sr.Microphone() as source:
        print("sepeak Anything:")
        time.sleep(1)  # pause de 1 seconde
        audio =r.listen(source)
        try:
            message = r.recognize_google(audio)
            print("you said : {}".format(message))
        except:
            print (" Sorry could not recognize your voice , try again ...")
    if len(message)==0 :
        continue
    print ('Sending message now ...')

    r = requests.post('http://localhost:5005/webhooks/rest/webhook', json={'message':message})
    print('Bot says ,',end=' ')
    for i in r.json():
        bot_message= i['text']
        print(f"{bot_message}")
    Speak(bot_message)

