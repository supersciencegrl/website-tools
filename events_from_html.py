__author__ = "Nessa Carson"
__copyright__ = "Copyright 2020"
__version__ = "1.4"
__email__ = "methionine57@gmail.com"
__status__ = "Production"

import datetime
from dateutil import tz
import os
import time
from shutil import copy2

print(f'events-from-html.py v.{__version__}')
# Last edited 2020-Apr-25 09:10

if os.path.isdir('C:\\Users\\Nessa\\Documents\\GitHub\\supersciencegrl.github.io'):
    mydir = 'C:\\Users\\Nessa\\Documents\\GitHub\\supersciencegrl.github.io'
    testdir = 'C:\\Users\\Nessa\\Documents\\GitHub\\website-tools'
else:
    mydir = 'C:\\Users\\S1024501\\OneDrive - Syngenta\\Documents\\GitHub\\supersciencegrl.github.io'
    testdir = 'C:\\Users\\S1024501\\OneDrive - Syngenta\\Documents\\GitHub\\website-tools'

os.chdir(mydir)

def check_html_is_list(html):
    if type(html) is str:
        htmllist = html.split('\n')
    else:
        htmllist = html

    return htmllist

def gettimezone(time_line):
    vtimezone = time_line.split('<td class="columnb2">')[1].split(' ')[1].split('</td>')[0]
    if vtimezone == 'BST':
        result = London
    else:
        result = tz.gettz() # Returns tzlocal

    return result

def findevent(html, startpos):
    htmllist = check_html_is_list(html)

    event = {}
    for n, line in [(m, longline.lstrip()) for m, longline in enumerate(htmllist)]:
        if line.startswith('<tr class="covidrow'):
            event = {'linestart': n + startpos, 'enddate': False, 'newevent': True, 'allday': False}
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
            elif 'all day' in line.lower():
                event['allday'] = True
                event['starttime'] = datetime.datetime.strptime(date, '%a %d/%m/%Y')
                event['timezone'] = gettimezone(line)
            else:
                wholetime = line.split('<td class="columnb2">')[1].replace('&#8209;', '-')
                vstarttime = wholetime.split('&ndash;')[0].split('-')[0].split(' ')[0]
                if any(('&ndash;' in wholetime, '-' in wholetime)):
                    vendtime = wholetime.split('&ndash;')[-1].split('-')[-1].split(' ')[0]
                else:
                    vendtime = None
                event['timezone'] = gettimezone(line)
                
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
                event['eventtype'] = event['description'].split('(')[-1].split(',')[-1].replace('&nbsp;', ' ').replace(')', '')
        elif line.startswith('<td class="columnb4">'):
            if event['newevent']:
                event['organizer'] = line.split('<td class="columnb4">')[1].split('</td>')[0]
        elif line.startswith('</tr>'):
            event['lineend'] = n + startpos
            break

    return event

def ics_from_event(event):
    icstext = vcalendarhead
    tzid = 'UTC' # default value

    # Add date and time information
    cdatetime = datetime.datetime.now()
    if event['allday']:
        dtstarttext = f'DTSTART;VALUE=DATE:{event["starttime"].strftime("%Y%m%d")}'
        if event['enddate']:
            dtendtext = f'DTEND;VALUE=DATE:{event["enddate"].strftime("%Y%m%d")}'
        else:
            enddate = event['starttime'] + datetime.timedelta(days = 1) # Set enddate to 1 day later for single-day, all-day event per ics requirements
            dtendtext = f'DTEND;VALUE=DATE:{enddate.strftime("%Y%m%d")}'
    else:
        try:
            if event['timezone']._filename == 'GB-Eire':
                tzid = 'Europe/London'
                dtstarttext = f'DTSTART;TZID={tzid}:{event["starttime"].strftime("%Y%m%dT%H%M00")}'
                dtendtext = f'DTEND;TZID={tzid}:{event["endtime"].strftime("%Y%m%dT%H%M00")}'
                icstext = icstext + vtimezone
        except AttributeError: # Thrown for tzlocal()
            dtstarttext = f'DTSTART:{event["starttime"].strftime("%Y%m%dT%H%M00")}Z'
            dtendtext = f'DTEND:{event["endtime"].strftime("%Y%m%dT%H%M00")}Z'
    icstext = icstext + ['BEGIN:VEVENT', f'DTSTAMP:{cdatetime.strftime("%Y%m%dT%H%M00")}', dtstarttext, dtendtext, \
                         'X-MICROSOFT-CDO-BUSYSTATUS:BUSY', 'X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY']
    if event['enddate'] and not event['allday']:
        icstext.append(f'RRULE:FREQ=DAILY;UNTIL={event["enddate"].strftime("%Y%m%dT000000")}') # Doesn't allow different times on different days

    # Add summary, UID, TZID
    uid = f'{cdatetime.strftime("%Y%m%dT%H%M%S")}-{event["linestart"] + 1}-online@supersciencegrl.co.uk'
    eventtype = event['eventtype']

    # Add description and tail
    descriptionhead = f'DESCRIPTION:{event["description"].replace("&nbsp;", " ").replace("<strong>", "").replace("</strong>", "")}'.replace(',', '\\,')
    icsdescriptiontail = descriptiontail.replace('%URL%', event['url']).replace('%EVENTTYPE%', eventtype).replace('%ORGANIZER%', event['organizer']).replace(',', '\\,').replace('\n', '\\n')
    description = f'{descriptionhead}{icsdescriptiontail}'.replace('&#163;', '£').replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&')
    splitdescription = []
    for index in range(0, len(description), 74):
        splitdescription.append(description[index:index+74])
    title = event['title'].replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&')

    if tzid != 'UTC':
        vcalendarmiddle = [f'SUMMARY:{title}', f'UID:{uid}', ('\n ').join(splitdescription)]
    else:
        vcalendarmiddle = [f'SUMMARY:{title}', f'UID:{uid}', f'TZID:{tzid}', ('\n ').join(splitdescription)]
    if event['allday']:
        icstext = icstext + vcalendarmiddle + vcalendaralldaytail
    else:
        icstext = icstext + vcalendarmiddle + vcalendartail

    with open(os.path.join(mydir, 'cal', f'{uid}.ics'), 'w', newline='', encoding = 'utf-8') as fout:
        fout.writelines(line + '\n' for line in icstext)

    return f'{uid}.ics'

