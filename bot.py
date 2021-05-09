from igo import *
from threading import Timer
import time
# importa l'API de Telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, MessageFilter, Filters, ConversationHandler
import os
from datetime import datetime



# /go destí: mostra a l'usuari un mapa per arribar de la seva posició actual fins al punt de destí escollit pel camí més curt segons el concetpe de ispeed. Exemples:
# /go Campus Nord
# /go Sagrada Família
# /go Pla de Palau, 18 (Facultat de Nàutica)
# /where: mostra la posició actual de l'usuari.
# També hi ha una comanda secreta que permet falsejar la posició actual de l'usuari, de forma que es puguin fer proves facilment sense haver de sortir de casa:

# /pos: fixa la posició actual de l'usuari a una posició falsa. Exemples:
# /pos Campus Nord
# /pos 41.38248 2.18511 (Facultat de Nàutica)

#   Messages sent by the bot
START = '''Hi there! I'm iGo DJ, your favorite GPS from Barcelona (Spain)! 🤠
Type or press /help to get more information about what I can do.'''
HELP = '''This is what I can do for you! Type:
/start: To get a warm welcome from me 😘 and to load the GPS
/author: To know about my fantastic parents
/go destination: Get the fastest route from your current location to the given destination (make sure its precise for both of them)
                 /go Sagrada Familia
                 /go 41.4036047312297, 2.174364514974909
/where: Shows your current location'''
AUTHORS = "Authors of iGo DJ: Dídac Alonso López & Jacinto Suñer Soler"
WARNING_GO = '''Error 💣 Please make sure you give the correct and precise name of the place you want to go or the pair latitude longitude. Here's an example:
                /go Sagrada Familia
                /go 41.4036047312297, 2.174364514974909
                '''
MISSING_USER_LOC = '''Error: Missing user location.
                    Please send us your location before using /go o /where, to do so you can press the safety pin icon and select the location'''
WAIT_TIME_SECONDS = 300 # number of seconds between each update of the igraph


# Global variables
GRAPH = get_graph()
iGRAPH = None

def start(update, context):
    '''Simply'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=START)
    

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=HELP)


def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=AUTHORS)

def go(update, context):
    try:
        lat, lon = query_to_location("/go ", update, context)
        user_lat, user_lon = context.user_data['user_location']
        path_image, aprox_time, distance = get_shortest_path_with_itimes(iGRAPH, (user_lat, user_lon), (lat, lon))
        context.bot.send_photo(chat_id = update.effective_chat.id, photo = open(path_image, 'rb'))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Estimated time: " + str(aprox_time))
        aprox_arrival = datetime.now() + aprox_time
        context.bot.send_message(chat_id=update.effective_chat.id, text="Estimated time arrival: {:d}:{:02d}:{:02d}".format(aprox_arrival.hour, aprox_arrival.minute, aprox_arrival.second))
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Distance: {round(distance/1000, 1)} km")
        os.remove(path_image)

    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=WARNING_GO)
    return

def filter_coordinates(x):
    '''Filters the given string from unnecesary characters'''
    for c in "()*,-+'/": x = x.replace(c, "")
    return x

def query_to_location(command, update, context):
    try: # if the string given is in the format (latitude, longitude)
        query = context.args
        query = list(map(lambda x : filter_coordinates(x), query))
        lat, lon = float(query[0]), float(query[1])
    except: #the string given is a query
        lat, lon = get_lat_lon(update.message.text.replace(command, ""))
    return lat, lon


def where(update, context):
    try:
        image_filename = get_location_image(context.user_data['user_location'])
        context.bot.send_photo(chat_id = update.effective_chat.id, photo = open(image_filename, 'rb'))
        os.remove(image_filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text = MISSING_USER_LOC)
    return
    
    

def pos(update, context):
    try:
        context.user_data['user_location'] = query_to_location("/pos ", update, context)
    except:
        print("Error with the position")
    return  

def user_location(update, context):
    '''aquesta funció es crida cada cop que arriba una nova localització d'un usuari'''

    # aquí, els missatges són rars: el primer és de debò, els següents són edicions
    message = update.edited_message if update.edited_message else update.message
    # extreu la localització del missatge
    context.user_data['user_location'] = message.location.latitude, message.location.longitude


def update_igraph(): 
    print("Pillant el igraph")
    global iGRAPH
    iGRAPH = get_igraph(GRAPH)
    print("Graph updated")
    Timer(WAIT_TIME_SECONDS, update_igraph).start()


# ticker = threading.Event()
# while not ticker.wait(WAIT_TIME_SECONDS):
update_igraph()

# declara una constant amb el access token que llegeix de token.txt
TOKEN = open('token.txt').read().strip()

# crea objectes per treballar amb Telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# indica que quan el bot rebi la comanda /start s'executi la funció start
dispatcher.add_handler(CommandHandler('start', start))

# help
dispatcher.add_handler(CommandHandler('help', help))

dispatcher.add_handler(CommandHandler('author', author))

dispatcher.add_handler(CommandHandler('go', go))

dispatcher.add_handler(CommandHandler('where', where))

dispatcher.add_handler(CommandHandler('pos', pos))

dispatcher.add_handler(MessageHandler(Filters.location, user_location))


# engega el bot
updater.start_polling()

def main():
    pass
            