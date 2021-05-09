from igo import *
from threading import Timer
# importa l'API de Telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from datetime import datetime


#   Messages sent by the bot
START = '''Hi there! I'm iGo DJ, your favorite GPS from Barcelona (Spain)! 🤠
Type or press /help to get more information about what I can do 👌'''
HELP = '''This is what I can do for you! Type:
/start: To get a warm welcome from me 😘
/author: To know about my fantastic parents.
/go destination: Get the fastest route from your current location to the given destination (make sure its precise for both of them)
                 using the concept of itime, which takes into account the congestions of the city.
                 For example, try:
                     /go Sagrada Familia
                     /go 41.4036047312297, 2.174364514974909
/where: Shows your current location'''
AUTHORS = "Authors of iGo DJ: Dídac Alonso López & Jacinto Suñer Soler"

WARNING_GO = '''Error 💣 Please make sure you give the correct and precise name of the place you want to go or the pair latitude longitude. Here's an example:
                /go Sagrada Familia
                /go 41.4036047312297, 2.174364514974909
                '''
MISSING_USER_LOC = '''Error: Missing user location.
Please send us your location before using /go or /where, to do so you can press the safety pin icon and select the location.'''

WAIT_TIME_SECONDS = 300  # number of seconds between each update of the igraph


# Global variables
GRAPH = get_graph()
iGRAPH = None


def start(update, context):
    '''Gives a warm welcome to the customer.'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=START)


def help(update, context):
    '''Explains what the bot can do for the customer.'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=HELP)


def author(update, context):
    '''Shows to the costumer the authors of the bot'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=AUTHORS)


def go(update, context):
    '''Given the command /go followed by a destination, either in the format of an address or with the coordinates,
    returns information about the shortest path from the costumer's current location to the given destination.
    More precisely, the bot sends:
    1) An image with the route the costumer has to follow.
    2) The estimate time it takes to get to the destination.
    3) The estimate time arrival.
    4) The estimate distance from one place to another.
    '''
    print("Starting command /go...")

    try:
        lat, lon = query_to_location("/go", update, context)
        user_lat, user_lon = context.user_data['user_location']
        path_image, aprox_time, distance = get_shortest_path_with_itimes(iGRAPH,
                                                                         (user_lat, user_lon),
                                                                         (lat, lon))

        # Sends picture of the path and deletes it from the directory
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(path_image, 'rb'))
        os.remove(path_image)

        # Gives the estimate time
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Estimated time: " + str(aprox_time))

        # Gives the estimate time arrival
        aprox_arrival = datetime.now() + aprox_time
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Estimated time arrival: {:d}:{:02d}:{:02d}".format(aprox_arrival.hour,
                                                                                          aprox_arrival.minute,
                                                                                          aprox_arrival.second))
        # Gives the distance to the destination
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Distance: {round(distance/1000, 1)} km")

    except:
        print("---Error in /go query---")
        context.bot.send_message(chat_id=update.effective_chat.id, text=WARNING_GO)

    print("...Command /go finished")

    return


def where(update, context):
    try:
        image_filename = get_location_image(context.user_data['user_location'])
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_filename, 'rb'))
        os.remove(image_filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=MISSING_USER_LOC)
    return


def pos(update, context):
    try:
        context.user_data['user_location'] = query_to_location("/pos", update, context)
    except:
        print("Error with the position")
    return


def user_location(update, context):
    '''aquesta funció es crida cada cop que arriba una nova localització d'un usuari'''

    # aquí, els missatges són rars: el primer és de debò, els següents són edicions
    message = update.edited_message if update.edited_message else update.message
    # extreu la localització del missatge
    context.user_data['user_location'] = message.location.latitude, message.location.longitude


def filter_coordinates(x):
    '''Filters the given string from unnecesary characters'''
    for c in "()*,-+'/":
        x = x.replace(c, "")
    return x


def query_to_location(command, update, context):
    '''Converts the given location by the user into a tuple of coordinates (latitude, lontitude).
       The command can be "/go", "/pos", or another one if it uses this method'''

    print("Converting query to location...")

    command += " "

    try:  # if the string given is in the format (latitude, longitude)
        query = context.args
        query = list(map(lambda x: filter_coordinates(x), query))
        lat, lon = float(query[0]), float(query[1])
    except:  # the string given is a query
        # we delete the command from the whole message given by the user
        lat, lon = get_lat_lon(update.message.text.replace(command, ""))

    print("...query converted")

    return lat, lon


def update_igraph():
    ''''''
    print("Updating the igraph")
    global iGRAPH
    iGRAPH = get_igraph(GRAPH)
    print("Igraph updated")
    Timer(WAIT_TIME_SECONDS, update_igraph).start()


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
