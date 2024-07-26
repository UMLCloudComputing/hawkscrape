from bs4 import BeautifulSoup
import requests
import re
from time import sleep
from urllib.parse import urlparse
import json
import os
import boto3
from io import BytesIO
from s3 import *
from dotenv import load_dotenv
load_dotenv()

def extract(soup):
    # Remove Headers, Footers, and Sidebars
    footer = soup.find("footer", class_="layout-footer")
    if footer:
        footer.decompose()
    
    for nav_element in soup.find_all(class_='l-page__nav'):
        nav_element.decompose()
    
    header_inside = soup.find("div", class_="layout-header__inside")
    if header_inside:
        header_inside.decompose()

    header_inside = soup.find("div", class_="layout-header__nav")
    if header_inside:
        header_inside.decompose()
    
    header_inside = soup.find("div", class_="layout-header__quick-links")
    if header_inside:
        header_inside.decompose()

    header_inside = soup.find("div", class_="l-supplemental-content")
    if header_inside:
        header_inside.decompose()


    parsed_text = ""
    
    title_tag = soup.find('title')
    if title_tag:
        parsed_text += f"# {title_tag.get_text(strip=True)}\n\n"

    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'table']):
        # Determine the tag name
        tag_name = element.name
        text_content = element.get_text(strip=True)

        # Check if the element is a header and prefix accordingly
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            parsed_text += f"## {text_content}\n\n"
        elif tag_name == 'ul':
            markdown_list = [f"- {li.text.strip()}" for li in element.find_all('li')]
            markdown_output = "\n".join(markdown_list)
            parsed_text += f"{markdown_output}\n\n"
        elif tag_name == 'table':
            # Extract table headers
            headers = [header.get_text(strip=True) for header in element.find_all('th')]

            # Extract table rows
            rows = []
            for row in element.find_all('tr')[1:]:  # Skip the header row
                cells = row.find_all('td')
                row_data = [cell.get_text(strip=True) for cell in cells]
                rows.append(row_data)

            # Write the cleaned-up table to the parsed_text variable
            table_string = " | ".join(headers) + "\n"
            table_string += "|".join(["---"] * len(headers)) + "\n"
            for row in rows:
                table_string += " | ".join(row) + "\n"
            
            parsed_text += f"{table_string}\n\n"
        else:  # For paragraphs and other text, write as regular text
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