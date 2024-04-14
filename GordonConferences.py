from datetime import datetime
import html
import time

from bs4 import BeautifulSoup
import dateparser
import pyperclip
import pywinauto
import requests

def format_url(url):
    """
    Formats a given URL to ensure it is properly structured.

    This function takes a URL as input and ensures it is properly formatted by performing the following actions:
    - Adds 'https://' if the URL lacks a protocol.
    - Appends 'grc.org' if the URL does not contain it.
    - Ensures 'www' is not present in the URL.

    Args:
        url (str): The input URL to be formatted.

    Returns:
        str: The formatted URL.
    """
    if 'http' not in url and 'grc.org' not in url and 'www' not in url:
        if url.startswith("/"):
            return r"https://grc.org" + url
        else:
            return r"https://grc.org/" + url

    elif '://' not in url:
        return f'https://{url}'

    else:
        return url

def get_html(url):
    """
    Fetches the HTML content of a web page given its URL.
    
    Args:
        url (str): The URL of the web page to fetch.

    Returns:
        bytes: The HTML content of the web page as bytes.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request encounters an error (e.g., 404 Not Found).
    """
    
    url = format_url(url)
    
    r = requests.get(url)
    r.raise_for_status()

    return r.content # r.content contains byte objects, unlike r.text

def scrape_page(page, url, print_output=True):
    event = {'url': url}
    soup = BeautifulSoup(page, 'html.parser')

    # Scrape title
    titleDiv = soup.find('div', class_='meetingName')
    meetingName = titleDiv.find('h3').text.strip()
    meetingType = titleDiv.find('span', class_='grcLabel').text.strip()
    meetingTitle = soup.find('h1', class_='meetingTitle') # Not currently used
    subtitle = meetingTitle.text.strip() # Not currently used
    event['title'] = f'{meetingType}: {meetingName}'
    event['title'] = event['title'].replace('nternational', 'ntl').replace(' and ', ' & ').replace(' (GRS)', '')

    # Scrape location
    titleLabels = soup.find_all('span', class_='titleLabel')
    for n, t in enumerate(titleLabels):
        if t.find_all('a', class_='doNotPrint'):
            address = titleLabels[n-1].next.next.next.find_all('div')
    location = address[-1].text
    for state in US_states.items():
        if f'{state[0]}, ' in location:
            location = location.replace(state[0], state[1])
            break
    event['location'] = location.replace('United States', 'USA').replace('United Kingdom', 'UK')

    # Scrape dates
    dateTitle = soup.find('span', class_='dateTitle')
    dateRange = dateTitle.text.strip()
    if '-' in dateRange:
        if dateRange.partition('-')[2].count(' ') == 2: # Starts and ends same month
            endDate = dateRange.partition(' ')[0] + dateRange.partition('-')[2]
        elif dateRange.partition('-')[2].count(' ') == 3: # More than one month
            endDate = dateRange.partition('- ')[2]
        startDate = dateRange.partition(' -')[0] + ('').join(dateRange.partition(',')[1:])
        startDateParsed = dateparser.parse(startDate)
        event['start_date'] = startDateParsed.strftime('%d %b %Y')
        endDateParsed = dateparser.parse(endDate)
        event['end_date'] = endDateParsed.strftime('%d %b %Y')
    
        endDateParsed = dateparser.parse(endDate)
        event['end_date'] = endDateParsed.strftime('%d %b %Y')
    else:
        event['start_date'] = dateparser.parse(dateRange)
        event['end_date'] = '&mdash;'

    # Scrape prices
    prices = soup.find_all('div', class_='price')
    if prices:
        if '$' in prices[0].text:
            event['currency'] = '$'
        else:
            event['currency'] = ''
    else:
        print('Fees are not yet available for this conference. ')
        return None
    
    price_list = []
    for p in prices:
        if 'Conferee' in p.previous:
            try:
                thisPrice = round(float(p.text.replace('$', '').replace(',', '')), 0)
                price_list.append(thisPrice)
            except ValueError:
                pass
    try:
        min_price = int(min(price_list))
        event['min_price'] = f'{min_price:,d}'
        max_price = int(max(price_list))
        event['max_price'] = f'{max_price:,d}'
    except ValueError:
        event['min_price'] = ''
        event['max_price'] = ''

    # html encode dictionary
    for k in event:
        try:
            event[k] = html.escape(event[k])
        except AttributeError: #floats, NoneType
            pass

    # Create output html
    if event['min_price']:
        event['priceString'] = event['currency'] + event['min_price'] + '&ndash;' + event['max_price']
    else:
        event['priceString'] = ''
    
    certificate = '<span class="new-fa"><i class="fa fa-certificate" aria-hidden="true"></i></span> '
    html_out = []
    html_out.append('<tr class="body ">')
    html_out.append('\t' * 13 + \
                    f'<td class="column1"><a class="table-link" href="{event["url"]}" target="_blank" rel="noopener">')
    html_out.append('\t' * 14 + \
                    certificate + \
                    f'{event["title"]}</a></td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column2"><nobr>{event["start_date"]}</nobr></td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column3"><nobr>{event["end_date"]}</nobr></td>')
    html_out.append('\t' * 13 + \
                    
                    f'<td class="column4">{event["location"]}</td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column5">{event["priceString"]}</td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column6">{event["priceString"]}</td>')
    html_out.append('\t' * 12 + '</tr>')

    if print_output:
        # Print output html and copy to Windows clipboard
        for h in html_out:
            print(h)
        pyperclip.copy(('\n').join(html_out))

    return event, html_out

