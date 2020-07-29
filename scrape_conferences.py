__author__ = "Nessa Carson"
__copyright__ = "Copyright 2020"
__version__ = "1.0"
__email__ = "nessa.carson@syngenta.com"
__status__ = "Production"

import glob
import html
import os
import urllib.request
import urllib.error
import string

import openpyxl
from openpyxl.styles import Alignment, Font

def getevent(position):
    for n, line in enumerate(page[position:]):
        if line.strip().startswith('</tr>'):
            endposition = position + n + 1
            break
    event = [p.strip() for p in page[position:endposition]]

    return event

def captureline(line):
    result = line.partition('">')[2].partition('</td>')[0]

    return result

def decodethemes(themelist):
    replacelist = [('agro', 'agrochemistry'), ('anal', 'analytical'), ('chembio', 'chem bio'), ('comp', 'computational/data'), ('edu', 'education'), ('inorg', 'inorganic/materials'), ('medchem', 'med chem'), ('policy', 'law/policy'), ('pharm', 'pharma/regulatory')]
    names = [r[0] for r in replacelist]
    newthemelist = []

    for theme in themelist:
        if theme in names:
            newthemelist.append(replacelist[names.index(theme)][1])
            if theme == 'chembio':
                newthemelist.append('med chem')
            if theme in ['medchem', 'process']:
                newthemelist.append('synthesis')
        else:
            newthemelist.append(theme)

    outputlist = [i for n, i in enumerate(newthemelist) if i not in newthemelist[:n]]
    outputlist.sort()

    themes = (', ').join(outputlist)
    return themes

def decoderegion(region):
    continents = [('NA', 'North America'), ('SA', 'South America'), ('Aus', 'Australasia')]
    Eurlocalities = [('WEur', 'Western Europe'), ('EEur', 'Eastern Europe')]
    USAlocalities = [('WUSA', 'Western USA'), ('EUSA', 'Eastern USA'), ('CUSA', 'Central USA')]
    UKlocalities = [('NEng', 'Northern England'), ('SEng', 'Southern England'), ('NI', 'Northern Ireland')]
    regionlist = continents + Eurlocalities + USAlocalities + UKlocalities

    if region in [r[0] for r in regionlist]:
        output = regionlist[[r[0] for r in regionlist].index(region)][1]
    else:
        output = region

    return output

def openoutput():
    os.system(f'start excel "{outputfile}"')

url = 'http://supersciencegrl.co.uk/conferences'

try:
    with urllib.request.urlopen(url) as response:
        htmlr = response.readlines()
except urllib.error.HTTPError as error:
    print(error.code, error.read)

page = []
errors = []
for h in htmlr:
    try:
        page.append(h.decode('utf-8'))
    except UnicodeDecodeError:
        errors.append(h)

lod = []
for n, p in enumerate(page):
    if p.strip().startswith('<tr class="body') and not 'postponed' in p and not 'cancelled' in p:
        event = getevent(n)
        mydict = {}
        ColumnOneEnd = False

        for n, line in [(n, line.strip()) for n, line in enumerate(event)]:
            if n == 0:
                themelist = []
                for kw in line.split(' '):
                    if kw.startswith('c') and not kw.startswith('class'):
                        themelist.append(kw[1:])
                    elif kw.startswith('l'):
                        region = kw.translate(str.maketrans('', '', string.punctuation)).strip()[1:]
                        region = decoderegion(region)
                        mydict['region'] = region
                mydict['themes'] = decodethemes(themelist)
            elif n == 1:
                mydict['url'] = line.partition('href="')[2].partition('"')[0]
                if line.endswith('</td>'):
                    title = line.partition('rel = "noopener">')[2].partition('</td>')[0]
                    title = title.replace('<span class="new-fa"><i class="fa fa-certificate" aria-hidden="true"></i></span> ', '')
                    mydict['title'] = title
                    ColumnOneEnd = True
            elif line.startswith('<span class="tooltipconf">') or line.startswith('<!--<span class="tooltipconf'):
                pass
            elif not ColumnOneEnd and line.endswith('</td>'):
                title = line.partition('</td>')[0]
                title = title.replace('<span class="new-fa"><i class="fa fa-certificate" aria-hidden="true"></i></span> ', '').replace('</a>', '')
                mydict['title'] = title
                ColumnOneEnd = True
            elif line.startswith('<td class="column2'):
                mydict['startdate'] = captureline(line)
            elif line.startswith('<td class="column3'):
                mydict['enddate'] = captureline(line)
            elif line.startswith('<td class="column4'):
                mydict['location'] = captureline(line)
            elif line.startswith('<td class="column5'):
                price = line.partition('>')[2].partition('</td>')[0]
                price = price.replace('/', '').replace('<em>', '')
                mydict['memberprice'] = html.unescape(price)
            elif line.startswith('<td class="column6'):
                price = line.partition('>')[2].partition('</td>')[0]
                price = price.replace('/', '').replace('<em>', '')
                mydict['nonmemberprice'] = html.unescape(price)
        lod.append(mydict)

