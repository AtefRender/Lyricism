import os
import telebot
from telebot import types
from bs4 import BeautifulSoup as bs
import requests
import json
import re
from datetime import datetime
from googletrans import Translator
from server import server

headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }

headers_ar = {
    'referer': 'https://kalimat.anghami.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
}

API_KEY = os.environ.get('API_KEY')
BASE = os.environ.get('BASE')
BASE_AR = os.environ.get('BASE_AR')
CHATID = os.environ.get('CHATID')
bot = telebot.TeleBot(API_KEY)

server()

def get_url(name):
    url = BASE + name.replace(" ", "%20")
    return url

def get_url_ar(name_ar):
    url_ar = BASE_AR + name_ar
    return url_ar

def first_page(name):
    r = requests.get(get_url(name), headers=headers)
    if r.status_code == 200:
        soup = bs(r.content, features='html.parser')
        data = soup.text
        parsed_json = json.loads(data)
        global searchq, links, photos, results_counter 
        searchq, links, photos = ([] for i in range(3))
        results_counter = len(parsed_json['response']['sections'][1]['hits'])
        for x in range(results_counter):
            link = parsed_json['response']['sections'][1]['hits'][x]['result']['url']
            info = parsed_json['response']['sections'][1]['hits'][x]['result']['full_title'].replace('by', '-')
            photo = parsed_json['response']['sections'][1]['hits'][x]['result']['song_art_image_url']
            links.append(link)
            searchq.append(info)
            photos.append(photo)
        
        #Serch kb:
        markup = types.InlineKeyboardMarkup()
        ar_button = types.InlineKeyboardButton(text='ابحث عن أغانٍ عربية', callback_data='ar_result')
        close_button = types.InlineKeyboardButton(text='Close', callback_data='result_no')
        nmarkup = types.InlineKeyboardMarkup([[ar_button], [close_button]])
        count = 0
        for value in searchq:
            markup.add(types.InlineKeyboardButton(text=value,callback_data='result'+str(count)))
            count += 1
        markup.add(ar_button)
        markup.add(close_button)

    else:
        return "Sorry, server error :)"
    
    return markup, nmarkup

def second_page(link):
    #second page (Entering the link):
    r1 = requests.get(link, headers=headers)
    if r1.status_code == 200:
        soup1 = bs(r1.content, features='html.parser')

        #Lyrics
        try:
            lyrics_raw = soup1.find("div", class_=re.compile("^lyrics$|Lyrics__Root"))
            lyrics_raw.find("div", class_="LyricsHeader__Container-ejidji-1 eOUfVo").decompose()
            lyrics_raw.find("div", class_="Lyrics__Footer-sc-1ynbvzw-1 jOTQyT").decompose()
            try:
                lyrics_raw.find("aside", class_="RecommendedSongs__Container-fhtuij-0 fUyrrM Lyrics__Recommendations-sc-1ynbvzw-16 dtNvkO").decompose()
            except:
                pass
        except:
            if lyrics_raw == None:
                lyrics_raw = soup1.find('div', 'LyricsPlaceholder__Message-uen8er-3 jlYyFx')
        lyrics_fixed = str(lyrics_raw).replace('<br/>', '\n')
        convert = bs(lyrics_fixed, features='html.parser')
        lyrics = convert.text

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

    else:
        return "Sorry, Server error :)"
    
    return lyrics

def AR(url_ar):
    r_ar = requests.post(url_ar, headers=headers_ar)
    data_ar = r_ar.text
    parsed_json_ar = json.loads(data_ar)
    global ar_counter
    ar_counter = parsed_json_ar['sections'][0]['count']
    if ar_counter <= 5 and ar_counter != 0:
        ar_counter = ar_counter-1
    if ar_counter > 5:
        ar_counter = 0
        for x in range(5):
            try:
                if parsed_json_ar['sections'][0]['data'][x]['arabictext'] == 1:
                    ar_counter += 1
            except:
                pass
        if ar_counter != 0:
            ar_counter -= 1
        
    global songIds, infos_ar, picIds
    songIds, infos_ar, picIds= ([] for i in range(3))
    if ar_counter != 0:
        for x in range(ar_counter+1):
            try:
                if parsed_json_ar['sections'][0]['data'][x]['is_podcast'] == 1:
                    pass
            except:
                try:
                    if parsed_json_ar['sections'][0]['data'][x]['arabictext'] == 1:
                        songId = parsed_json_ar['sections'][0]['data'][x]['id']
                        artist = parsed_json_ar['sections'][0]['data'][x]['artist']
                        title = parsed_json_ar['sections'][0]['data'][x]['title']
                        picId = parsed_json_ar['sections'][0]['data'][x]['coverArt']
                        songIds.append(songId)
                        infos_ar.append(title + ' - ' + artist)
                        picIds.append(picId)
                except:
                    pass
    else:
        pass

