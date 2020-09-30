__author__ = "Nessa Carson"
__copyright__ = "Copyright 2020"
__version__ = "1.0"
__email__ = "methionine57@gmail.com"
__status__ = "Production"

import os
import time
from shutil import copy2

print(f'remove-ics-links.py v.{__version__}')
''' This script is modified from the mother script events-from-html.py '''

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

def updateevent(html):
    htmllist = check_html_is_list(html)
    event = []

    for line in htmllist:
        if line.lstrip().startswith('<tr class="covidrow'):
            event = [line]

        # Remove ics link
        elif event and line.lstrip().startswith('<td class="columnb2'):
            if '<a class="fa-ics"' in line:
                newline = line.partition(' href="https://supersciencegrl.co.uk/')[0] + line.partition('@supersciencegrl.co.uk.ics"')[2]
                event.append(newline)

        elif event and not line.lstrip().startswith('</tr>'): # For all other rows within the event
            event.append(line)
                
        elif event: # Row starting with '</tr>'
            event.append(line)
            
            return event

def updatehtml(html):
    starttime = time.time()
    htmllist = check_html_is_list(html)

    html_out = []
    firsteventfound = False
    lasteventfound = False
    eventcount = 0
    for n, row in enumerate(htmllist):
        if row.lstrip().startswith('<tr class="covidrow'):
            eventcount += 1
            firsteventfound = True
            event = updateevent(htmllist[n:])

            html_out = html_out + event
        elif row.lstrip().startswith('</tbody>'):
            lasteventfound = True
        if not firsteventfound or lasteventfound:
            html_out.append(row)
        elif not row.lstrip():
            html_out.append(row)

    # Copy original file to testdir in case of corruption
    copy2(os.path.join(mydir, inputfile), os.path.join(testdir, inputfile))
    with open(os.path.join(mydir, inputfile), 'w') as fout:
        fout.writelines(html_out)
    endtime = time.time()
    
    return f'{round(endtime - starttime, 4)} s', f'{eventcount} entries'

html_in = []
inputfile = 'online-old.html'

with open(os.path.join(mydir, inputfile), 'r') as fin:
    for line in fin:
        html_in.append(line)
