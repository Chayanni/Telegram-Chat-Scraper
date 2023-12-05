#!/usr/bin/env python3
#-*- coding:utf -8-*-

# Author: @Chayanni on Telegram

from csv import writer, QUOTE_NONE, reader
from unidecode import unidecode
from bs4 import BeautifulSoup
from datetime import datetime
from requests import Session
from rich import print
from os import path
import urllib3

# Para instalar as dependências, execute: pip3 install requests bs4 rich unidecode
# Para executar o script, execute: python3 main.py

# ----------------- CONFIG ----------------- #

GET_CHANNELS = False # Se True, ele vai extrair os canais, se não, sete como: False
GET_GROUPS = True # Se True, ele vai extrair os grupos, se não, sete como: False
MIN_MEMBERS_OR_SUBSCRIBERS = 2000 # Se o grupo ou canal tiver menos que esse número, ele não vai extrair
PAGE_LIMIT = None # Número limite de páginas por site em que ele vai extrair os links, se não quiser por limite, sete como: None
CSV_FILE_NAME = 'chats.csv' # Nome do arquivo CSV em que os dados serão salvos

HOSTS = [ # Os sites de onde os chats serão extraídos. Repare que cada site tem que ter um mesmo padrão para funcionar, é fácil reparar isso nele através de seu design.
    'https://putariatelegram.com/',
    'https://telegrupos.com.br/categoria/grupos-telegram-adulto/',
    'https://putariatelegram.net/c/adult-content-18/',
    'https://gruposdeputariatelegram.com/',
    'https://linksdegrupo.com/category/grupo-de-putaria-telegram/',
    'https://telegramputaria.com/tags/canais-e-grupos-de-telegram-18/',
    'https://gruposporno.com.br/telegram/category/novinhas-18/',
    'https://linkdegrupoadulto.com/',
    'https://www.linksdegrupos.site/',
    'https://grupoputaria.com/',
    'https://linkdegrupoporno.xyz/',
    'https://grupodeputaria.net/telegram/',
    'https://www.gruposdelinks.com.br/category/adulto/',
    'https://www.grupotelegram.com.br/18/',
    'https://gruposputaria.com/telegram/',
]

# ------------------------------------------- #


HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36 Edg/119.0.0.0',
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if GET_CHANNELS == False and GET_GROUPS == False:
    print('[red]GET_CHANNELS[/red] e [red]GET_GROUPS[/red] não podem ser ambos [red]False[/red]')
    exit()


def get_saved_chats(file_name: str) -> list:
    if path.exists(file_name):
        with open(file_name, 'r', encoding='UTF-8') as file:
            csv_reader = reader(file, delimiter='|', quoting=QUOTE_NONE, escapechar='\\')
            return list(csv_reader)
    return []


def insert_into_csv(file_name: str, data: list) -> None:
    new_data = []
    for value in data:
        if value:
            new_data.append(str(value).replace('\n', '').replace('\r', '').replace('\t', '').replace('|', ''))
        else:
            new_data.append('N/A')
        
    if not path.exists(file_name):
        with open(file_name, 'w', encoding='UTF-8') as file:
            csv_writer = writer(file, delimiter='|', quoting=QUOTE_NONE, lineterminator='\n', escapechar='\\')
            csv_writer.writerow(['Group or Channel Name', 'Chat Type', 'Chat URL', 'Number of Members or Subscribers', 'Description', 'Scrapped From', 'Scrapped Date'])

    with open(file_name, 'a', encoding='UTF-8') as file:
        csv_writer = writer(file, delimiter='|', quoting=QUOTE_NONE, lineterminator='\n', escapechar='\\')
        csv_writer.writerow(new_data)


