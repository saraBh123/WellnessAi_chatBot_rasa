from pymongo import MongoClient 
from deep_translator import GoogleTranslator
#connexion à MongoDB
try:
    client = MongoClient('mongodb://localhost',27017)
    db = client.ChatbotRasa
    col = db.healthcare 
except:
    print("erreur de connexion") 
#Nom de l'intention à extraire 
intent_name = 'definition_healthcare'
# Recuperation des exemples pour l'intention donné
try:
    examples = col.find()
except:
    print('erreur de rechercher')
# Ajouter les exemples de intent definition_healthcare
with open('data/definition_healthcare.yml','a', encoding='utf-8') as file:
    file.write('\n- intent: '+intent_name + '\n  examples: | \n')
    for example in examples:
        titre = example['Titre']
        file.write('    - ['+ titre +'](title)\n')
        file.write('    - ['+ GoogleTranslator(source='auto', target='fr').translate(titre) +'](title)\n')
        file.write('    - ['+ GoogleTranslator(source='auto', target='ar').translate(titre) +'](title)\n')
           
               
  
           