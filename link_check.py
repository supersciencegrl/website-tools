from collections import Counter
from pathlib import Path
from typing import Sequence

from bs4 import BeautifulSoup
import requests

''' Debug mode '''
DEBUG = False

def get_html(url: str) -> bytes | None:
    """
    Fetches the HTML content of a given URL.

    Sends an HTTP GET request to the specified URL and returns the response
    content as bytes if the request is successful (status code 200). Returns
    None for non-200 responses.

    Args:
        url (str): The URL to retrieve.

    Returns:
        bytes | None: The raw HTML content as bytes when successful, otherwise None.
    """
    r = requests.get(url)
    if r.status_code == 200:
        page = r.content # r.content contains byte objects, unlike r.text
    else:
        return None

    return page

def parse_filename(filename: str) -> Path:
    """
    Constructs a Path for a filename, ensuring a .html suffix.

    Creates a Path from the provided filename. If the path is relative, it is
    resolved against the default directory (mydir). The returned path is forced
    to have a .html file suffix.

    Args:
        filename (str): The file name or path to convert into a Path.

    Returns:
        Path: The absolute or mydir-resolved Path with a .html suffix.
    """
    path = Path(filename)

    if not path.is_absolute(): # Use mydir as default folder
        path = mydir / path

    return path.with_suffix('.html') # Ensure .html suffix

def print_links(filepath: Path, 
                linklist: Sequence[str], 
                min_count: int = 1, 
                no_duplicates: bool = True
                ):
    """
    Pretty-prints links from a list with optional frequency filtering.

    Prints each link and its occurrence count when the count is greater than or
    equal to min_count. If short is True, each qualifying link is printed only
    once even if it appears multiple times in the list.

    Args:
        linklist (list[str]): The list of link strings to print and count.
        min_count (int, optional): Minimum number of occurrences required for a
            link to be printed. Defaults to 1.
        no_duplicates (bool, optional): If True, avoid printing duplicate entries. 
            Defaults to True.
    """
    print(f'From {filepath.name}:\n')
    
    link_counts = Counter(linklist) # Counts occurrences of each link
    for link, count in link_counts.items():
        if count >= min_count:
            print(f'{link} ({count})')
            if no_duplicates:
                continue # Avoid printing dupliactes

def run() -> tuple[list[str], list[str], Sequence[str]]:
    """
    Load an HTML file, extract links, classify them, and print duplicate externals.

    Reads the specified HTML file, parses all anchor elements, classifies links
    into internal (starting with '/' or '#') and external, identifies duplicate
    external links excluding those in excluded_links, prints them, and returns
    the three link collections.

    Returns:
        tuple[list[str], list[str], list[str]]: A tuple containing:
            - internal_links: Links starting with '/' or '#'.
            - external_links: Links not classified as internal.
            - duplicate_links: External links that occur more than once and are
              not in excluded_links.
    """
    def is_internal_link(href: str) -> bool:
        return href.startswith('/') or href.startswith('#')
    
    filename = 'learning.html' if DEBUG else input('Page filename: ') # Default to learning.html
    filepath = parse_filename(filename)

    try:
        content = Path(filepath).read_bytes()
    except FileNotFoundError:
        print('Not found.')
        return [], [], []

    # Read page and retrieve all links
    soup = BeautifulSoup(content, 'html.parser')
    links = soup.find_all('a')

    # Categorize links
    internal_links = [link['href'] for link in links if is_internal_link(link['href'])]
    external_links = [link['href'] for link in links if link['href'] not in internal_links]

    # Find duplicate external links
    external_link_counts = Counter(external_links)
    duplicate_links = [href for href, count in external_link_counts.items()
                        if count > 1 and href not in excluded_links
                        ]

    print_links(filepath, duplicate_links, no_duplicates = True)

    return internal_links, external_links, duplicate_links

mydir = Path(r"C:/Users/methi/GitHub/supersciencegrl.github.io/")

excluded_links = ['https://bsky.app/profile/supersciencegrl.co.uk',
                    'https://github.com/supersciencegrl/',
                    'https://ko-fi.com/supersciencegrl',
                    'https://www.linkedin.com/in/nessacarson/'
                    ]