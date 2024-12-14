''' This script was created for the supersciencegrl.github.io repo. A more recent version may exist in supersciencegrl/supersciencegrl.github.io '''

import glob

def checkSublist(mylist, snippet):
    """
    Returns a list of indices where the `snippet` is found in the `mylist`.

    Args:
    - mylist (list): The list to search in.
    - snippet (str): The substring to search for.

    Returns:
    - idxList (list): The list of indices where the `snippet` is found in the `mylist`.
    """
    
    listLength = len(mylist)
    snippetLength = len(snippet)
    idxList = [i for i in range(listLength-snippetLength+1) if snippet == mylist[i:i+snippetLength]]

    return idxList

def inputToHtml(my_input):
    """
    Formats the input into an list of HTML lines, with newlines at the end of each line.

    Args:
    - my_input (str): The input string.

    Returns:
    - edited_list (list): The formatted HTML list.
    """
    
    mylist = my_input.split('\\n')
    edited_list = [f'{i}\n' for i in mylist]

    return edited_list

def obtain_html_from_user():
    """
    This function prompts the user to input old and new HTML data. It then converts the input to HTML format.
    
    Returns:
    str: The old HTML data entered by the user.
    str: The new HTML data entered by the user.
    """
    print('WARNING: Recommend git push before editing for easy reversion to original.\n')
    
    oldhtml = ''
    while not oldhtml:
        oldhtml = input('Old html (copy tabs as tabs without changing; replace newlines with \'\\n\'): ')
    oldhtml = inputToHtml(oldhtml)

    newhtml = ''
    while not newhtml:
        newhtml = input('New html (copy tabs as tabs without changing; replace newlines with \'\\n\'): ')
    newhtml = inputToHtml(newhtml)

    return oldhtml, newhtml

def run(pages, oldhtml, newhtml):
    """
    Replaces all instances of `oldhtml` with `newhtml` in the `pages` list of files.
    Prints a report of the changes made and the files that were not changed.
    Note: BeautifulSoup etc does not maintain indentation by default

    Args:
    - pages (list): A list of file paths to update.
    - oldhtml (str): The old HTML code to replace.
    - newhtml (str): The new HTML code to replace with.
    """
    
    pages_changed = 0
    pages_not_changed = []
    for page in pages:
        with open(page, 'r+', encoding='utf8') as fin:
            html = fin.readlines()

            idx_list = checkSublist(html, oldhtml)
            old_length = len(oldhtml)
            for idx in idx_list[::-1]:
                html[idx:idx+old_length] = newhtml
            if idx_list:
                print(f'{page}:\t{len(idx_list)} instances of old html replaced.')
                pages_changed += 1
            else:
                pages_not_changed.append(page)

            fin.seek(0)
            fin.writelines(html)
            fin.truncate() # Allows shorter file when overwriting

    print(f'\n{pages_changed} pages changed.')
    pages_not_changed_string = ('\n').join(pages_not_changed)
    print(f'Pages not changed ({len(pages_not_changed)}):\n', pages_not_changed_string)

# Set list of desired pages to change
pages = glob.glob('**/*.html', recursive=True)
exclusions = ['googlec9a765a08c18ee51.html', 'pinterest-fc74e.html']
for exc in exclusions:
    idx = pages.index(exc)
    _ = pages.pop(idx)

# Obtain user inputs and replace all oldhtml with newhtml
oldhtml, newhtml = obtain_html_from_user()
result = input('\nProceed? (Y/N) ')
if result.lower() in 'yestrue1':
    run(pages, oldhtml, newhtml)
else:
    print('Operation aborted.')
