from pymongo import MongoClient 
from deep_translator import GoogleTranslator
#connexion à MongoDB
try:
    client = MongoClient('mongodb://localhost',27017)
    db = client.ChatbotRasa
    col = db.hospitals 
except:
    print("erreur de connexion") 
#Nom de l'intention à extraire 
intent_name = 'hopitals'
# Recuperation des exemples pour l'intention donné
try:
    examples = col.find()
except:
    print('erreur de rechercher')
# Ajouter les exemples de intent definition_healthcare
with open('data/location.yml','a', encoding='utf-8') as file:
    file.write('\n- lookup: '+intent_name + '\n  examples: | \n')
    for example in examples:
        file.write('    - '+ example['Hopital'] +'\n')
        file.write('    - '+ GoogleTranslator(source='auto', target='fr').translate(example['Hopital']) +'\n')
        file.write('    - '+ GoogleTranslator(source='auto', target='ar').translate(example['Hopital']) +'\n')