def get_pages_from_host(session: Session, host: str, page: int = 1) -> list:
    url = f'{host}page/{page}'
    chat_post_urls = []

    response = session.get(url, headers=HEADERS, verify=False, allow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')
    chat_tags = soup.find_all('a', title=True)

    for post in chat_tags:
        url = post['href']
        if not '%' in url and not 'outros' in url and not url in chat_post_urls:
            chat_post_urls.append(url)
    
    if len(chat_post_urls) == 0:
        return []

    return chat_post_urls


def get_tg_chat_url_from_page(session: Session, chat_post_url: str) -> str:
    try:
        response = session.get(chat_post_url, headers=HEADERS, verify=False, allow_redirects=True)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            chat_url = soup.find('a', class_='btn btn-success btn-block')
            return chat_url['href'] if chat_url else None

    except Exception as e:
        print(f'[red]Erro ao obter link do chat[/red]: {e}')


def get_chat_info(session: Session, tg_chat_url: str) -> tuple:
    if tg_chat_url.startswith('https://t.me/'):
        response = session.get(tg_chat_url, headers=HEADERS, verify=False, allow_redirects=True)
        refused_by = 'Ser um chat inválido ou inacessível'

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            join_chat = soup.find('a', class_='tgme_action_button_new')
            join_chat_text = ''
            chat_type = 'N/A'

            if join_chat:
                join_chat_text = join_chat.text.strip()

            if 'channel' in response.text:
                chat_type = 'channel'

            elif join_chat_text == 'View in Telegram' or join_chat_text.lower() == 'join chat' or join_chat_text.lower() == 'join group':
                chat_type = 'group'

            name = soup.find('meta', property='og:title')["content"]
            desc = soup.find('meta', property='og:description')["content"]
            if 'you can' in str(desc).lower():
                desc = 'N/A'

            if chat_type == 'channel' and not GET_CHANNELS:
                refused_by = 'Ser um canal'
            elif chat_type == 'group' and not GET_GROUPS:
                refused_by = 'Ser um grupo'
            else:
                members = 'N/A'
                members = soup.find('div', class_='tgme_page_extra')
                if members:
                    members = members.text.strip()
                    if 'members' in members:
                        members = members.split('members')[0].strip().replace(' ', '')
                        if 'K' in members:
                            members = int(float(members.replace('K', '')) * 1000)

                    elif 'subscriber' in members:
                        members = members.split('subscriber')[0].strip().replace(' ', '')
                        if 'K' in members:
                            members = int(float(members.replace('K', '')) * 1000)

                    if not str(members).isdigit():
                        refused_by = 'Não ser um grupo ou canal válido'
                    elif int(members) < MIN_MEMBERS_OR_SUBSCRIBERS:
                        refused_by = f'Ter um número de membros ou inscritos menor que {MIN_MEMBERS_OR_SUBSCRIBERS}'
                    else:
                        return True, unidecode(str(name)).strip(), unidecode(str(desc).strip()), str(members).strip(), str(chat_type).strip()
    else:
        refused_by = 'Ser um link inválido'

    return False, refused_by, '', '', ''


def is_valid_host(session: Session, host: str) -> bool:
    try:
        response = session.get(host, headers=HEADERS, verify=False, allow_redirects=True)
        if response.status_code == 200:
            if 'telegram' in response.text.lower() and 'minha-conta' in response.text:
                return True

    except: pass
    return False


def telegram_chat_scraper(host: str) -> None:
    tg_chats = []
    chat_urls = []
    scraped_urls = []
    chat_names = []
    page = 1

    saved_chats = get_saved_chats(CSV_FILE_NAME)
    for chat in saved_chats:
        if len(chat) > 2:
            tg_chats.append(chat[2])
    
    if host[-1] != '/':
        host += '/'

    with Session() as session:
        while True:
            if not is_valid_host(session, host):
                print(f'[red]Host inválido[/red]: {host}')
                break
            
            if PAGE_LIMIT and page > PAGE_LIMIT:
                print(f'[red]Limite de páginas atingido[/red]: {PAGE_LIMIT}')
                break

            chat_urls = get_pages_from_host(session, host, page)
            print(f'\nForam achados {len(chat_urls)} links na página: {page} - Site: {host}page/{page}\n')
            page += 1
            checked_chats = 0

            if len(chat_urls) == 0:
                break

            for chat_url in chat_urls:
                if not chat_url in tg_chats:
                    if not chat_url in scraped_urls:
                        scraped_urls.append(chat_url)
                        if not 't.me' in chat_url:
                            tg_url = get_tg_chat_url_from_page(session, chat_url)
                        else:
                            tg_url = chat_url

                        if tg_url and 't.me' in tg_url:
                            if tg_url in tg_chats or chat_url in chat_names:
                                print(f'[red]Chat inválido[/red]: {tg_url} - Recusado por: Possívelmente já estar na lista')
                                continue
                            else:
                                checked_chats += 1

                            tg_chats.append(tg_url)
                            chat_names.append(chat_url)
                            check = get_chat_info(session, tg_url)
                            
                            if check[0]:
                                print(f'[green]Chat válido[/green]: {tg_url} - Nome: {check[1]} - Usuários: {check[3]}')
                                insert_into_csv(CSV_FILE_NAME, [check[1], check[4], tg_url, check[3], check[2], host, datetime.now()])
                                checked_chats += 1

                            else:
                                print(f'[red]Chat inválido[/red]: {tg_url} - Recusado por: {check[1]}')
                
            if checked_chats == 0:
                print(f'[red]Possívelmente é o final das páginas[/red]\n')
                break

if __name__ == '__main__':
    for host in HOSTS:
        telegram_chat_scraper(host)

