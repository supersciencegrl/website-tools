__author__ = "Nessa Carson"
__copyright__ = "Copyright 2020"
__version__ = "1.0"
__email__ = "methionine57@gmail.com"
__status__ = "Production"

import datetime
from dateutil import tz
import os
import time

print(f'events-from-html.py v.{__version__}')
# Last edited 2020-Apr-11 15:35

mydir = 'C:\\Users\\Nessa\\Documents\\Work\\Website\\Current'
testdir = 'C:\\Users\\Nessa\\Documents\\Work\\Coding\\Website'
os.chdir(mydir)

def check_html_is_list(html):
    if type(html) is str:
        htmllist = html.split('\n')
    else:
        htmllist = html

    return htmllist

def findevent(html, startpos):
    htmllist = check_html_is_list(html)

    event = {}
    for n, line in [(n, longline.lstrip()) for n, longline in enumerate(htmllist)]:
        if line.startswith('<tr class="covidrow'):
            event = {'linestart': n + startpos, 'enddate': False, 'newevent': True}
        # Event dates
        elif line.startswith('<td class="columnb1">'):
            wholedate = line.split('<td class="columnb1">')[1].split('</td>')[0].replace('&nbsp;', ' ')
            if any(('-' in wholedate, '&ndash;' in wholedate)):
                date = wholedate.split('&ndash;')[0].split('-')[0]
                enddate = wholedate.split('&ndash;')[-1].split('-')[-1]
                event['enddate'] = datetime.datetime.strptime(enddate, '%a %d/%m/%Y') + datetime.timedelta(days = 1) # Until midnight the following day

            else:
                date = wholedate

        # Event times
        elif line.startswith('<td class="columnb2">'):
            if '<a class="fa-ics"' in line:
                event['newevent'] = False
            else:
                wholetime = line.split('<td class="columnb2">')[1]
                vstarttime = wholetime.split('&ndash;')[0].split('-')[0].split(' ')[0]
                if '&ndash;' in wholetime:
                    vendtime = wholetime.split('&ndash;')[1].split(' ')[0]
                elif '-' in wholetime:
                    vendtime = wholetime.split('-')[1].split(' ')[0]
                else:
                    vendtime = None
                vtimezone = line.split('<td class="columnb2">')[1].split(' ')[1].split('</td>')[0]

                if vtimezone == 'BST':
                    event['timezone'] = London
                else:
                    event['timezone'] = tz.gettz() # Returns tzlocal()
                event['starttime'] = datetime.datetime.strptime(f'{date} {vstarttime}', '%a %d/%m/%Y %H:%M').replace(tzinfo = event['timezone'])
                if vendtime:
                    event['endtime'] = datetime.datetime.strptime(f'{date} {vendtime}', '%a %d/%m/%Y %H:%M').replace(tzinfo = event['timezone'])
                else:
                    event['endtime'] = event['starttime'] + datetime.timedelta(hours = 1) # Default event length to 1 h
                
        elif line.startswith('<td class="columnb3">'):
            if event['newevent']:
                event['url'] = line.split('<td class="columnb3"><a href="')[1].split('"')[0]
                description = []
                for nextline in [longnextline.strip() for longnextline in htmllist[n+1:]]:
                    if not nextline.startswith('<td'):
                        description.append(nextline.replace('<br>', '\n'))
                    else:
                        description[-1] = description[-1].split('</td>')[0]
                        event['description'] = ('').join(('').join(description).split('</a>'))
                        event['title'] = event['description'].split('</a>')[0].split('\n')[0].split(' (')[0]
                        break
        elif line.startswith('<td class="columnb4">'):
            if event['newevent']:
                event['organizer'] = line.split('<td class="columnb4">')[1].split('</td>')[0]
        elif line.startswith('</tr>'):
            event['lineend'] = n + startpos
            break

    return event

