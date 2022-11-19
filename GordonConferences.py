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
            url = r'https://grc.org/additive-manufacturing-of-soft-materials-conference/2022/' # Test
        else:
            url = input('url: ')

        url = formatUrl(url)

        page = get_html(url)
        if page:
            event = scrape_page(page, url)
        else:
            print('Not found. ')
        print('\n')

def get_html(url):
    url = formatUrl(url)
    
    r = requests.get(url)
    if r.status_code == 200:
        page = r.content # r.content contains byte objects, unlike r.text
    else:
        return None

    return page

def formatUrl(url):
    if 'http' not in url and 'grc.org' not in url and 'www' not in url:
        if url.startswith("/"):
            return r"https://grc.org" + url
        else:
            return r"https://grc.org/" + url

    elif '://' not in url:
        return f'https://{url}'

    else:
        return url

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
    location = address[-1]
    event['location'] = location.text.replace('United States', 'USA').replace('United Kingdom', 'UK')

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

    if print_output:
        # Print output html and copy to Windows clipboard
        for h in html_out:
            print(h)
        pyperclip.copy(('\n').join(html_out))

    return event, html_out

def meetingsFromPage():
    ''' Save the html as GordonConferences.html '''

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
    knownConferences = get_html(r"https://supersciencegrl.co.uk/conferences")
    knownSoup = BeautifulSoup(knownConferences, 'html.parser')
    links = []
    if knownSoup:
        links = [a['href'] for a in knownSoup.find_all('a')]

    meetingDivs = soup.find_all('div', class_='meetingThumb')
    meetings = []
    for meeting in meetingDivs:
        url = meeting.find('a', class_='quickView')['href']
        if url=='{{pageurl}}':
            break

        # Check meeting not already in database
        url = formatUrl(url)
        if url in links:
            continue
        
        mydict = {}
        print(url)
        mydict['url'] = formatUrl(url)
        meetings.append(mydict)

        page = get_html(mydict['url'])
        mydict['event'], mydict['html_out'] = scrape_page(page, url, print_output=False)

    return meetings

def checkMeetings(meetings: dict):
    ''' Collaborative function to check semi-manually through the meetings from meetingsFromPage() '''
    
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