def meetingsFromPage():
    """
    Extracts meeting details from the Gordon Conference 'Find A Conference' page to HTML.

    This function performs the following tasks:
    - Prompts the user to save each page of HTML from the 'Find A Conference' page separately.
    - Loads the saved HTML, extracts links to conferences, and checks if they are already known.
    - Extracts meeting details for conferences not already in the database.

    Returns:
        list: A list of dictionaries, each containing meeting details and HTML representation.
              Each dictionary represents a conference.

    Note:
        - This function relies on user input to save HTML pages manually.
        - It uses the 'requests', 'requests-html', and 'BeautifulSoup' libraries for web scraping.
    """

    main_url = 'https://grc.org/find-a-conference/'
    print(main_url)
    print('\nSave each page of html from the Find A Conference page separately.')
    _ = input('Press Enter when complete...')
    
    with open('GordonConferences.html', 'r', encoding='utf-8') as fin:
        html = fin.read()
    if html:
        soup = BeautifulSoup(html, 'html.parser')
    else:
        return None

    # Check which links are already known
    known_conferences = get_html(r"https://supersciencegrl.co.uk/conferences")
    known_soup = BeautifulSoup(known_conferences, 'html.parser')
    links = []
    if known_soup:
        links = [a['href'] for a in known_soup.find_all('a')]

    meeting_divs = soup.find_all('div', class_='meetingThumb')
    meetings = []
    for meeting in meeting_divs:
        url = meeting.find('a', class_='quickView')['href']
        if url=='{{pageurl}}':
            break

        # Check meeting not already in database
        url = format_url(url)
        if url in links:
            continue
        
        mydict = {}
        print(url)
        mydict['url'] = format_url(url)
        meetings.append(mydict)

        page = get_html(mydict['url'])
        mydict['event'], mydict['html_out'] = scrape_page(page, url, print_output=False)

    return meetings

def check_meetings(meetings: dict):
    """
    Collaborative function to manually review and check through a list of meetings.

    This function iterates through a list of meetings and allows a manual review of each meeting's details.
    It checks whether the meeting has already passed, and if not, prompts for acceptance to view details.

    Args:
        meetings (list): A list of meeting dictionaries, each containing event details and HTML representation.

    Note:
        - This function relies on user input to determine whether to accept and view meeting details.
        - It uses the 'pyperclip' library to copy meeting details to the clipboard for further use.
    """
    
    for meeting in meetings:
        # Move onto next meeting if this one has passed
        end_date = datetime.strptime(meeting['event']['end_date'], '%d %b %Y')
        if end_date < datetime.today():
            continue
        
        print(meeting['event']['title'] + '\n')
        accept = input('Accept? (Y/N) ')
        if accept and accept.lower() in 'yestrue1':
            print('\n')
            result = ('\n').join(meeting['html_out'])
            print(result)
            pyperclip.copy(result)

def run():
    """
    Interactive function to fetch and scrape event details from a web page.

    This function provides an interactive interface to fetch and scrape event details from a web page.
    It prompts the user to input a URL or uses a test URL if in debug mode.
    It fetches the HTML content of the page, scrapes event details, and displays the result.

    Note:
        - In debug mode (when 'Debug' is set to True), a test URL is used automatically.
        - The 'get_html' and 'scrape_page' functions are used to retrieve and process the web page.
    """
    while True:
        if Debug:
            url = r'https://grc.org/additive-manufacturing-of-soft-materials-conference/2022/' # Test
        else:
            url = input('url: ')

        url = format_url(url)

        page = get_html(url)
        if page:
            event = scrape_page(page, url)
        else:
            print('Not found. ')
        print('\n')

def getCurrentTabs():
    """
    Retrieves URLs of currently open tabs in Google Chrome from the 'grc.org' domain.

    This function simulates clicking through all open tabs in Google Chrome to find and collect URLs
    that belong to 'grc.org' but are not related to the 'Find a Conference' page.

    Returns:
        list: A list of 'grc.org' URLs currently open in Chrome.

    Note:
        - This function uses simulated clicks and should not be used while moving the pointer.
        - This function is slow. 
    """
    ### WARNING ###
    ''' This uses simulated clicks: do NOT move the pointer while this function is running! '''

    grc_urls = []
    desktop = pywinauto.Desktop(backend = 'uia')
    chrome_windows = desktop.windows(title_re = '.*Chrome.*', control_type='Pane')
    for cw in chrome_windows:
        cw.set_focus()
        tab_list = cw.descendants(control_type = 'TabItem')
        for tab in tab_list:
            tab.click_input()
            tab_url_wrapper = cw.descendants(title='Address and search bar', control_type='Edit')[0]
            tab_url = tab_url_wrapper.get_value()
            
            if tab_url.startswith('grc.org') and 'find-a-conference' not in tab_url:
                grc_urls.append(tab_url)
                print(tab_url)

    return grc_urls

US_states = {
    'Alaska': 'AK',
    'Alabama': 'AL',
    'Arkansas': 'AR',
    'Arizona': 'AZ',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Iowa': 'IA',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Massachusetts': 'MA',
    'Maryland': 'MD',
    'Maine': 'ME',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Missouri': 'MO',
    'Mississippi': 'MS',
    'Montana': 'MT',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Nebraska': 'NE',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'Nevada': 'NV',
    'New York': 'NY',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Virginia': 'VA',
    'Vermont': 'VT',
    'Washington': 'WA',
    'Wisconsin': 'WI',
    'West Virginia': 'WV',
    'Wyoming': 'WY',
    'District of Columbia': 'DC',
    'American Samoa': 'AS',
    'Guam GU': 'GU',
    'Northern Mariana Islands': 'MP',
    'Puerto Rico': 'PR',
    'US Virgin Islands': 'VI'
    }

''' Debug mode '''
Debug = False

run()
