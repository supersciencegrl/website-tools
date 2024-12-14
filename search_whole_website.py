import glob
import os

import tabulate

baseFolder = r"C:\Users\kfsd435\GitHub\supersciencegrl.github.io"
os.chdir(baseFolder)

pages = glob.glob('**/*.html', recursive=True)
exclusions = ['googlec9a765a08c18ee51.html',
              'pinterest-fc74e.html'
              ]
for exc in exclusions:
    idx = pages.index(exc)
    _ = pages.pop(idx)

print('WARNING: Recommend git push before editing for easy reversion to original.\n')
query = input('Query: ')
caseSensitive = input('Case sensitive? (Y/N) ')
if 'y' in caseSensitive.lower():
    caseSensitive = True
else:
    caseSensitive = False

#''' Note: BeautifulSoup etc does not maintain indentation '''
pagesFound = [['Page', 'Counts']]
for page in pages:
    with open(page, 'r', encoding='utf8') as fin:
        html = fin.read()

        if not caseSensitive:
            htmlLower = html.lower()
            if query.lower() in htmlLower:
                pagesFound.append([page, htmlLower.count(query.lower())])
        else:
            if query in html:
                pagesFound.append([page, html.count(query)])

suffix = ''
if not caseSensitive:
    suffix = ' (not case-sensitive)'

print(f'Instances of {query} found{suffix}:')
print(tabulate.tabulate(pagesFound, headers='firstrow', tablefmt='fancy_grid'))
