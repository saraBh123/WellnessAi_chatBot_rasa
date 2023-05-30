from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pymongo
import detectlanguage
from langdetect import detect
from iso639 import languages
import random
from deep_translator import GoogleTranslator
from geopy.distance import geodesic

#Connection to DataBase healthcare
def ConnectionHealth():
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017')
        db = client.ChatbotRasa
        col = db.healthcare
    except KeyError:
        return ('Sorry !! Error de cnx ')
    
    return col

#Connection to DataBase Location
def ConnectionPosition():
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017')
        db = client.ChatbotRasa
        col = db.hospitals
    except KeyError:
        return ('Sorry !! Error de cnx ')
    
    return col

def detectLang(text):
    detectlanguage.configuration.api_key = "b736cf47c1b5d9c9004fc35598c68fbb"

    ds = detectlanguage.detect(text)

    for lang in ds:
        if lang['isReliable']:
            langcode = lang['language']
    return langcode

class ActionDefinitionHealthcare(Action):

    def name(self) -> Text:
        return "action_def_health"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        titre = tracker.latest_message.get('text')
        td = GoogleTranslator(source='auto', target='en').translate(titre)
        
        #Function Connect
        col = ConnectionHealth()
        try:
            x = col.find_one({"Titre":td})
            if(td == None):
                print( 'titre est vide')
            else:
                print(titre)
        except KeyError:
            dispatcher.utter_message(text='Sorry !! Error de recharche ')
        
        #Detect language of message
        lang = detect(titre)
        
        #Find Title from DataBase
        print(lang)
        des = x['Description']
        if lang=='en':
            dispatcher.utter_message(text = des)
            dispatcher.utter_message(text = 'But it is crucial to consult a human doctor in dangerous situations ')
        else:
            trans = GoogleTranslator(source='auto', target=lang).translate(des)
            resp = GoogleTranslator(source='auto', target=lang).translate('But it is crucial to consult a human doctor in dangerous situations')
            dispatcher.utter_message(text = trans)
            print(trans)
            dispatcher.utter_message(text = resp)

        return []

class ActionDetectLanguage(Action):

    def name(self) -> Text:
        return "action_detect_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get("text")
                
        langcode = detectLang(text)
        langname = languages.get(alpha2=langcode).name
        langname = langname if "(" not in langname else langname.split(" ")[0]

        return [SlotSet("langcode", langcode), SlotSet("langname",langname)]

# the false greet by user
class ActionFalseGreet(Action):

    def name(self) -> Text:
        return "action_false_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        t = tracker.latest_message.get("text")
        res1 = '\''+t +'\',Je ne suis pas sûr de comprendre ce que vous voulez dire. Mais je pense que c\'est une salutation.\nAlors bienvenue'
        res2 = '\''+t +'\',I\'m not sure I understand what you mean. But I think it\'s a greeting.\nSo welcome'
        res3 = '\''+t +'\',لست متأكدًا من أنني أفهم ما تعنيه. لكني أعتقد أنها تحية.\nإذا أهلا وسهلا بك'
        t1 = [res1,res2,res3]
        response = random.choice(t1)
        
        dispatcher.utter_message(text= res1)
        dispatcher.utter_message(text= res2)
        dispatcher.utter_message(text= res3)
        
# entre name of user
class ActionGiveName(Action):

    def name(self) -> Text:
        return "action_give_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot('name')
        text = tracker.latest_message.get('text')
        lang = detectLang(text)
        if lang == 'en':
            en = ['Nice to meet you, '+name+'!','Happy to talk to you, '+name+'!','Welcome, '+name+'!']
            dispatcher.utter_message(text= random.choice(en))
            dispatcher.utter_message(text= 'How can I help you today')
        elif lang == 'ar':
            ar = ['مرحبًا '+name+'!','يسعدني التحدث إليك ، '+name+'!','تشرفت بمقابلتك ، '+name+'!']
            dispatcher.utter_message(text= random.choice(ar))
            dispatcher.utter_message(text= 'كيف استطيع مساعدتك اليوم')
        elif lang == 'fr':
            fr = ['Ravi de vous rencontrer, '+name+' !','Content de faire votre connaissance, '+name+' !','Bienvenue, '+name+' !','C\'est un plaisir de vous connaître, '+name+' !','Heureux de vous parler, '+name+'!']
            dispatcher.utter_message(text= random.choice(fr))
            dispatcher.utter_message(text= 'Comment puis-je vous aider aujourd\'hui ')
        else:
            dispatcher.utter_message(text= 'Enchanté, '+name+'!')
            dispatcher.utter_message(text= 'Comment puis-je vous aider aujourd\'hui ')


