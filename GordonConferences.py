__version__ = '1.1.0'

from datetime import datetime
import html
from typing import Any

from bs4 import BeautifulSoup
import dateparser
from deprecated import deprecated
import pyperclip
import pywinauto
import requests
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

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

def get_selenide(url: str, driver: WebDriver, cookies: list[dict[str, Any]]) -> tuple[bytes, list[dict[str, Any]]] | None:
    """
    Retrieve the page source of the specified URL as bytes using Selenium.

    Args:
        url (str): The URL of the web page to retrieve.
        driver (WebDriver): The Selenium WebDriver instance used to navigate.
        cookies (list[dict[str, Any]]): List of cookies to be set in the session.

    Returns:
        tuple: A tuple containing:
            bytes: The page source of the URL as bytes.
            list[dict[str, Any]]: The cookies from the web session.
        None: If no URL was specified. 
    """
    if not url:
        return None

    # Connect to the page and retrieve content
    driver.get(url)
    # Load cookies if not already provided
    if not cookies: 
        # Pause execution until the server's happy I'm not doing anything dodgy
        input("Please press Enter once the page is fully loaded in browser to continue...")
        cookies = driver.get_cookies() # Get cookies after the first page load
    
    # Set cookies for session
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url) # Yes you do need to do this again after setting cookies
    page_source = driver.page_source
    page_source_bytes = page_source.encode('utf-8')

    return page_source_bytes, cookies

@deprecated()
def get_html(url):
    """
    This function is now deprecated since the GRC website now disallows automated
    scraping this way. 

    Fetches the HTML content of a web page given its URL.
    
    Args:
        url (str): The URL of the web page to fetch.

    Returns:
        bytes: The HTML content of the web page as bytes.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request encounters an error (e.g., 404 Not Found).
    """
    
    url = format_url(url)
    
    r = requests.get(url, headers = headers, stream = True, verify = False, timeout = 15)
    r.raise_for_status()

    content = []
    for chunk in r.iter_content(chunk_size=1024):  # 1KB chunks
        if chunk:  # Filter out keep-alive new chunks
            content.append(chunk)

    return content # content contains byte objects, unlike r.text

def format_title(meeting_type: str, meeting_name: str) -> str:
    """
    Format a meeting title based on the given meeting type and name.

    This function creates a formatted title by combining the meeting type and meeting name. 
    It performs specific replacements in the title string: 
    - Replaces 'nternational' with 'ntl'
    - Replaces ' and ' with ' & '
    - Removes the substring ' (GRS)'

    Additionally, it adjusts the title formatting by replacing repeated occurrences of ': ' 
    with ' &ndash; '. 

    Args:
        meeting_type (str): The type of the meeting (e.g., 'Gordon Research Seminar').
        meeting_name (str): The name associated with the meeting.

    Returns:
        str: The formatted title string.
    """
    title = f'{meeting_type}: {meeting_name}'
    title = title.replace('nternational', 'ntl').replace(' and ', ' & ').replace(' (GRS)', '')
    
    # Replace only occurrences of ": " after the first occurrence with dashes
    first_idx = title.find(': ')
    if first_idx == -1: # No colon
        return title
    
    second_idx = title.find(': ', first_idx + 1)
    if second_idx == -1:
        return title
    
    return title[:second_idx] + title[second_idx:].replace(': ', ' &ndash; ')

def format_location(location: str) -> str:
    """
    Format the given location string by replacing specific locations and abbreviating terms.

    This function takes a location string and performs the following transformations:
    - Replaces specific city and country names with simplified forms from location_replacements 
      (e.g., 'Castelldefels, Barcelona' may become 'Barcelona' if specified in 
      location_replacements).
    - Replaces 'United States' with 'USA' and abbreviates US states with their corresponding codes 
      based on predefined mappings.

    Args:
        location (str): The original location string to be formatted.

    Returns:
        str: The formatted location string with specified replacements made.
    """
    # Replace locations with city and country only, and abbreviate 'UK'
    for orig, new in location_replacements.items():
        location = location.replace(orig, new)

    # Replace USA and US states with abbreviations
    if 'United States' in location:
        location = location.replace('United States', 'USA')
        for state in US_states.items():
            if f'{state[0]}, ' in location:
                location = location.replace(state[0], state[1])
                break

    return location

