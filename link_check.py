import os
import pathlib

from bs4 import BeautifulSoup

''' Debug mode '''
Debug = False

def get_html(url):
    r = requests.get(url)
    if r.status_code == 200:
        page = r.content # r.content contains byte objects, unlike r.text
    else:
        return None

    return page

def print_links(linklist, min_count=1, short=False):
    ''' Pretty prints the link list, if there are greater than/equal to min_count entries '''

    print(f'From {filename}:\n')
    
    printed = [] # List only used if short = True
    for link in linklist:
        if linklist.count(link) >= min_count and link not in printed:
            print(link, f'({linklist.count(link)})')
            if short:
                printed.append(link)

mydir = r"C:/Users/methi/GitHub/supersciencegrl.github.io/"

if Debug:
    filename = r"learning.html" # Test
else:
    filename = input('Page filename: ')

if not filename.endswith('.html'):
    filename = filename + '.html'
filepath = pathlib.Path(os.path.join(mydir, filename))

with open(filepath, 'rb') as page:
    soup = BeautifulSoup(page, 'html.parser')
    
if page:
    links = soup.find_all('a')
else:
    print('Not found. ')

socials = ['https://www.linkedin.com/in/nessacarson/',
           'https://github.com/supersciencegrl/']

internal_links = [link['href'] for link in links if link['href'].startswith('/') or link['href'].startswith('#')]
external_links = [link['href'] for link in links if link['href'] not in internal_links]
duplicate_links = [href for href in external_links if (external_links.count(href) > 1 and href not in socials)]
short_duplicate_links = list(set(duplicate_links)) # Remove duplicates in the list

