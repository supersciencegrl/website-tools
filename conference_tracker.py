__author__ = "Nessa Carson"
__copyright__ = "Copyright 2023"
__version__ = "0.0"
__status__ = "Development"

from datetime import datetime
import json
from pathlib import Path
import string

from bs4 import BeautifulSoup
import requests

def decode_themes(theme_list: list) -> list:
    """
    Decode a list of theme codes into their corresponding theme names.

    Args:
        theme_list (list): A list of theme codes.

    Returns:
        list: A list of theme names.

    """
    
    theme_names = {
        'agro': 'agrochemistry',
        'anal': 'analytical',
        'automation': 'automation',
        'careers': 'careers',
        'catalysis': 'catalysis',
        'chembio': 'chem bio',
        'comp': 'computational/data',
        'diversity': 'diversity',
        'edu': 'education',
        'env': 'environment/fuels',
        'fuels': 'environment/fuels',
        'form': 'formulation/particle science',
        'inorg': 'inorganic/nano',
        'policy': 'law/policy',
        'mat': 'materials/polymers',
        'poly': 'materials/polymers',
        'medchem': 'med chem',
        'pharm': 'pharma industry',
        'phys': 'physical/phys org',
        'process': 'process/engineering',
        'safety': 'safety',
        'synthesis': 'synthesis'
    }

    if 'all' in theme_list:
        output_set = set(theme_names.values())
    else:
        output_set = set([theme_names[theme] for theme in theme_list])
    output_list = sorted(list(output_set))

    return output_list

def decode_region(region: str) -> str:
    """
    Decode a region code into its corresponding region name.

    Args:
        region (str): A region code.

    Returns:
        str: The corresponding region name.

    """
    
    region_short_names = {
        # contintents
        'NA': 'North America',
        'SA': 'South America',
        'Aus': 'Australasia',
        # Eur localities
        'NEur': 'Northern Europe',
        'WEur': 'Western Europe',
        'EEur': 'Eastern Europe',
        # USA localities
        'WUSA': 'Western USA',
        'EUSA': 'Eastern USA',
        'CUSA': 'Midwest USA',
        'SUSA': 'Southern USA',
        # UK localities
        'NEng': 'Northern England',
        'SEng': 'Southern England',
        'NI': 'Northern Ireland'
        }

    if region in region_short_names:
        output = region_short_names[region]
    else:
        output = region

    return output

def scrape_conference_list():
    """
    Scrape a list of conferences from the Conference Database.

    Returns:
        list: A list of conference details extracted from the webpage.

    """
    
    url = 'http://supersciencegrl.co.uk/conferences'
    r = requests.get(url, proxies=proxies)
    r.raise_for_status() # raise HTTPError if status code is not 2xx Success

    soup = BeautifulSoup(r.content, 'html.parser')
    conferences = soup.find_all('tr', class_='body')

    return conferences

