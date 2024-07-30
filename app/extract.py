from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
load_dotenv()

def extract(soup):
    # Remove Headers, Footers, and Sidebars
    # List of selectors to find and decompose
    selectors = [
        ("footer", "layout-footer"),
        ("div", "layout-header__inside"),
        ("div", "layout-header__nav"),
        ("div", "layout-header__quick-links"),
        ("div", "l-supplemental-content"),
        ("div", "l-page__nav"),
        ("div", "c-browser-support-message")
    ]

    # Decompose elements based on selectors
    for tag, class_name in selectors:
        elements = soup.find_all(tag, class_=class_name)
        for element in elements:
            element.decompose()


    parsed_text = ""
    
    title_tag = soup.find('title')
    if title_tag:
        parsed_text += f"# {title_tag.get_text(strip=True)}\n\n"

    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'table']):
        tag_name = element.name
        text_content = element.get_text(strip=True)

        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            parsed_text += f"## {text_content}\n\n"
        elif tag_name == 'ul':
            markdown_list = [f"- {li.text.strip()}" for li in element.find_all('li')]
            markdown_output = "\n".join(markdown_list)
            parsed_text += f"{markdown_output}\n\n"
        elif tag_name == 'table':
            parsed_text += str(element) + "\n\n"
        else:
            parsed_text += f"{text_content}\n\n"

    return parsed_text

def test(url): 
    # Note: Will override former "soup" variable contents (uml.edu/sitemap.xml). Not an issue though because we already got everything we needed from uml.edu/sitemap.xml.
    page = requests.get(url) 

    # Parse using HTML
    soup = BeautifulSoup(page.content, "html.parser") 

    parsed_text = extract(soup)

    print(parsed_text)

if __name__ == "__main__":
    test("https://www.uml.edu/student-services/reslife/housing/housing-food-rates.aspx")