from datetime import datetime
import html
import time

from bs4 import BeautifulSoup
import dateparser
import pyperclip
import pywinauto
import requests

def get_html(url):
    """
    Fetches the HTML content from a given URL and returns it as bytes.

    Args:
        url (str): The URL of the web page to fetch.

    Returns:
        bytes: The HTML content as bytes.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the HTTP request.
    """
    r = requests.get(url)
    r.raise_for_status()
    
    return r.content

def clean_location(location_paragraph):
    """
    Cleans and standardizes a location string extracted from a webpage.

    This function takes a location paragraph extracted from a webpage and performs the following tasks:
    - Removes the 'Location: ' prefix.
    - Standardizes location names based on a predefined set of replacements.

    Args:
        location_paragraph (bs4.element.Tag): The BeautifulSoup Tag containing the location information.

    Returns:
        str: The cleaned and standardized location string.
    """
    location = location_paragraph.text.replace('Location: ', '')
    
    location_replacements = {'The Netherlands': 'Netherlands',
                             'United States': 'USA',
                             'United Kingdom': 'UK',
                             'Boston': 'Boston, MA',
                             'Denver': 'Denver, CO',
                             'Edinburgh': 'Edinburgh, Scotland',
                             'San Diego': 'San Diego, CA',
                             'Online Platform': 'Online'
                             }
    for k, v in location_replacements.items():
        location = location.replace(k, v)

    return location

def get_currency(price):
    """
    Extracts the currency symbol and value from a price string.

    This function takes a price string and performs the following tasks:
    - Converts the price string to lowercase and removes ' per person' if present.
    - Searches for certain currency symbols (£, $, €) in the price string and extracts the currency symbol and value.

    Args:
        price (str): The price string to extract currency and value from.

    Returns:
        tuple: A tuple containing the extracted value (as an integer) and the currency symbol.

    Example:
        If price is '£500', the function returns (500, '£').
    """
    price = price.lower().replace(' per person', '')
    for symbol in ['£', '$', '€']:
        if symbol in price:
            currency = symbol
            value_string = price.partition(symbol)[2].replace(',', '').strip()
            value = round(float(value_string))

    return value, currency

def get_prices(prices):
    """
    Extracts and organizes prices and their types from a list of price elements.

    This function takes a list of BeautifulSoup elements representing prices and performs the following tasks:
    - Extracts and categorizes prices into different types (e.g., 'student', 'academic', 'conference', or 'all' if prices are uniform).
    - Assigns the extracted prices to corresponding event attributes along with the currency.

    Args:
        prices (list of bs4.element.Tag): A list of BeautifulSoup Tag elements containing price information.

    Returns:
        dict: A dictionary containing the extracted prices and their types, along with the currency symbol.

    Example:
        If prices is a list of BeautifulSoup elements representing student, academic, and conference prices,
        the function returns a dictionary like {'price_student': 500, 'price_academic': 750, 'price_standard': 1000, 'currency': '£'}.
    """
    if len(prices) == 1:
            price = prices[0].text.partition(' + VAT')[0]
            event['price_all'], event['currency'] = get_currency(price)
        elif len(prices) > 1:
            price_types = [price.parent.text.partition(' ')[0].lower() for price in prices]
            if 'student' in price_types:
                idx = price_types.index('student')
                studentPrice = prices[idx].text.partition(' + VAT')[0]
                event['price_student'], event['currency'] = get_currency(studentPrice)
            if 'academic' in price_types:
                idx = price_types.index('academic')
                academicPrice = prices[idx].text.partition(' + VAT')[0]
                event['price_academic'], event['currency'] = get_currency(academicPrice)
                if 'price_student' not in event:
                    event['price_student'] = event['price_academic']
            if 'conference' in price_types:
                idx = price_types.index('conference')
                standardPrice = prices[idx].text.partition(' + VAT')[0]
                event['price_standard'], event['currency'] = get_currency(standardPrice)
                if 'price_academic' not in event and 'price_student' not in event:
                    event['price_all'] = event['price_standard']
            else:
                print(f'Price types for this event: {price_types}. Please revisit.')
                return event

def scrape_page(page, url):
    """
    Scrapes information from a web page and organizes it into an event dictionary.

    This function takes a web page content and its URL and performs the following tasks:
    - Extracts and cleans the event title, including adjustments for training courses.
    - Scrapes and standardizes the event location.
    - Extracts and formats event dates, including handling date ranges.
    - Retrieves and categorizes event prices.
    - Encodes dictionary values to HTML entities.
    - Creates an output HTML representation of the event.

    Args:
        page (bytes): The HTML content of the web page to scrape.
        url (str): The URL of the web page.

    Returns:
        dict or None: A dictionary containing the scraped event information, or None if there are no available fees.
    """
    event = {'url': url}
    soup = BeautifulSoup(page, 'html.parser')

    # Scrape title
    title_heading = soup.find('h1')
    event['title'] = title_heading.text.strip()
    event['title'] = event['title'].replace('nternational', 'ntl').replace(' and ', ' & ')

    eventType = soup.find('div', class_='breadcrumbs')
    if 'training' in eventType.text.lower():
        title = event['title'].replace(' – Short Course', '').replace(': Short Course', '').replace(' Short Course', '')
        event['title'] = title + ' (training course)'
    else:
        event['title'] = 'Scientific Update: ' + event['title']

    # Scrape location
    location_paragraph = soup.find('p', class_='location')
    event['location'] = clean_location(location_paragraph)

    # Scrape dates
    date_title = soup.find('p', class_='date')
    date_range = date_title.text.replace('Date: ', '').strip()
    if '-' in date_range:
        end_date = date_range.partition('- ')[2]
        end_date_parsed = dateparser.parse(end_date)
        start_date = date_range.partition('-')[0] + str(end_date_parsed.year)
        start_date_parsed = dateparser.parse(start_date)
        event['start_date'] = start_date_parsed.strftime('%d %b %Y')
        event['end_date'] = end_date_parsed.strftime('%d %b %Y')
    else:
        event['start_date'] = dateparser.parse(date_range)
        event['end_date'] = '&mdash;'

    # Scrape prices
    prices = soup.find_all('span', class_='price')
    if prices:
        get_prices(prices) 
    else:
        print('Fees are not yet available for this conference. ')
        return None

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
                    f'<td class="column5">{event["currency"]}{event["price_all"]:,}</td>'
        price_html_nonmember = price_html_member.replace('column5', 'column6')
    else:
        price_html_member = '\t' * 13 + \
                             f'<td class="column5 standard">{event["currency"]}{event["price_standard"]:,}</td>' + \
                             f'<td class="column5 student">{event["currency"]}{event["price_student"]:,}</td>' + \
                             f'<td class="column5 academic">{event["currency"]}{event["price_academic"]:,}</td>'
        price_html_nonmember = price_html_member.replace('column5', 'column6')
    
    price_html_member = price_html_member.replace('€', '&euro;')
    price_html_nonmember = price_html_nonmember.replace('€', '&euro;')

    event['title'] = event['title'].replace(' - ', ' &ndash; ')
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
    html_out.append(price_html_member)
    html_out.append(price_html_nonmember)
    html_out.append('\t' * 12 + '</tr>')

    # Print output html and copy to Windows clipboard
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

        page = get_html(url)
        if page:
            scrape_page(page, url)
        else:
            print('Not found. ')
        print('\n')
        if Debug:
            break

''' Debug mode '''
Debug = False

run()
