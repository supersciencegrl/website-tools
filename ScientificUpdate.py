__version__ = '1.4.0'

import html

from bs4 import BeautifulSoup
import bs4.element
import dateparser
from deprecated import deprecated
from pathlib import Path
import pyperclip
import requests
from selenium import webdriver

def get_selenide(url: str) -> bytes | None:
    """
    Retrieve the page source of the specified URL as bytes using Selenium.

    Args:
    url (str): The URL of the web page to retrieve.

    Returns:
    None: No URL was specified. 
    bytes: The page source of the URL as bytes.
    """
    if not url:
        return None

    # Create local web driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new') # headless browser
    driver = webdriver.Chrome(options = options)

    # Get page source then quit the browser
    driver.get(url)
    page_source = driver.page_source
    page_source_bytes = page_source.encode('utf-8')
    driver.quit()

    return page_source_bytes

@deprecated()
def get_html(url: str) -> bytes:
    """
    This function is now deprecated since the Scientific Update website now disallows automated
    scraping this way. 
    
    Fetches the HTML content from a given URL and returns it as bytes.

    Args:
        url (str): The URL of the web page to fetch.

    Returns:
        bytes: The HTML content as bytes.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the HTTP request.
    """
    r = requests.get(url, headers = headers)
    r.raise_for_status()
    
    return r.content

def scrape_title(soup: BeautifulSoup) -> str:
    """
    Scrapes and processes the title from a BeautifulSoup object representing a webpage.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed webpage.

    Returns:
        str: The processed title string.
    """
    title_heading = soup.find('h1')
    title = title_heading.text.strip()
    title = title.replace('nternational', 'ntl').replace(' and ', ' & ')

    event_type = soup.find('div', class_='breadcrumbs')
    if 'training' in event_type.text.lower():
        title = title.replace(' – Short Course', '').replace(': Short Course', '').replace(' Short Course', '')
        title = title + ' (training course)'
    else:
        title = 'Scientific Update: ' + title

    return title

def scrape_location(soup: BeautifulSoup) -> str:
    """
    Cleans and standardizes a location string extracted from a webpage.

    This function finds a location paragraph extracted from a webpage then performs the following tasks:
    - Removes any prefix before a "|" (referring to a precise venue).
    - Standardizes location names based on a predefined set of replacements to ensure standardized 
        country (and state, if applicable).

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed webpage.

    Returns:
        str: The cleaned and standardized location string.
    """
    location_div = soup.find('div', class_='sidebar-details').find('div', class_='location')
    location_paragraph = location_div.find('span')

    if '| ' in location_paragraph.text:
        location = location_paragraph.text.partition('| ')[2] # Take only text after '| '
    else:
        location = location_paragraph.text
    
    location_replacements = {'The Netherlands': 'Netherlands',
                             'United Kingdom': 'UK',
                             'United States': 'USA',
                             'Online Event': 'Online',

                             'Edinburgh': 'Edinburgh, Scotland',
                             'Steamboat, Colorado': 'Steamboat Springs, CO',
                             'San Diego, USA': 'San Diego, CA, USA', # Must come after USA
                             'Denver, USA': 'Denver, CO, USA', # Must come after USA
                             'Atlanta, USA': 'Atlanta, GA, USA', # Must come after USA
                             'Boston, USA': 'Boston, MA, USA', # Must come after USA
                             'Charleston, USA': 'Charleston, SC, USA' # Must come after USA
                             }
    for k, v in location_replacements.items():
        location = location.replace(k, v)

    return location

def scrape_dates(soup) -> dict[str, str]:
    """
    Cleans and standardizes date strings extracted from a webpage, and returns them as a dictionary of
        standardized date strings.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed webpage.

    Returns:
        dict[str, str]: A dictionary with keys 'start_date' and 'end_date' containing the standardized date strings.
    """
    date_title = soup.find('div', class_='dates')
    date_spans = date_title.find_all('span')

    start_date, end_date = (date.text for date in date_spans)

    start_date_parsed = dateparser.parse(start_date)
    start_date_std = start_date_parsed.strftime('%d %b %Y')

    end_date.replace('- ', '')
    end_date_parsed = dateparser.parse(end_date)
    end_date_std = end_date_parsed.strftime('%d %b %Y')

    dates = {'start_date': start_date_std,
             'end_date': end_date_std
             }

    return dates