def ics_from_event(event):
    icstext = vcalendarhead

    # Add date and time information
    cdatetime = datetime.datetime.now()
    try:
        if event['timezone']._filename == 'GB-Eire':
            tzid = 'Europe/London'
            dtstarttext = f'DTSTART;TZID={tzid}:{event["starttime"].strftime("%Y%m%dT%H%M00")}'
            dtendtext = f'DTEND;TZID={tzid}:{event["endtime"].strftime("%Y%m%dT%H%M00")}'
            icstext = icstext + vtimezone
    except AttributeError: # Thrown for tzlocal()
        tzid = 'UTC'
        dtstarttext = f'DTSTART:{event["starttime"].strftime("%Y%m%dT%H%M00")}Z'
        dtendtext = f'DTEND:{event["endtime"].strftime("%Y%m%dT%H%M00")}Z'
    icstext = icstext + ['BEGIN:VEVENT', f'DTSTAMP:{cdatetime.strftime("%Y%m%dT%H%M00")}', dtstarttext, dtendtext, \
                         'X-MICROSOFT-CDO-BUSYSTATUS:BUSY', 'X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY']
    if event['enddate']:
        icstext.append(f'RRULE:FREQ=DAILY;UNTIL={event["enddate"].strftime("%Y%m%dT000000")}') # Doesn't allow different times on different days

    # Add summary, UID, TZID
    uid = f'{cdatetime.strftime("%Y%m%dT%H%M00")}-{event["linestart"] + 1}-online@supersciencegrl.co.uk'
    eventtype = event['description'].split(' ')[-1].split('&nbsp;')[-1].replace('(', '').replace(')', '')

    # Add description and tail
    descriptionhead = f'DESCRIPTION:{event["description"].replace("&nbsp;", " ").replace("<strong>", "").replace("</strong>", "")}'.replace(',', '\\,')
    icsdescriptiontail = descriptiontail.replace('%URL%', event['url']).replace('%EVENTTYPE%', eventtype).replace('%ORGANIZER%', event['organizer']).replace(',', '\\,').replace('\n', '\\n')
    description = f'{descriptionhead}{icsdescriptiontail}'.replace('&#163;', '£').replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&')
    splitdescription = []
    for index in range(0, len(description), 74):
        splitdescription.append(description[index:index+74])
    title = event['title'].replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&')
    icstext = icstext + [f'SUMMARY:{title}', f'UID:{uid}', f'TZID:{tzid}', ('\n ').join(splitdescription)] + vcalendartail

    with open(os.path.join(mydir, 'cal', f'{uid}.ics'), 'w', newline='') as fout:
        fout.writelines(line + '\n' for line in icstext)

    return f'{uid}.ics'

def gcal_from_event(event):
    text = event['title']
    eventtype = event['description'].split(' ')[-1].split('&nbsp;')[-1].replace('(', '').replace(')', '')
    detailshead = event['description'].replace('\n', '%0A').replace('&nbsp;', ' ').replace('<strong>', '').replace('</strong>', '')
    detailstail = descriptiontail.replace('\\n', '%0A').replace('%URL%', event['url']).replace('%EVENTTYPE%', eventtype).replace('%ORGANIZER%', event['organizer'])
    dates = f'{event["starttime"].strftime("%Y%m%dT%H%M00")}%2F{event["endtime"].strftime("%Y%m%dT%H%M00")}'
    try:
        if event['timezone']._filename == 'GB-Eire':
            gcaltail = 'ctz=Europe/London&sprop=website:supersciencegrl.co.uk'
    except AttributeError: # Thrown for tzlocal()
        gcaltail = 'sprop=website:supersciencegrl.co.uk'
    gcalurl = ('&').join([gcalhead, f'text={text}', f'details={detailshead}{detailstail}', 'location=Online', f'dates={dates}', gcaltail])
    if event['enddate']:
        gcalurl = f'{gcalurl}&recur=RRULE:FREQ=DAILY;UNTIL={event["enddate"].strftime("%Y%m%dT000000")}' # Doesn't allow different times on different days
    gcalurl = gcalurl.replace('&amp;', '%26').replace('#', '%23').replace('&%23', '&#').replace('&#163;', '£')

    return gcalurl

