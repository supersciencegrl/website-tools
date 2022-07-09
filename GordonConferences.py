from datetime import datetime
import html

from bs4 import BeautifulSoup
import dateparser
import pyperclip
import requests

''' Debug mode '''
Debug = False

def run():
    while True:
        if Debug:
            url = r'https://www.grc.org/additive-manufacturing-of-soft-materials-conference/2022/' # Test
        else:
            url = input('url: ')

        get_html(url)

def get_html(url):
    r = requests.get(url)
    if r.status_code == 200:
        page = r.content # r.content contains byte objects, unlike r.text
    else:
        page = None

    event = {'url': url}
    if page:
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
        location = address[-1]
        event['location'] = location.text.replace('United States', 'USA').replace('United Kingdom', 'UK')

        # Scrape dates
        dateTitle = soup.find('span', class_='dateTitle')
        dateRange = dateTitle.text.strip()
        if '-' in dateRange:
            if dateRange.partition('-')[2].count(' ') == 2:
                endDate = dateRange.partition(' ')[0] + dateRange.partition('-')[2]
            elif dateRange.partition('-')[2].count(' ') == 3:
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
        if '$' in prices[0].text:
            event['currency'] = '$'
        else:
            event['currency'] = ''
        
        priceList = []
        for p in prices:
            if 'Conferee' in p.previous:
                try:
                    thisPrice = round(float(p.text.replace('$', '').replace(',', '')), 0)
                    priceList.append(thisPrice)
                except ValueError:
                    pass
        try:
            event['min_price'] = str(int(min(priceList)))
            event['max_price'] = str(int(max(priceList)))
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

        # Print output html and copy to Windows clipboard
        for h in html_out:
            print(h)
        pyperclip.copy(('\n').join(html_out))

    else:
        print('Not found. ')
    print('\n')

run()