def conference_html_to_dict(conference):
    """
    Convert conference HTML data to a dictionary.

    Args:
        conference: The conference HTML data.

    Returns:
        dict: A dictionary containing conference details.
        None: Conference is either postponed or cancelled. 

    """
    
    if 'cancelled' in conference['class'] or 'postponed' in conference['class']:
        return None

    my_dict = {}
    
    # Pull themes from the html classes in the tr tag
    themes = [my_class[1:] for my_class in conference['class'] if my_class.startswith('c')]
    my_dict['themes'] = decode_themes(themes)

    # Pull region(s) from the html classes in the tr tag
    regions = [my_class[1:] for my_class in conference['class'] if my_class.startswith('l')]
    my_dict['regions'] = [decode_region(region) for region in regions]

    column1 = conference.find('td', class_='column1')
    title = column1.text.strip()
    my_dict['title'] = title.rpartition('\t')[2] # Removes tooltips
    
    my_dict['url'] = column1.a.get('href')

    column2 = conference.find('td', class_='column2')
    #my_dict['start_date'] = datetime.strptime(column2.text, '%d %b %Y') # Do not use datetime - not JSON serializable
    my_dict['start_date'] = column2.text

    column3 = conference.find('td', class_='column3')
    end_date = column3.text
    if end_date == '—': # em-dash
        my_dict['end_date'] = None
    else:
        #my_dict['end_date'] = datetime.strptime(end_date, '%d %b %Y') # Do not use datetime - not JSON serializable
        my_dict['end date'] = end_date

    column4 = conference.find('td', class_='column4')
    locations = column4.text.split('/')
    my_dict['locations'] = locations
    my_dict['countries'] = [location.rpartition(', ')[2] for location in locations]
    # Add US state
    if 'USA' in my_dict['countries']:
        my_dict['US_state'] = [location.split(', ')[-2] for location in locations if location.endswith('USA')]

    column5 = conference.find('td', class_='column5') # Selects only standard fees, not student/academic
    if column5.text == 'Free':
        my_dict['member_fee'] = '0'
    else:
        my_dict['member_fee'] = column5.text
    
    column6 = conference.find('td', class_='column6') # Selects only standard fees, not student/academic
    if column6.text == 'Free':
        my_dict['non_member_fee'] = '0'
    else:
        my_dict['non_member_fee'] = column6.text
    # Calculate max fee for sorting
    smaller_fee, sep, max_fee = my_dict['non_member_fee'].rpartition('–')
    if ' / ' in max_fee:
        for currency in ['£', '€', '$']: # In order of preferences
            if currency in max_fee:
                if smaller_fee:
                    smaller_fee = [section for section in smaller_fee.split(' / ') if currency in section][0]
                max_fee = [section for section in max_fee.split(' / ') if currency in section][0]
                break
    if all([char in f'{string.digits},' for char in max_fee]):
        currency = ('').join([char for char in smaller_fee if char not in f'{string.digits},'])
    else:
        currency = ''
    my_dict['max_fee'] = f'{currency}{max_fee}'
    
    return my_dict

def set_proxy():
    """
    Set up a proxy for HTTP and HTTPS requests.

    The function reads the proxy URL from a file named 'proxy.dat' and sets the global 'proxies' variable.

    """
    
    global proxies

    proxy_file = Path('proxy.dat')
    if proxy_file.exists():
        proxy = True
    else:
        proxy = False
    proxies = {}
    if proxy:
        with open(proxy_file, 'rt') as fin:
            proxy_url = fin.readline()
        proxies = {'http': proxy_url,
                   'https': proxy_url
                   }

def get_conferences() -> list[dict]:
    """
    Get a list of conference details.

    Returns:
        list[dict]: A list of dictionaries containing conference details.

    """
    
    conferences = scrape_conference_list()
    all_conferences = [] # list(dict)
    for conference in conferences:
        if conference:
            conference_dict = conference_html_to_dict(conference)
            # Create UID
            remove_spaces_punctuation = str.maketrans('', '', string.punctuation + ' ')
            short_title = conference_dict['title'].translate(remove_spaces_punctuation).lower()
            #short_date = datetime.strftime(conference_dict['start_date'], '%d%m%y')
            short_date = conference_dict['start_date'].replace(' ', '')
            iterator = 0
            uid = f'{short_title[:20]}{short_date}_{iterator}'
            while uid in all_conferences: # Ensure UID is unique
                previous_iterator_length = len(str(iterator))
                iterator += 1
                uid = uid[:-previous_iterator_length] + str(iterator)
            conference_dict['uid'] = uid
            all_conferences.append(conference_dict)

    return all_conferences

def export_to_json(lod: list[dict], output_file='conferences.json'):
    """
    Export a list of dictionaries to a JSON file.

    Args:
        lod (list[dict]): The list of dictionaries to be exported.
        output_file (str, optional): The name of the output JSON file. Defaults to 'conferences.json'.

    """
    
    json_export = json.dumps(lod)
    with open(output_file, 'w', encoding='utf8') as fout:
        json.dump(all_conferences, fout, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    set_proxy()
    all_conferences = get_conferences()
    export_to_json(all_conferences)