def newhtml(event, htmllist):
    eventhtml = htmllist[event['linestart']:event['lineend']+1]

    if event['newevent']:
        ics = ics_from_event(event)
        gcal = gcal_from_event(event)

        # Find the html row containing time information
        for n, row in enumerate(eventhtml):
            if row.lstrip().startswith('<td class="columnb2">'):
                timerow = n
                break

        indent = eventhtml[timerow].count('\t') * '\t'
        eventhtml = eventhtml[:timerow] + [f'{eventhtml[timerow].split("</td>")[0]}{htmltemplate[0].replace("%ICS%", ics)}\n', \
                     f'{indent}{htmltemplate[1].replace("%GCAL%", gcal)}\n', f'{indent} {htmltemplate[2]}\n'] +\
                     eventhtml[timerow + 1:]

    return eventhtml

def updatehtml(html):
    starttime = time.time()
    htmllist = check_html_is_list(html)

    html_out = []
    firsteventfound = False
    lasteventfound = False
    eventcount = 0
    for n, row in enumerate(htmllist):
        if row.lstrip().startswith('<tr class="covidrow">'):
            eventcount += 1
            firsteventfound = True
            event = findevent(htmllist[n:], n)
            eventhtml = newhtml(event, htmllist)

            html_out = html_out + eventhtml
        if row.lstrip().startswith('</tbody>'):
            lasteventfound = True
        if not firsteventfound or lasteventfound:
            html_out.append(row)
        elif not row.lstrip():
            html_out.append(row)

    with open(os.path.join(testdir, 'online.html'), 'w') as fout:
        fout.writelines(html_out)
    endtime = time.time()
    
    return f'{endtime - starttime} s', f'{eventcount} entries'

def printsingleevent(html):
    event = findevent(html, 0)
    htmllist = check_html_is_list(html)
    html_out = newhtml(event, htmllist)
    print(('\n').join(html_out).replace('\n\n', '\n'))

examplehtml = '''								<tr class="covidrow">
									<td class="columnb1">Fri 22/04/2020</td>
									<td class="columnb2">15:00 BST</td>
									<td class="columnb3"><a href="https://www.genscript.com/webinars/engineering-protease-activatable-adeno-associated-virus.html" target="_blank">
									Susan Butler &ndash; Engineering protease-activatable adeno-associated virus (AAV) for targeted delivery through library design</a> (webinar)</td>
									<td class="columnb4">GenScript</td>
								</tr>'''

# Time zones
London = tz.gettz('Europe/London')

# Extended standard event description
descriptiontail = '''\\n\\nPlease visit %URL% for more information. Note: you may need to \
register separately for this event. \\n\\nThis %EVENTTYPE% is run by %ORGANIZER%. \\n\\nThis is an auto-generated placeholder event created by \
Nessa Carson at https://supersciencegrl.co.uk. Please check with %ORGANIZER% for any registration links, passwords, or possible changes to \
the event. I do not hold any responsibility for this %EVENTTYPE%. '''

# .ics standard lines
vcalendarhead = ['BEGIN:VCALENDAR', 'PRODID:-//supersciencegrl.co.uk/', 'VERSION:2.0']
vtimezone = ['BEGIN:VTIMEZONE', 'TZID:Europe/London', 'TZURL:http://tzurl.org/zoneinfo-outlook/Europe/London', 'X-LIC-LOCATION:Europe/London', \
             'BEGIN:DAYLIGHT', 'TZOFFSETFROM:+0000', 'TZOFFSETTO:+0100', 'TZNAME:BST', 'DTSTART:19700329T010000', 'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU', \
             'END:DAYLIGHT', 'BEGIN:STANDARD', 'TZOFFSETFROM:+0100', 'TZOFFSETTO:+0000', 'TZNAME:GMT', 'DTSTART:19701025T020000', \
             'RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU', 'END:STANDARD', 'END:VTIMEZONE']
vcalendartail = ['LOCATION:Online', 'BEGIN:VALARM', 'TRIGGER:-PT10M', 'ACTION:DISPLAY', 'DESCRIPTION:Reminder', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR']

# GCal standard strings
gcalhead = 'https://www.google.com/calendar/render?action=TEMPLATE'

# html text to insert
htmltemplate = [' <a class="fa-ics" href="https://supersciencegrl.co.uk/cal/%ICS%"><br><i class="far fa-calendar-alt"></i></a>', \
'<a class="fa-gcal" href="%GCAL%" target="_blank">', \
'<i class="far fa-calendar-alt"></i></a></td>']

html_in = []
with open('online.html', 'r') as fin:
    for line in fin:
        html_in.append(line)