class ActionGetHospital(Action):

    def name(self) -> Text:
        return "action_get_hospital"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        text = tracker.latest_message.get('text')
        region = tracker.get_slot('region')
        lat = tracker.get_slot('latitude')
        long = tracker.get_slot('longitude')

        #Connection to mongodb
        col = ConnectionPosition()
        lang = detect(text)

        if lang == 'fr':
            dispatcher.utter_message(text="Très bien. Je vais chercher les hôpitaux à proximité votre position. Veuillez patienter un instant.")
            
            if region != None:
                dispatcher.utter_message(text='J\'ai trouvé quelques hôpitaux près de '+ region+'. Voici quelques-uns d\'entre eux :')
                for x in col.find({"Région":region}):
                    dispatcher.utter_message(text='  - '+x['Hopital'])
            else:
                hopitaux_proches = {}
                k = 1000
                while k <= 30000:
                    for x in col.find():
                        hospital_latitude = x["Latitude"]
                        hospital_longitude = x["Longitude"]
                        distance = geodesic((lat, long), (hospital_latitude, hospital_longitude)).meters
                        if distance <= k:
                            hopitaux_proches[distance] = x["Hopital"]
                    if hopitaux_proches:
                        dispatcher.utter_message(f"Voici les hôpitaux à moins de {k/1000} kilomètres :")
                        for distance, hopital in hopitaux_proches.items():
                            dispatcher.utter_message(f"- {hopital} (distance : {distance/1000} mètres)")
                        break
                    if hopitaux_proches == '':
                        dispatcher.utter_message(f"Je ne trouve aucun hôpital à {k/1000} kilomètres")    
                    k += 1000
        elif lang == 'en':
            dispatcher.utter_message(text="Alright, i'll look for hospitals near your location. Please wait a moment.")
            
            if region != None:
                dispatcher.utter_message(text='I found some hospitals near '+region+'. Here are some of them:')
                for x in col.find({"Région":region}):
                    dispatcher.utter_message(text='  - '+x['Hopital'])
            else:
                hopitaux_proches = {}
                k = 1000
                while k <= 30000:
                    for x in col.find():
                        hospital_latitude = x["Latitude"]
                        hospital_longitude = x["Longitude"]
                        distance = geodesic((lat, long), (hospital_latitude, hospital_longitude)).meters
                        if distance <= k:
                            hopitaux_proches[distance] = x["Hopital"]
                    if hopitaux_proches:
                        dispatcher.utter_message(f"Here are the hospitals within {k/1000} kilometers:")
                        for distance, hopital in hopitaux_proches.items():
                            dispatcher.utter_message(f"- {hopital} (distance: {distance} meters)")
                        break
                    if hopitaux_proches == '':
                        dispatcher.utter_message(f"I can't find any hospital within {k/1000} kilometers")
                    k += 1000
        elif lang == 'ar':
            dispatcher.utter_message(text="تمام. سأبحث عن مستشفيات قريبة من موقعك. فضلا انتظر لحظة.")
            
            if region != None:
                dispatcher.utter_message(text='لقد وجدت بعض المستشفيات بالقرب من '+ region +'. فيما يلي بعض منهم:')
                for x in col.find({"Région":region}):
                    dispatcher.utter_message(text='  - '+x['Hopital'])
            else:
                hopitaux_proches = {}
                k = 1000
                while k <= 30000:
                    for x in col.find():
                        hospital_latitude = x["Latitude"]
                        hospital_longitude = x["Longitude"]
                        distance = geodesic((lat, long), (hospital_latitude, hospital_longitude)).meters
                        if distance <= k:
                            hopitaux_proches[distance] = x["Hopital"]
                    if hopitaux_proches:
                        dispatcher.utter_message(f"إليك المستشفيات التي تقع في نطاق {k/1000} كيلومتر:")
                        for distance, hopital in hopitaux_proches.items():
                            dispatcher.utter_message(f"- {hopital} (المسافة: {distance} متر)")
                        break
                    if hopitaux_proches == '':
                        dispatcher.utter_message(f"لا يمكنني العثور على أي مستشفى في نطاق {k/1000} كيلومتر")
                    k += 1000
        return []