def extract_dates(date_range: str) -> tuple[str, str]:
    """
    Extract and format start and end dates from a given date range string.

    This function takes a date range string, which may represent a single date, or a range separated 
    by a hyphen ('-'). It parses the dates and returns them in a standardized format of 'DD MMM YYYY'.

    Args:
        date_range (str): A string representing a date range or a single date.

    Returns:
        tuple[str, str]: A tuple containing the formatted start and end dates. 
                         If only a single date is provided, the end date will be 
                         represented as '&mdash;'.
    """
    if '-' in date_range:
        if date_range.partition('-')[2].count(' ') == 2: # Starts and ends same month
            end_date_text = date_range.partition(' ')[0] + date_range.partition('-')[2]
        elif date_range.partition('-')[2].count(' ') == 3: # More than one month
            end_date_text = date_range.partition('- ')[2]
        
        start_date_text = date_range.partition(' -')[0] + ('').join(date_range.partition(',')[1:])
        start_date_parsed = dateparser.parse(start_date_text)
        start_date = start_date_parsed.strftime('%d %b %Y')

        end_date_parsed = dateparser.parse(end_date_text)
        end_date = end_date_parsed.strftime('%d %b %Y')

    else:
        start_date = dateparser.parse(date_range)
        end_date = '&mdash;'
    
    return start_date, end_date

@deprecated
def scrape_prices(soup) -> str:
    """
    This function is deprecated since I no longer extract price data. 

    Scrape prices from a BeautifulSoup object representing a web page.

    This function searches for all `div` elements with the class 'price' in the provided BeautifulSoup object.
    It extracts the prices associated with 'Conferee' entries, rounding them to the nearest integer and 
    handling currency formatting.

    The function returns a formatted price string that combines:
    - The currency symbol found in the prices (e.g., '$').
    - The minimum price formatted with commas.
    - The maximum price formatted with commas.

    If no prices are available, an empty string is returned. 

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of the webpage. 

    Returns:
        str: A formatted string that represents the price range (e.g., "$1,000&ndash;2,000").
            If no prices are found, an empty string is returned.
    """
    prices = soup.find_all('div', class_='price')
    if prices:
        currency = '$' if '$' in prices[0].text else ''
    
        price_list = []
        for p in prices:
            if 'Conferee' in p.previous:
                try:
                    this_price = round(float(p.text.replace('$', '').replace(',', '')), 0)
                    price_list.append(this_price)
                except ValueError:
                    pass
        try:
            min_price_int = int(min(price_list))
            min_price = f'{min_price_int:,d}'
            max_price_int = int(max(price_list))
            max_price = f'{max_price_int:,d}'
        except ValueError:
            min_price = ''
            max_price = ''
    
    if min_price:
        price_string = currency + min_price + '&ndash;' + max_price
    else:
        price_string = ''
    
    return price_string

