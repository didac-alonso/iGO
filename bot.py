from igo import *
from threading import Timer
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from datetime import datetime

# Messages sent by the bot
START = '''Hi there! I'm iGo DJ, your favorite GPS from Barcelona (Spain)! 🤠
Type or press /help to get more information about what I can do 👌
Please send us your location first, to do so you can press the safety pin icon and select the location.'''

HELP = '''This is what I can do for you! Type:

/start:
To get a warm welcome from me 😘

/author:
To know about my fantastic parents.

/go destination:
Get the fastest route from your current location
to the given destination (make sure its precise for both of them)
using the concept of itime, which takes into account the congestions of the city.

Please make sure you give the correct and precise name of the place you want to go (as an address) or using coordinates.
IMPORTANT: in the case of coordinates, give them in the order latitude, longitude.
           For example, try:
           /go Sagrada Familia
           /go 41.4036047312297, 2.174364514974909

NOTE: The estimated time might be inaccurate.

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

# Necessary items to work with Telegram
TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
    '''
    Gives a warm welcome to the user and gives him further instructions such
    as sending his location before using any functionality.
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text=START)


def help(update, context):
    '''Explains what the bot can do for the user.'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=HELP)


def author(update, context):
    '''Shows to the user the authors of the bot.'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=AUTHORS)


def go(update, context):
    '''
    Given the command /go followed by a destination, either in the format of an address or with the coordinates,
    returns information about the shortest path from the user's current location to the given destination.
    More precisely, the bot sends:
    1) An image with the route the costumer has to follow.
    2) The estimate time it takes to get to the destination.
    3) The estimate time arrival.
    4) The estimate distance from one place to another.
    NOTE: The estimated time might be inaccurate.
    '''
    # This print is for testing purposes, uncomment it in order to see when this command is being executed
    # print("Starting command /go...")

    # Check we have the current user location
    try:
        user_lat, user_lon = context.user_data['user_location']
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=MISSING_USER_LOC)
        print("Missing current user location on command /go")
        return

    try:
        lat, lon = query_to_location("/go", update, context)
        path_image, aprox_time, distance = get_shortest_path_with_itimes(iGRAPH,
                                                                         (user_lat, user_lon),
                                                                         (lat, lon))
    except:
        print("---Error in /go query---")
        context.bot.send_message(chat_id=update.effective_chat.id, text=WARNING_GO)
        return

    # Sends picture of the path and deletes it from the directory
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(path_image, 'rb'))
    os.remove(path_image)

    # Gives the estimate time
    if aprox_time.seconds//3600 == 0:  # estimate time is less than an hour
        str_aprox_time = "Estimated time: {:d} minutes".format(aprox_time.seconds//60)
    else:
        str_aprox_time = "Estimated time: {:d} hours and {:02d} minutes".format(aprox_time.seconds//3600,
                                                                                aprox_time.seconds//60)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=str_aprox_time)

    # Gives the estimate time arrival
    aprox_arrival = datetime.now() + aprox_time
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Estimated time arrival: {:d}:{:02d}".format(aprox_arrival.hour,
                                                                               aprox_arrival.minute))

    # Gives the distance to the destination
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Distance: {round(distance/1000, 1)} km")

    # Gives further information about the colors of the map
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Origin          ➡️ {ORIGIN_COLOR} \nDestination ➡️ {DESTINATION_COLOR}")

    # This print is for testing purposes, uncomment it in order to see when this command is being executed
    # print("...Command /go finished")
    return


def where(update, context):
    '''
    Sends an image of the current user's location in the map.
    If the user has not given its location it sends an error message to the user.
    '''
    try:
        image_filename = get_location_image(context.user_data['user_location'])

        # Sends picture of the location and deletes it from the directory
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open(image_filename, 'rb'))
        os.remove(image_filename)

    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=MISSING_USER_LOC)
    return


def pos(update, context):
    '''
    This method is for testing purposes, is called sending /pos location to the bot,
    it will save a fictitious user's location, specified by location.
    If the location given is not found or is mispelled, it notifies an error via python terminal.
    '''

    try:
        context.user_data['user_location'] = query_to_location("/pos", update, context)
    except:
        print("Error with the position given by command /pos")
    return


def user_location(update, context):
    '''
    This method is called every time the user sends a new location. It is adapted to work
    with static and dynamic location and it saves it.
    '''

    # Takes the message of the user.
    # If its dynamic, the updates are considered as an edition of the message.
    message = update.edited_message if update.edited_message else update.message

    # Takes the location from the message and saves it.
    context.user_data['user_location'] = message.location.latitude, message.location.longitude


def filter_coordinates(x):
    '''Filters the given string from unnecesary characters.'''
    for c in "()*,-+'/":
        x = x.replace(c, "")
    return x


def query_to_location(command, update, context):
    '''
    Converts the given location by the user into a tuple of coordinates (latitude, longitude).
    The command can be "/go", "/pos", or another one if it uses this method.
    '''

    # This print is for testing purposes, uncomment it in order to see when this command is being executed
    # print("Converting query to location...")

    command += " "

    query = context.args

    assert query != [], "You haven't given a location"

    try:  # if the string given is in the format (latitude, longitude)
        query = list(map(lambda x: filter_coordinates(x), query))
        lat, lon = float(query[0]), float(query[1])

    except:  # if the string given is a query
        # the command is deleted from the whole message given by the user,
        # and we make sure the address is from PLACE (see global variable in igo module).
        lat, lon = get_lat_lon(update.message.text.replace(command, "") + ", " + PLACE)

    # This print is for testing purposes, uncomment it in order to see when this command is being executed
    # print("...query converted")

    return lat, lon


def update_igraph():
    '''
    This method is called every 5 minutes in another thread in order to make the bot fluid while the
    igraph is updating. It updates the igraph with the newest highways and congestions information.
    '''
    # This print is for testing purposes, uncomment it in order to see when this command is being executed
    # print("Updating the igraph")

    global iGRAPH

    iGRAPH = get_igraph(GRAPH)

    # This print is for testing purposes, uncomment it in order to see when this command is being executed
    # print("Igraph updated")

    # This commands sets a task that will be executed in background every 5 minutes. The task is the method itself,
    # so it will update the graph every 5 minutes.
    Timer(WAIT_TIME_SECONDS, update_igraph).start()


# The first time the igraph must be updated "manually". Then, the Timer, updates it every 5 minutes.
update_igraph()


# Indicates the bot will execute the specified methods (second parameter)
# when it receives the message /command (first parameter)
dispatcher.add_handler(CommandHandler('start', start))

dispatcher.add_handler(CommandHandler('help', help))

dispatcher.add_handler(CommandHandler('author', author))

dispatcher.add_handler(CommandHandler('go', go))

dispatcher.add_handler(CommandHandler('where', where))

dispatcher.add_handler(CommandHandler('pos', pos))

# Indicates the bot must execute user_location method when it receives a location
dispatcher.add_handler(MessageHandler(Filters.location, user_location))


# turns on the bot
updater.start_polling()
