import os
import telebot
from telebot import types
from bs4 import BeautifulSoup as bs
import requests
import json
from datetime import datetime
from googletrans import Translator
from server import server
import time

headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }

API_KEY = os.environ.get('API_KEY')
BASE = os.environ.get('BASE')
CHATID = os.environ.get('CHATID')
bot = telebot.TeleBot(API_KEY)

server()
file = []

def get_url(name):
    url = BASE + name.replace(" ", "%20")
    return url

def first_page(name):
    #first page:
    time.sleep(0.01)
    r = requests.get(get_url(name), headers=headers)
    if r.status_code == 200:
        soup = bs(r.content, features='html.parser')
        data = soup.text
        parsed_json = json.loads(data)
        global searchq
        global links
        global photos
        searchq = []
        links = []
        photos = []
        global results_counter
        results_counter = len(parsed_json['response']['sections'][1]['hits'])
        print(results_counter)
        for x in range(results_counter):
            link = parsed_json['response']['sections'][1]['hits'][x]['result']['url']
            info = parsed_json['response']['sections'][1]['hits'][x]['result']['full_title']
            photo = parsed_json['response']['sections'][1]['hits'][x]['result']['song_art_image_url']
            links.append(link)
            searchq.append(info)
            photos.append(photo)
        if results_counter == 0:
            return "Sorry, no matches :)"
        
        print(searchq)
        
    else:
        print("Server error")
        return "Sorry, server error :)"

def second_page(link):
    #second page (Entering the link):
    time.sleep(0.01)
    print(link)
    r1 = requests.get(link, headers=headers)
    if r1.status_code == 200:
        soup1 = bs(r1.content, features='lxml')
        #About the song:
        global about 
        try:
            about = soup1.find('div', 'SongDescription__Content-sc-615rvk-2 kRzyD').get_text()
            if about == None:
                about = 'Sorry, couldn\'t find data.'
        except:
            about = 'Sorry, couldn\'t find data.'

        #Album tracklist:
        global album 
        try:
            album = soup1.find('ol', 'AlbumTracklist__Container-sc-123giuo-0 kGJQLs')
            if album == None:
                album = 'Sorry, couldn\'t find data.'
            else:
                album_fixed = str(album).replace('</li>','\n')
                convert_album = bs(album_fixed, features='html.parser')
                album = convert_album.text
        except:
            album = 'Sorry, couldn\'t find data.'

        #Lyrics
        try:
            lyrics_raw = soup1.find("div", class_="PageGriddesktop-a6v82w-0 SongPageGriddesktop-sc-1px5b71-0 Lyrics__Root-sc-1ynbvzw-0 UljRP")
            lyrics_raw.find("div", class_="LyricsHeader__Container-ejidji-1 eOUfVo").decompose()
            lyrics_raw.find("div", class_="Lyrics__Footer-sc-1ynbvzw-1 jOTQyT").decompose()
            try:
                lyrics_raw.find("aside", class_="RecommendedSongs__Container-fhtuij-0 fUyrrM Lyrics__Recommendations-sc-1ynbvzw-17 glqGdw").decompose()
            except:
                pass
        except:
            if lyrics_raw == None:
                lyrics_raw = soup1.find('div', 'LyricsPlaceholder__Message-uen8er-3 jlYyFx')
        print(lyrics_raw)
        lyrics_fixed = str(lyrics_raw).replace('<br/>', '\n')
        convert = bs(lyrics_fixed, features='html.parser')
        lyrics = convert.text
        file.append(lyrics)

    else:
        print("Server error")
        return "Sorry, Server error :)"
        