@deprecated
def get_currency(price: str) -> tuple[str, str]:
    """
    This function is no longer used, since it is a child of get_prices(), which is deprecated. 

    Extracts and processes currency information from a given price string, returning the value as a
        formatted string and the currency symbol.

    Args:
        price (str): The price string containing currency information.

    Returns:
        tuple[str, str]: A tuple containing the formatted value string and the currency symbol.
    """
    vat = '+ VAT' in price # bool
    asterisk_present = '*' in price # bool
    
    price = price.lower().replace('usd ', '').replace('*', '').replace('full course: ', '')
    price = price.partition(' ')[0].strip() # Only take everything before the first space
    INTEGER_FORMAT = '{:,.0f}'
    for symbol in ['£', '$', '€']:
        if symbol in price:
            currency = symbol
            value_float = float(price.partition(symbol)[2].replace(',', '').strip())
            if vat:
                value_plus_vat_string = INTEGER_FORMAT.format(value_float * (1 + VAT_RATE))
                if asterisk_present:
                    value_without_tax_string = INTEGER_FORMAT.format(value_float)
                    value_string = f'{value_without_tax_string}–{value_plus_vat_string}'
                else:
                    value_string = value_plus_vat_string
            else:
                value_string = INTEGER_FORMAT.format(value_float)
            break

    return value_string, currency

@deprecated
def get_prices(prices: list[bs4.element.Tag]) -> dict[str, str]:
    """
    This function is now deprecated since I no longer publish conference fees. 

    Extracts and organizes prices and their types from a list of price elements.

    This function takes a list of BeautifulSoup elements representing prices and performs the following tasks:
    - Extracts and categorizes prices into different types (e.g., 'student', 'academic', 'conference', or 'all' if prices are uniform).
    - Assigns the extracted prices to corresponding event attributes along with the currency.

    Args:
        prices (list of bs4.element.Tag): A list of BeautifulSoup Tag elements containing price information.

    Returns:
        dict[str, str]: A dictionary containing the extracted prices and their types, along with the currency symbol.

    Example:
        If prices is a list of BeautifulSoup elements representing student, academic, and conference prices,
        the function returns a dictionary like:
        {'price_student': 500, 'price_academic': 750, 'price_standard': 1000, 'currency': '£'}
    """
    my_zip = zip(prices[0].find_all(class_='title'), prices[0].find_all(class_='content'))
    price_dict = {title.text.strip(): content.text.strip() for title, content in my_zip}
    result = {}
    
    if len(price_dict) == 1:
        first_price = next(iter(price_dict.values()))
        result['price_all'], result['currency'] = get_currency(first_price)

    elif len(price_dict) > 1:
        event_fee_section = price_dict.get('Conference Fee') or price_dict.get('Course Fee')
        standard_fee, result['currency'] = get_currency(event_fee_section)
        
        student_fee, academic_fee = None, None #default
        if 'Student Fee' in price_dict.keys():
            student_fee, _ = get_currency(price_dict['Student Fee'])
        if 'Academic Fee' in price_dict.keys():
            academic_fee, _ = get_currency(price_dict['Academic Fee'])

        # Set fees
        result['price_standard'] = standard_fee
        result['price_academic'] = academic_fee or standard_fee # Std if not specified
        result['price_student' ] = student_fee or academic_fee or standard_fee # Academic or std if not specified
                        
    return result