def AR1(sId, pId, infos):
    pic_url = 'https://angartwork.anghcdn.co/?id=' + pId
    lyrics_url = 'https://kalimat.anghami.com/lyrics/' + sId
    ar_lyrics_req = requests.get(lyrics_url, headers=headers)
    soup_ar = bs(ar_lyrics_req.content, 'html.parser')
    try:
        ar_lryics = infos + ' | كلمات:\n\n' + soup_ar.find('pre', class_='lyrics-body_lyrics_body_container__e_Gwj').text
    except:
        ar_lryics = infos + ' | كلمات:\n\n' + soup_ar.find('h4', class_='error-page_error_page_subtitle__3REFJ').text
    return ar_lryics, pic_url

def tbot():
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_chat_action(message.chat.id, action='typing')
        smsg = "Lyricism is UP!\nSend me the name of a song and I will get its lyrics for you <3\n(You can send with artist name for more accuarcy)."
        bot.reply_to(message, smsg)
        
    @bot.message_handler(commands=['contact'])
    def contact(message):
        bot.send_chat_action(message.chat.id, action='typing')
        smsg = "Contact bot craetor to report a bug or suggest a feature:\n@TheAtef\nhttps://t.me/TheAtef"
        bot.reply_to(message, smsg)

    @bot.message_handler(commands=['donate'])
    def donate(message):
        bot.send_chat_action(message.chat.id, action='typing')
        smsg = "Thanks for consedring donating!\nHere is my Buy Me a Coffee link:\nhttps://www.buymeacoffee.com/TheAtef"
        bot.reply_to(message, smsg)

    @bot.message_handler()
    def reply(message):
        bot.send_chat_action(message.chat.id, action='typing')
        name = message.text
        global name_ar
        name_ar = message.text
        markup, nmarkup = first_page(name)

        #Sending searchq:
        if results_counter != 0:
            bot.reply_to(message, 'Choose your song:', reply_markup=markup)
        else:
            bot.reply_to(message, 'Sorry, no matches.', reply_markup=nmarkup)
        
        #Sending data:
        userId = message.chat.id
        nameUser = str(message.chat.first_name) + ' ' + str(message.chat.last_name)
        username = message.chat.username
        text = message.text
        date = datetime.now()
        data = f'User id: {userId}\nUsermae: {username}\nName: {nameUser}\nText: {text}\nDate: {date}'
        bot.send_message(chat_id=CHATID, text=data)


    @bot.callback_query_handler(func=lambda call: True)
    def callback_data(call):
        if call.message:
            if call.data == 'result_no':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            call_data = call.data
            
            global lyricsfr
            if call.data == 'result' + call_data[-1]:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_chat_action(call.message.chat.id, action='typing')

                #More info kb:
                global keyboard
                button0 = types.InlineKeyboardButton(text='About the song', callback_data='click0')
                button1 = types.InlineKeyboardButton(text='Album tracklist', callback_data='click1')
                button2 = types.InlineKeyboardButton(text='Translation (beta)', callback_data='click2')
                button3 = types.InlineKeyboardButton(text='Done', callback_data='click_done')
                keyboard = types.InlineKeyboardMarkup([[button0, button1, button2], [button3]])
                long_keyboard = types.InlineKeyboardMarkup()
                long_keyboard.add(button0, button1, button3)

                call_num = int(call_data[-1])
                lyrics = second_page(links[call_num])
                lyricsfr = searchq[call_num] + ' | Lyrics:\n\n' + lyrics
                bot.send_photo(chat_id=call.message.chat.id, photo=photos[call_num])
                if len(lyricsfr) > 4096:
                    for x in range(0, len(lyricsfr), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=lyricsfr[x:x+4096])
                    bot.send_message(chat_id=call.message.chat.id, text="More stuff to see:\n\n", reply_markup=long_keyboard)
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=lyricsfr, reply_markup=keyboard)

            if call.data == 'click_done':
                if len(lyricsfr) > 4096:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                else:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=lyricsfr)

            if call.data == 'ar_result':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_chat_action(call.message.chat.id, action='typing')
                #Ar_search kb:
                AR(get_url_ar(name_ar))
                if ar_counter == 0:
                    bot.send_message(chat_id=call.message.chat.id, text='عذراً، لم يتم العثور على نتائج')
                else:
                    ar_markup = types.InlineKeyboardMarkup()
                    counter = 0
                    for value in infos_ar:
                        ar_markup.add(types.InlineKeyboardButton(text=value,callback_data='ar_result'+str(counter)))
                        counter += 1
                    ar_markup.add(types.InlineKeyboardButton(text='إغلاق', callback_data='result_no'))
                    bot.send_message(chat_id=call.message.chat.id, text='اختر الأغنية:', reply_markup=ar_markup)

            if call.data == 'ar_result' + call_data[-1]:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_chat_action(call.message.chat.id, action='typing')
                call_num = int(call_data[-1])
                ar_lyrics, pic = AR1(songIds[call_num], picIds[call_num], infos_ar[call_num])
                bot.send_photo(chat_id=call.message.chat.id, photo=pic)
                if len(ar_lyrics) > 4096:
                    for x in range(0, len(ar_lyrics), 4096):
                        bot.send_message(chat_id=call.message.chat.id, text=ar_lyrics[x:x+4096])
                else:
                    bot.send_message(chat_id=call.message.chat.id, text=ar_lyrics)
            
            
            if call.data == 'click0':
                bot.send_chat_action(call.message.chat.id, action='typing')
                bot.send_message(chat_id=call.message.chat.id, text='About the song:\n' + about)
            if call.data == 'click1':
                bot.send_chat_action(call.message.chat.id, action='typing')
                bot.send_message(chat_id=call.message.chat.id, text='Album tracklist:\n' + album)
            if call.data == 'click2':
                global kb_tanslate
                button2_1 = types.InlineKeyboardButton(text='Translate to English', callback_data='click2_1')
                button2_2 = types.InlineKeyboardButton(text='Translate to Arabic', callback_data='click2_2')
                button2_3 = types.InlineKeyboardButton(text='Translate to French', callback_data='click2_3')
                button2_4 = types.InlineKeyboardButton(text='Translate to Spanish', callback_data='click2_4')
                button2_0 = types.InlineKeyboardButton(text='Go back', callback_data='click2_0')
                kb_tanslate = types.InlineKeyboardMarkup([[button2_1, button2_2], [button2_3, button2_4], [button2_0]])
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=lyricsfr, reply_markup=kb_tanslate)
            translator = Translator()
            if call.data == 'click2_1':
                bot.send_chat_action(call.message.chat.id, action='typing')
                en = translator.translate(lyricsfr, dest='en').text
                bot.send_message(chat_id=call.message.chat.id, text="English translation:\n\n" + en)
            if call.data == 'click2_2':
                bot.send_chat_action(call.message.chat.id, action='typing')
                ar = translator.translate(lyricsfr, dest='ar').text
                bot.send_message(chat_id=call.message.chat.id, text="Arabic translation:\n\n" + ar)
            if call.data == 'click2_3':
                bot.send_chat_action(call.message.chat.id, action='typing')
                fr = translator.translate(lyricsfr, dest='fr').text
                bot.send_message(chat_id=call.message.chat.id, text="French translation:\n\n" + fr)
            if call.data == 'click2_4':
                bot.send_chat_action(call.message.chat.id, action='typing')
                es = translator.translate(lyricsfr, dest='es').text
                bot.send_message(chat_id=call.message.chat.id, text="Spanish translation:\n\n" + es)
            if call.data == 'click2_0':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=lyricsfr, reply_markup=keyboard)
    print('Bot is running...')
    bot.infinity_polling()

if __name__ == "__main__":
    tbot()