def tbot():
    @bot.message_handler(commands=['start'])
    def start(message):
        smsg = "Hey, I am LyricsG Bot\nSend me the name of the song and I will get its lyrics for you <3\n(You can send with artist name for more accuarcy)."
        bot.reply_to(message, smsg)
        print(str(message.chat.username) + " start")

    @bot.message_handler()
    def reply(message):
        name = message.text
        print(str(message.chat.username) + ' - ' + name)
        first_page(name)
        userId = message.chat.id
        nameUser = str(message.chat.first_name) + ' ' + str(message.chat.last_name)
        username = message.chat.username
        text = message.text
        date = datetime.now()
        data = f'User id: {userId}\nUsermae: {username}\nName: {nameUser}\nText: {text}\nDate: {date}'
        bot.send_message(chat_id=CHATID, text=data)
        #Serch kb:
        markup = types.InlineKeyboardMarkup()
        count = 0
        for value in searchq:
            markup.add(types.InlineKeyboardButton(text=value,callback_data='result'+str(count)))
            count += 1
        markup.add(types.InlineKeyboardButton(text='Close', callback_data='result_no'))
        #More info kb:
        global keyboard
        keyboard = types.InlineKeyboardMarkup()
        button0 = types.InlineKeyboardButton(text='About the song', callback_data='click0')
        button1 = types.InlineKeyboardButton(text='Album tracklist', callback_data='click1')
        button2 = types.InlineKeyboardButton(text='Translation (beta)', callback_data='click2')
        button3 = types.InlineKeyboardButton(text='Done', callback_data='click3')
        keyboard.add(button0, button1, button2, button3)
        global long_keyboard
        long_keyboard = types.InlineKeyboardMarkup()
        long_keyboard.add(button0, button1, button3)
        if results_counter != 0:
            bot.reply_to(message, 'Choose your song:', reply_markup=markup)
        else:
            bot.reply_to(message, 'Sorry, no matches :)')


    @bot.callback_query_handler(func=lambda call: True)
    def callback_data(call):
        if call.message:
            global lyricsfr
            if call.data == 'result_no':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            if call.data == 'result0':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                second_page(links[0])
                file.insert(0, searchq[0] + ' | Lyrics:\n\n')
                lyricsfr = "".join(line for line in file)
                file.clear()
                bot.send_photo(chat_id=call.message.chat.id, photo=photos[0])
                if len(lyricsfr) > 4096:
                    for x in range(0, len(lyricsfr), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=lyricsfr[x:x+4096])
                    bot.send_message(chat_id=call.message.chat.id, text="More stuff to see:\n\n", reply_markup=long_keyboard)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=lyricsfr, reply_markup=keyboard)
            if call.data == 'result1':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                second_page(links[1])
                file.insert(0, searchq[1] + ' | Lyrics:\n\n')
                lyricsfr = "".join(line for line in file)
                file.clear()
                bot.send_photo(chat_id=call.message.chat.id, photo=photos[1])
                if len(lyricsfr) > 4096:
                    for x in range(0, len(lyricsfr), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=lyricsfr[x:x+4096])
                    bot.send_message(chat_id=call.message.chat.id, text="More stuff to see:\n\n", reply_markup=long_keyboard)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=lyricsfr, reply_markup=keyboard)
            if call.data == 'result2':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                second_page(links[2])
                file.insert(0, searchq[2] + ' | Lyrics:\n\n')
                lyricsfr = "".join(line for line in file)
                file.clear()
                bot.send_photo(chat_id=call.message.chat.id, photo=photos[2])
                if len(lyricsfr) > 4096:
                    for x in range(0, len(lyricsfr), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=lyricsfr[x:x+4096])
                    bot.send_message(chat_id=call.message.chat.id, text="More stuff to see:\n\n", reply_markup=long_keyboard)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=lyricsfr, reply_markup=keyboard)
            if call.data == 'result3':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                second_page(links[2])
                file.insert(0, searchq[3] + ' | Lyrics:\n\n')
                lyricsfr = "".join(line for line in file)
                file.clear()
                bot.send_photo(chat_id=call.message.chat.id, photo=photos[2])
                if len(lyricsfr) > 4096:
                    for x in range(0, len(lyricsfr), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=lyricsfr[x:x+4096])
                    bot.send_message(chat_id=call.message.chat.id, text="More stuff to see:\n\n", reply_markup=long_keyboard)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=lyricsfr, reply_markup=keyboard)
            if call.data == 'result4':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                second_page(links[4])
                file.insert(0, searchq[4] + ' | Lyrics:\n\n')
                lyricsfr = "".join(line for line in file)
                file.clear()
                bot.send_photo(chat_id=call.message.chat.id, photo=photos[4])
                if len(lyricsfr) > 4096:
                    for x in range(0, len(lyricsfr), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=lyricsfr[x:x+4096])
                    bot.send_message(chat_id=call.message.chat.id, text="More stuff to see:\n\n", reply_markup=long_keyboard)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=lyricsfr, reply_markup=keyboard)
            
            if call.data == 'click0':
                bot.send_message(chat_id=call.message.chat.id, text='About the song:\n' + about)
            if call.data == 'click1':
                bot.send_message(chat_id=call.message.chat.id, text='Album tracklist:\n' + album)
            if call.data == 'click2':
                kb_tanslate = types.InlineKeyboardMarkup()
                button2_1 = types.InlineKeyboardButton(text='Translate to English', callback_data='click2_1')
                button2_2 = types.InlineKeyboardButton(text='Translate to Arabic', callback_data='click2_2')
                button2_3 = types.InlineKeyboardButton(text='Translate to French', callback_data='click2_3')
                button2_4 = types.InlineKeyboardButton(text='Translate to Spanish', callback_data='click2_4')
                button2_0 = types.InlineKeyboardButton(text='Go back', callback_data='click2_0')
                kb_tanslate.add(button2_1, button2_2, button2_3, button2_4, button2_0)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=lyricsfr, reply_markup=kb_tanslate)
            translator = Translator()
            if call.data == 'click2_1':
                en = translator.translate(lyricsfr, dest='en').text
                bot.send_message(chat_id=call.message.chat.id, text="English translation:\n\n" + en)
            if call.data == 'click2_2':
                ar = translator.translate(lyricsfr, dest='ar').text
                bot.send_message(chat_id=call.message.chat.id, text="Arabic translation:\n\n" + ar)
            if call.data == 'click2_3':
                fr = translator.translate(lyricsfr, dest='fr').text
                bot.send_message(chat_id=call.message.chat.id, text="French translation:\n\n" + fr)
            if call.data == 'click2_4':
                es = translator.translate(lyricsfr, dest='es').text
                bot.send_message(chat_id=call.message.chat.id, text="Spanish translation:\n\n" + es)
            if call.data == 'click2_0':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=lyricsfr, reply_markup=keyboard)
            if call.data == 'click3':
                if len(lyricsfr) > 4096:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                else:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=lyricsfr)
    print('Bot is running...')
    bot.infinity_polling()

tbot()