def scrape_page(page: bytes, url: str):
    """
    Now deprecated
    Scrapes information from a web page and organizes it into an event dictionary.

    This function takes a web page content and its URL and performs the following tasks:
    - Extracts and standardizes the event title and location.
    - Extracts and formats event dates, including handling date ranges.
    - Retrieves and categorizes event prices.
    - Encodes dictionary values to HTML entities.
    - Creates an output HTML representation of the event.

    Args:
        page (bytes): The HTML content of the web page to scrape.
        url (str): The URL of the web page.

    Side-effects:
        Creates an output HTML representation of the event.
    """
    event = {'url': url}
    soup = BeautifulSoup(page, 'html.parser')

    event['title'] = scrape_title(soup)
    event['location'] = scrape_location(soup)    

    # Scrape dates
    dates = scrape_dates(soup)
    event.update(dates)

    # I no longer publish prices online - these will all be blank
    # prices = soup.find_all('div', class_='fees')
    # if prices:
    #     price_result = get_prices(prices)
    #     event.update(price_result)
    event['currency'] = ''
    event['price_all'] = ''

    # html encode dictionary
    for k in event:
        try:
            event[k] = html.escape(event[k])
        except AttributeError: # floats, NoneType
            pass

    create_output_html(event)
    
def create_output_html(event):
    """
    Creates an HTML representation of event data and copies it to the clipboard.

    This function takes an event dictionary and performs the following tasks:
    - Constructs an HTML representation of the event, including title, dates, location, and prices.
    - Handles different price scenarios based on the event data.
    - Encodes the HTML output for proper display.

    Args:
        event (dict): A dictionary containing event information.

    Example:
        An example event dictionary might look like:
        {
            'url': 'https://supersciencegrl.co.uk',
            'title': 'Automated Intelligent Chemistry',
            'start_date': '10 Sep 2023',
            'end_date': '12 Sep 2023',
            'location': 'Warrington, UK',
            'currency': '£',
            'price_standard': 1200,
            'price_student': 800,
            'price_academic': 900
        }
    """
    if 'price_all' in event:
        # Print prices with thousands separation using f'{number:,}'
        price_html_member = '\t' * 13 + \
                    f'<td class="column5">{event["currency"]}{event["price_all"]}</td>'
        price_html_nonmember = price_html_member.replace('column5', 'column6')
    else:
        price_html_member = '\t' * 13 + \
                             f'<td class="column5 standard">{event["currency"]}{event["price_standard"]}</td>' + \
                             f'<td class="column5 student">{event["currency"]}{event["price_student"]}</td>' + \
                             f'<td class="column5 academic">{event["currency"]}{event["price_academic"]}</td>'
        price_html_nonmember = price_html_member.replace('column5', 'column6')
    
    price_html_member = price_html_member.replace('€', '&euro;')
    price_html_nonmember = price_html_nonmember.replace('€', '&euro;')

    event['title'] = event['title'].replace(' - ', ' &ndash; ')
    event['title'] = event['title'].replace('  ', ' ') # Remove double spaces
    
    html_out = []
    html_out.append('<tr class="body ">')
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
    html_out.append(price_html_member)
    html_out.append(price_html_nonmember)
    html_out.append('\t' * 12 + '</tr>')

    # Print output html and copy to Windows clipboard
    print(f'{event["title"]}, {event["location"]}, {event["start_date"]}') # Mark to user what has been printed
    for h in html_out:
        print(h)
    pyperclip.copy(('\n').join(html_out))

def run():
    """
    Interactive function to fetch and scrape event details from a web page.

    This function provides an interactive interface to fetch and scrape event details from a web page.
    It prompts the user to input a URL, or uses a test URL if in debug mode.
    It fetches the HTML content of the page, scrapes event details, and displays the result.

    Note:
        - In debug mode (when 'Debug' is set to True), a test URL is used automatically.
    """
    while True:
        if Debug:
            url = r'https://www.scientificupdate.com/training_courses/work-up-and-product-isolation/' # Test
        else:
            url = input('url: ')

        page = get_selenide(url)
        if page:
            scrape_page(page, url)
        else:
            print('Not found. ')
        print('\n')
        if Debug:
            break

''' Debug mode '''
Debug = False

VAT_RATE = 0.20
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://supersciencegrl.com'
}

run()