''' This script was created for the supersciencegrl.github.io repo. A more recent version may exist in supersciencegrl/supersciencegrl.github.io '''

import glob

def checksublist(mylist, snippet):
    listlength = len(mylist)
    snippetlength = len(snippet)
    idxlist = [i for i in range(listlength-snippetlength+1) if snippet == mylist[i:i+snippetlength]]

    return idxlist

def inputToHtml(myinput):
    mylist = myinput.split('\\n')
    editedlist = [i+'\n' for i in mylist]

    return editedlist

pages = glob.glob('**/*.html', recursive=True)
exclusions = ['googlec9a765a08c18ee51.html', 'pinterest-fc74e.html']
for exc in exclusions:
    idx = pages.index(exc)
    _ = pages.pop(idx)

print('WARNING: Recommend git push before editing for easy reversion to original.\n')
oldhtml = input('Old html (include \\t; replace newlines with \'\\n\'): ')
oldhtml = inputToHtml(oldhtml)

newhtml = input('New html (include \\t; replace newlines with \'\\n\'): ')
newhtml = inputToHtml(newhtml)

# Example html
#oldhtml = ['\t<meta property="og:image" content="http://www.supersciencegrl.co.uk/SuperScienceGrl.png">\n',
#           '\t<meta property="og:image:alt" content="Nessa Carson website: a chemistry repository">\n',
#           '\t<meta property="og:image:width" content="892px">\n',
#           '\t<meta property="og:image:height" content="593px">\n']
#newhtml = ['\t<meta property="og:image" content="http://www.supersciencegrl.co.uk/SuperScienceGrl2.png">\n',
#           '\t<meta property="og:image:alt" content="Nessa Carson website: a chemistry repository">\n',
#           '\t<meta property="og:image:width" content="1080px">\n',
#           '\t<meta property="og:image:height" content="749px">\n']

oldlength = len(oldhtml)
newlength = len(newhtml)

#''' Note: BeautifulSoup etc does not maintain indentation '''
pageschanged = 0
for page in pages:
    with open(page, 'r+', encoding='utf8') as fin:
        html = fin.readlines()

        idxlist = checksublist(html, oldhtml)
        for idx in idxlist[::-1]:
            html[idx:idx+oldlength] = newhtml
        if idxlist:
            print(f'{page}:\t{len(idxlist)} instances of old html replaced.')
            pageschanged += 1

        fin.seek(0)
        fin.writelines(html)

print(f'\n{pageschanged} pages changed.')