class ActionGetInfoHospital(Action):

    def name(self) -> Text:
        return "action_get_info_hospital"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        hospital = tracker.get_slot('hopitals')
        text = tracker.latest_message.get('text')
        #Connection to mongodb
        try:
            col = ConnectionPosition()
            x = col.find_one({'Hopital': hospital})
        except KeyError:
            dispatcher.utter_message(text='Sorry !! Error de cnx ')
            
        lang = detect(text)
        
        if lang == 'en':
            if x['Région'] is not None:
                dispatcher.utter_message('The' +hospital+' is a reputable healthcare facility offering a wide range of medical services. It belongs to the region of '+x['Region']+'.')
            dispatcher.utter_message(f"Here is information about the {hospital}:")
            if x['Type'] is not None:
                dispatcher.utter_message('- Type of hospital: '+x['Type'])
            if x['Avis'] is not None:
                dispatcher.utter_message("- Notice : "+x['Avis'])
            if x['Adressse'] is not None:
                dispatcher.utter_message("- Address : "+ x['Adressse'])
            if x['Open'] is not None:
                dispatcher.utter_message("- Hours of operation : "+ x['Open'])
            if x['Tel'] is not None:
                dispatcher.utter_message("- Phone : " + x['Tel'])
            if x['Site Web'] is not None:
                dispatcher.utter_message("- Website : "+ x['Site Web'])
            if x['Maps'] is not None :
                dispatcher.utter_message("- Link to Google Maps : "+ x['Maps'])
        elif lang == 'fr':
            if x['Région'] is not None:
                dispatcher.utter_message('L\''+ hospital+' est un établissement de santé réputé offrant une large gamme de services médicaux.Il appartient à la région de '+x['Région']+'.')
            dispatcher.utter_message(f"Voici des informations sur l'{hospital} :")
            if x['Type'] is not None:
                dispatcher.utter_message('- Type d\'hôpital : '+x['Type'])
            if x['Avis'] is not None:
                dispatcher.utter_message("- Avis : "+x['Avis'])
            if x['Adressse'] is not None:
                dispatcher.utter_message("- Adresse : "+ x['Adressse'])
            if x['Open'] is not None:
                dispatcher.utter_message("- Horaires d'ouverture : "+ x['Open'])
            if x['Tel'] is not None:
                dispatcher.utter_message("- Téléphone : " + x['Tel'])
            if x['Site Web'] is not None:
                dispatcher.utter_message("- Site web : "+ x['Site Web'])
            if x['Maps'] is not None :
                dispatcher.utter_message("- Lien vers Google Maps : "+ x['Maps'])
        elif lang == 'ar':    
            if x['Région'] is not None:
                dispatcher.utter_message('إن '+ hospital + 'هي منشأة رعاية صحية ذات سمعة طيبة تقدم مجموعة واسعة من الخدمات الطبية. وهي تنتمي إلى منطقة '+ x [' Region '] +'.')
            dispatcher.utter_message(f"هذه معلومات عن {hospital}:")
            if x['Type'] is not None:
                dispatcher.utter_message('- نوع المستشفى: '+x['Type'])
            if x['Avis'] is not None:
                dispatcher.utter_message("- إشعار : "+x['Avis'])
            if x['Adressse'] is not None:
                dispatcher.utter_message("- عنوان : "+ x['Adressse'])
            if x['Open'] is not None:
                dispatcher.utter_message("- اوقات الفتح : "+ x['Open'])
            if x['Tel'] is not None:
                dispatcher.utter_message("- هاتف :" + x['Tel'])
            if x['Site Web'] is not None:
                dispatcher.utter_message("- موقع إلكتروني : "+ x['Site Web'])
            if x['Maps'] is not None :
                dispatcher.utter_message("- رابط خرائط جوجل: "+ x['Maps'])

        return []