def scrape_page(page: bytes, url: str, print_output=True) -> tuple[dict, list]:
    """
    Scrape relevant information from a web page and generate HTML output.

    This function takes an HTML page and a URL, extracts details about a meeting, including its 
    title, location, and dates, and formats the extracted data into a structured HTML table row. 
    If specified, it also prints the generated HTML and copies it to the clipboard.

    Args:
        page (str): A string containing the HTML content of the web page to scrape.
        url (str): The URL of the web page being scraped. 
        print_output (bool): A flag indicating whether to print the output HTML 
                             and copy it to the clipboard. Defaults to True.

    Returns:
        tuple[dict, list]: A tuple containing:
            - A dictionary `event` with the scraped information, including keys 
              for 'url', 'title', 'location', 'start_date', 'end_date', and 'price_string'.
            - A list of strings representing the formatted HTML output for the event.
    """
    event = {'url': url}
    soup = BeautifulSoup(page, 'html.parser')

    # Scrape title
    title_div = soup.find('div', class_='meetingName')
    if title_div is None:
        return None, None
    
    meeting_name = title_div.find('h3').text.strip()
    meeting_type = title_div.find('span', class_='grcLabel').text.strip()
    event['title'] = format_title(meeting_type, meeting_name)
    meeting_title = soup.find('h1', class_='meetingTitle') # Not currently used
    subtitle = meeting_title.text.strip() # Not currently used

    # Scrape location
    title_labels = soup.find_all('span', class_='titleLabel')
    for n, title_label in enumerate(title_labels):
        if title_label.find_all('a', class_='doNotPrint'):
            address = title_labels[n-1].next.next.next.find_all('div')
    location = address[-1].text
    location = format_location(location)
    event['location'] = location

    # Scrape dates
    date_title = soup.find('span', class_='dateTitle')
    event['start_date'], event['end_date'] = extract_dates(date_title.text.strip())

    event['price_string'] = ''

    # html encode dictionary
    for k in event:
        try:
            event[k] = html.escape(event[k])
        except AttributeError: # floats, NoneType
            pass

    tr_classes = 'body ' # Space to nudge user to input their own categories and location
    
    html_out = []
    html_out.append(f'<tr class="{tr_classes}">')
    html_out.append('\t' * 13 + \
                    f'<td class="column1"><a class="table-link" href="{event["url"]}" target="_blank" rel="noopener">')
    html_out.append('\t' * 14 + \
                    f'{event["title"]}</a></td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column2"><nobr>{event["start_date"]}</nobr></td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column3"><nobr>{event["end_date"]}</nobr></td>')
    html_out.append('\t' * 13 + \
                    
                    f'<td class="column4">{event["location"]}</td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column5">{event["price_string"]}</td>')
    html_out.append('\t' * 13 + \
                    f'<td class="column6">{event["price_string"]}</td>')
    html_out.append('\t' * 12 + '</tr>')

    if print_output:
        # Print output html and copy to Windows clipboard
        for h in html_out:
            print(h)
        pyperclip.copy(('\n').join(html_out))

    return event, html_out

def meetings_from_page(driver: WebDriver, cookies: list[dict[str, Any]]):
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
    known_conferences = get_selenide(r"https://supersciencegrl.co.uk/conferences", driver, cookies)
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

        page = get_selenide(mydict['url'], driver, cookies)
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

    This function provides an interactive interface for users to input a URL or use a predefined test 
    URL in debug mode. It creates a Selenium WebDriver instance to navigate to the specified page, 
    fetches the HTML content, and calls the `scrape_page` function to extract event details. 
    The function displays the results or a message if the content could not be found.

    Note:
        - If 'Debug' is set to True, a test URL is used automatically. 
        - The function retrieves cookies from the previous session if available 
          to maintain session state.
        - The `format_url` function is utilized to ensure the URL is correctly structured 
          before fetching the page.

    Returns:
        None: This function runs indefinitely until interrupted by the user (e.g., via Ctrl+C).
    """
    # Create local web driver
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options = options)
    cookies = None

    while True:
        if Debug:
            url = r'https://www.grc.org/biomass-to-biobased-chemicals-and-materials-conference/2025/' # Test
        else:
            url = input('url: ')

        url = format_url(url)

        page, cookies = get_selenide(url, driver, cookies)
        if page:
            event, html_out = scrape_page(page, url)
        else:
            print('Not found. ')
        print('\n')

def get_current_tabs():
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
location_replacements = {
                             'Castelldefels, Barcelona': 'Barcelona',
                             'Les Diablerets, Vaud (fr)': 'Les Diablerets',
                             'Lucca (Barga), Lucca': 'Lucca',
                             'United Kingdom': 'UK'
                             }

''' Debug mode '''
Debug = False

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'identity',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://supersciencegrl.com'
}

run()