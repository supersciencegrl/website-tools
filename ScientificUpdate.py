from datetime import datetime
import html
import time

from bs4 import BeautifulSoup
import dateparser
import pyperclip
import pywinauto
import requests

''' Debug mode '''
Debug = False

def run():
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

def get_html(url):
    r = requests.get(url)
    if r.status_code == 200:
        page = r.content # r.content contains byte objects, unlike r.text
    else:
        return None

    return page

def scrape_page(page, url):
    event = {'url': url}
    soup = BeautifulSoup(page, 'html.parser')

    # Scrape title
    titleHeading = soup.find('h1')
    event['title'] = titleHeading.text.strip()
    event['title'] = event['title'].replace('nternational', 'ntl').replace(' and ', ' & ')

    eventType = soup.find('div', class_='breadcrumbs')
    if 'training' in eventType.text.lower():
        title = event['title'].replace(' – Short Course', '').replace(': Short Course', '').replace(' Short Course', '')
        event['title'] = title + ' (training course)'
    else:
        event['title'] = 'Scientific Update: ' + event['title']

    # Scrape location
    locationPara = soup.find('p', class_='location')
    location = locationPara.text.replace('Location: ', '')
    event['location'] = location.replace('United States', 'USA').replace('United Kingdom', 'UK').replace('Online Platform', 'Online')

    # Scrape dates
    dateTitle = soup.find('p', class_='date')
    dateRange = dateTitle.text.replace('Date: ', '').strip()
    if '-' in dateRange:
        endDate = dateRange.partition('- ')[2]
        endDateParsed = dateparser.parse(endDate)
        startDate = dateRange.partition('-')[0] + str(endDateParsed.year)
        startDateParsed = dateparser.parse(startDate)
        event['start_date'] = startDateParsed.strftime('%d %b %Y')
        event['end_date'] = endDateParsed.strftime('%d %b %Y')
    else:
        event['start_date'] = dateparser.parse(dateRange)
        event['end_date'] = '&mdash;'

    # Scrape prices
    prices = soup.find_all('span', class_='price')
    if prices:
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
            
    else:
        print('Fees are not yet available for this conference. ')
        return None

    # html encode dictionary
    for k in event:
        try:
            event[k] = html.escape(event[k])
        except AttributeError: #floats, NoneType
            pass

    # Create output html
    if 'price_all' in event:
        pricehtmlMember = '\t' * 13 + \
                    f'<td class="column5">{event["currency"]}{event["price_all"]}</td>'
        pricehtmlNonMember = pricehtmlMember.replace('column5', 'column6')
    else:
        pricehtmlMember = '\t' * 13 + \
                             f'<td class="column5 standard">{event["currency"]}{event["price_standard"]}</td>' + \
                             f'<td class="column5 student">{event["currency"]}{event["price_student"]}</td>' + \
                             f'<td class="column5 academic">{event["currency"]}{event["price_academic"]}</td>'
        pricehtmlNonMember = pricehtmlMember.replace('column5', 'column6')
    pricehtmlMember = pricehtmlMember.replace('£', '&#163;').replace('$', '&dollar').replace('€', '&euro;')
    pricehtmlNonMember = pricehtmlNonMember.replace('£', '&#163;').replace('$', '&dollar;').replace('€', '&euro;')

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
    html_out.append(pricehtmlMember)
    html_out.append(pricehtmlNonMember)
    html_out.append('\t' * 12 + '</tr>')

    # Print output html and copy to Windows clipboard
    for h in html_out:
        print(h)
    pyperclip.copy(('\n').join(html_out))

def get_currency(price):
    ''' Returns currency and value from a price '''

    for symbol in ['£', '$', '€']:
        if symbol in price:
            currency = symbol
            valueString = price.partition(symbol)[2].replace(',', '').strip()
            value = round(float(valueString))

    return value, currency

def getCurrentTabs():
    ''' This returns all grc.org urls currently open.
        Used to create a list of conferences that don't have fees yet for later scraping.
        Note: this is slow and simulates clicking through all Chrome tabs '''
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

run()
