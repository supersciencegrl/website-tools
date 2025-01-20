''' This script was created for the supersciencegrl.github.io repo. A more recent version may exist in supersciencegrl/supersciencegrl.github.io '''

__author__ = "Nessa Carson"
__copyright__ = "Copyright 2023"
__version__ = "1.1"
__email__ = "methionine57@gmail.com"
__status__ = "Production"

import glob

def search_for_query(pages: list[str], query: str, print_page_counts=False):
    '''
    Searches through a list of html pages for the presence of a specified query string.
    Args:
        pages (list): A list of file paths to the html pages to be searched.
        query (str): The query string to be searched for.

    Prints the file paths and number of instances of the query string found in each page.
    Also prints the total number of pages where the query string was found.
    '''
    pages_found = 0    
    for page in pages:
        with open(page, 'r+', encoding='utf8') as fin:
            html = fin.read()
            page_count = html.count(query)
            if page_count:
                if print_page_counts:
                    print(f'{page}:\t{page_count} instances found in html.')
                pages_found += 1

    if pages_found:
        print(f'\nTotal pages: {pages_found}\n')
    else:
        print('\nQuery not found in folder!\n')

pages = glob.glob('../**/*.html', recursive=True)
exclusions = ['googlec9a765a08c18ee51.html', 'pinterest-fc74e.html', 'sandbox.html']
for exc in exclusions:
    idx = pages.index(exc)
    _ = pages.pop(idx)

while True:
    query = input('Search query: ')
    if '-pages' in query or '--p' in query:
        query = query.replace(' --p', '')
        search_for_query(pages, query, print_page_counts=True)
    else:
        search_for_query(pages, query, print_page_counts=False)