def gcal_from_event(event):
    title = event['title']
    eventtype = event['eventtype']
    detailshead = event['description'].replace('\n', '%0A').replace('&nbsp;', ' ').replace('<strong>', '').replace('</strong>', '')
    detailstail = descriptiontail.replace('\\n', '%0A').replace('%URL%', event['url']).replace('%EVENTTYPE%', eventtype).replace('%ORGANIZER%', event['organizer'])
    if event['allday']:
        if event['enddate']:
            dates = f'{event["starttime"].strftime("%Y%m%d")}/{event["enddate"].strftime("%Y%m%d")}'
        else:
            enddate = event['starttime'] + datetime.timedelta(days = 1) # Set enddate to 1 day later for single-day, all-day event per Google requirements
            dates = f'{event["starttime"].strftime("%Y%m%d")}/{enddate.strftime("%Y%m%d")}'
    else:
        dates = f'{event["starttime"].strftime("%Y%m%dT%H%M00")}%2F{event["endtime"].strftime("%Y%m%dT%H%M00")}'
    try:
        if event['timezone']._filename == 'GB-Eire':
            gcaltail = 'ctz=Europe/London&sprop=website:supersciencegrl.co.uk'
    except AttributeError: # Thrown for tzlocal()
        gcaltail = 'sprop=website:supersciencegrl.co.uk'
    gcalurl = ('&').join([gcalhead, f'text={title}', f'details={detailshead}{detailstail}', 'location=Online', f'dates={dates}', gcaltail])
    if event['enddate'] and not event['allday']:
        gcalurl = f'{gcalurl}&recur=RRULE:FREQ=DAILY;UNTIL={event["enddate"].strftime("%Y%m%dT000000")}' # Doesn't allow different times on different days
    gcalurl = gcalurl.replace('&ndash;', '–').replace('&amp;', '%26').replace('#', '%23').replace('&%23', '&#').replace('&#163;', '£')

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
        elif row.lstrip().startswith('</tbody>'):
            lasteventfound = True
        if not firsteventfound or lasteventfound:
            html_out.append(row)
        elif not row.lstrip():
            html_out.append(row)

    # Copy original file to testdir in case of corruption
    copy2(os.path.join(mydir, 'online.html'), os.path.join(testdir, 'online.html'))
    with open(os.path.join(mydir, 'online.html'), 'w') as fout:
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

examplehtml2 = '''								<tr class="covidrow">
									<td class="columnb1">Fri 22/04/2020</td>
									<td class="columnb2">All day</td>
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
vcalendaralldaytail = ['LOCATION:Online', 'BEGIN:VALARM', 'TRIGGER:-PT12H', 'ACTION:DISPLAY', 'DESCRIPTION:Reminder', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR']

# GCal standard strings
gcalhead = 'https://www.google.com/calendar/render?action=TEMPLATE'

# html text to insert
htmltemplate = [' <a class="fa-ics" href="https://supersciencegrl.co.uk/cal/%ICS%"><br><i class="far fa-calendar-alt" title="Save to Outlook"></i></a>', \
'<a class="fa-gcal" href="%GCAL%" target="_blank" rel="noopener">', \
'<i class="far fa-calendar-alt" title="Save to Google Calendar"></i></a></td>']

html_in = []
with open(os.path.join(mydir, 'online.html'), 'r') as fin:
    for line in fin:
        html_in.append(line)
