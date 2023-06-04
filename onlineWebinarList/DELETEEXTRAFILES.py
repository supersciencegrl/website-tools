# Temporary file to delete extraneous cal files

import datetime
from dateutil import tz
import glob
import os
import time
from shutil import copy2

mydir = 'C:\\Users\\Nessa\\Documents\\GitHub\\supersciencegrl.github.io'
os.chdir(mydir)

# WATCH OUT: DELETES ALL FILES IN LIST
def WARNINGdeletefiles():
    i = 0
    for e in extraneous:
        os.remove(e)
        i += 1
    print(f'{i} files removed. ')

all_ics = []
with open(os.path.join(mydir, 'online.html'), 'r') as fin:
    for line in fin:
        if line.lstrip().startswith('<td class="columnb2">'):
            all_ics.append(line.partition('/cal/')[2].partition('"><br>')[0])

os.chdir(os.path.join(mydir, 'cal'))

icsfiles = [i for i in glob.glob('**supersciencegrl**')]

extraneous = [i for i in icsfiles if i not in all_ics]