outlist = []
for event in lod:
    eventlist = []
    eventlist.append(event['title'])
    if event['enddate'] != '&mdash;':
        eventlist.append(f'{event["startdate"]}–{event["enddate"]}')
    else:
        eventlist.append(event['startdate'])
    eventlist.append(event['location'])
    eventlist += ['', '', '', ''] # Empty cells for Syngenta list
    if event['memberprice'] == event['nonmemberprice']:
        eventlist.append(event['memberprice'])
    else:
        eventlist.append(f'Members: {event["memberprice"]};\nNon-members: {event["nonmemberprice"]}')
    eventlist.append(event['url'])

    # Extra fields
    eventlist.append(event['themes'])
    eventlist.append(event['region'])
    outlist.append(eventlist)

# Find possible inputfile to append sheet
inputfile = None
xlsxlist = glob.glob('**.xls*')
shortlist = glob.glob('**onference**.xls*')
if not shortlist:
    potentiallist = xlsxlist
else:
    potentiallist = shortlist
if len(potentiallist) == 1:
    possinput = input(f'Do you want to add conferences to {potentiallist[0]}? \n(Existing scraped worksheets will be overwritten.) ')
    if possinput.lower() in 'yestrue1':
        inputfile = potentiallist[0]

if inputfile:
    if inputfile.endswith('.xlsm'):
        wb = openpyxl.load_workbook(filename = inputfile, data_only = False, keep_vba = True)
    else:
        wb = openpyxl.load_workbook(filename = inputfile, data_only = False)
    if 'Scraped from web' in wb.sheetnames:
        wb.remove(wb['Scraped from web'])
    ws = wb.create_sheet('Scraped from web')
    outputfile = inputfile
else:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Scraped from web'
    outputfile = 'Conference_List.xlsx'
ws.sheet_properties.tabColor = '00B050'

headers = ['Conference', 'Date', 'Location', 'Nominations', 'Confirmed Attendees (JH)', 'Confirmed Attendees (ST)', 'Comments', 'Registration fee', 'Weblink', 'Themes', 'Region']
for n, h in enumerate(headers):
    ws.cell(row = 1, column = n + 1).value = h
    ws.cell(row = 1, column = n + 1).font = Font(name = 'Arial', size = 10, bold = True)
    ws.cell(row = 1, column = n + 1).alignment = Alignment(wrapText = True)

for y, row in enumerate(outlist):
    for x, cell in enumerate(row):
        if x == 8:
            value = cell
            ws.cell(row = y + 2, column = x + 1).hyperlink = value
            ws.cell(row = y + 2, column = x + 1).font = Font(name = 'Arial', size = 10, color = '0000FF', underline = 'single')
        else:
            value = html.unescape(cell)
            ws.cell(row = y + 2, column = x + 1).font = Font(name = 'Arial', size = 10)
        ws.cell(row = y + 2, column = x + 1).value = value
        if x == 7:
            ws.cell(row = y + 2, column = x + 1).alignment = Alignment(wrapText = True) # Allow newlines in price

# Aesthetics
colwidths = [('A', 66), ('B', 14), ('C', 20), ('D', 17), ('E', 18), ('F', 18), ('G', 18), ('H', 22), ('I', 30), ('J', 57), ('K', 18)]
for col in colwidths:
    ws.column_dimensions[col[0]].width = col[1]
ws.freeze_panes = 'A2'

wb.active.views.sheetView[0].tabSelected = False
wb.active = ws

wb.save(outputfile)
# Then ask in GUI if user wishes to open it
