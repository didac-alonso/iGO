from igo import *
# importa l'API de Telegram
from telegram.ext import Updater, CommandHandler



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
/go destination: Get the fastest route from your current location to the given destination
                 e.g: go Campus Nord
/where: Shows your current location
'''
AUTHORS = "Authors of iGo DJ: Dídac Alonso López & Jacinto Suñer Soler"

# Global variables
GRAPH = None

def start(update, context):
    '''Loads the graph used for the GPS...defineix una funció que saluda i que s'executarà quan el bot rebi el missatge /start'''
    global GRAPH
    GRAPH = get_graph()
    plot_graph(GRAPH)
    print('hello')
    context.bot.send_message(chat_id=update.effective_chat.id, text=START)
    return GRAPH
    

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=HELP)


def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=AUTHORS)

def go(update, context):
    pass

def where(update, context):
    pass

def pos(update, context):
    pass



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



# engega el bot
updater.start_polling()

def main():
    pass
            