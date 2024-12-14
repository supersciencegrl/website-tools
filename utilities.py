from pathlib import Path

from bs4 import BeautifulSoup

def parse_html(html_doc: Path) -> BeautifulSoup:
    """
    Parses an HTML file and returns a BeautifulSoup object.

    This function opens an HTML file, reads its content, and parses it
    using BeautifulSoup with the 'html.parser'. The resulting BeautifulSoup
    object can be used to navigate and search the HTML document.

    Parameters:
    - html_doc (Path): The file path to the HTML document to be parsed.

    Returns:
    - BeautifulSoup: A BeautifulSoup object representing the parsed HTML document.

    Raises:
    - FileNotFoundError: If the specified file does not exist.
    - IOError: If an error occurs while reading the file.
    """
    with open(html_doc, 'r') as fin:
        content = fin.read()
    soup = BeautifulSoup(content, 'html.parser')

    return soup

def retrieve_class_names(soup: BeautifulSoup, section_classes: list[str]=None) -> set:
    """
    Retrieves a set of unique class names from div elements. 
    Originally used on learning.html to check for alternative class names to add to the 
    improved filter checkbox list. 

    If no section classes are specified, retrieves class names from all div elements. 
    If section classes are provided, only retrieves class names from div elements that 
    have any of the specified section classes, excluding those section classes from the result.

    Parameters:
    - soup (BeautifulSoup): A BeautifulSoup object representing a parsed HTML document.
    - section_classes (list[str], optional): A list of class names to search for in div 
        elements. Defaults to None.

    Returns:
    - set: A set containing unique class names found in the div elements, excluding the 
        section classes if specified. 
    """
    divs = []
    # If no section_classes provided, find all divs
    if not section_classes:
        section_classes = [] # SonarLint shouted at me for using [] as default value
        divs += soup.find_all('div')
    # Else, find only divs with the desired classes
    else:
        for class_name in section_classes:
            divs += soup.find_all('div', class_ = class_name)
    
    # Retrieve all class names for these divs except for section_classes
    other_classes = set()
    for div in divs:
        classes = div.get('class', [])
        other_classes.update(c for c in classes if c not in section_classes)

    return other_classes

inputfile = Path(r"C:\Users\kfsd435\GitHub\supersciencegrl.github.io\learning.html")
section_classes = ["div-literature"]

soup = parse_html(inputfile)
retrieve_class_names(soup, section_classes)