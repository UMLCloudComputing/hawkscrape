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

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def url_to_filename(url):
    # Parse the URL
    parsed_url = urlparse(url)
    # Extract the domain name and path
    netloc = parsed_url.netloc
    path = parsed_url.path
    # Replace slashes with underscores and remove unsafe characters
    safe_path = re.sub(r'[^a-zA-Z0-9\-_\.]', '', path.replace('/', '_'))
    # Concatenate and ensure the filename is not too long
    filename = f"{netloc}_{safe_path}".strip("_")
    # Limit filename length to 255 characters (common maximum for filesystems)
    filename = (filename[:252] + '...') if len(filename) > 255 else filename
    return filename

def main(substrings: list) -> None: 
    
    origin_url = 'https://www.uml.edu/sitemap.xml' 

    # Call get method to request that page
    page = requests.get(origin_url)

    # Parse using XML 
    soup = BeautifulSoup(page.content, features = "xml")

    # Compile a regular expression pattern to match any of the substrings. Read more about RegEx expressions if interested.
    pattern = re.compile('|'.join(substrings))

    # Find all <loc> tags that contain any of the substrings using the compiled pattern 
    filtered_loc_tags = soup.find_all('loc', string=pattern)

    for sub_url in filtered_loc_tags:
        # Convert html into text
        sub_url = sub_url.get_text() 
    
        # Note: Will override former "soup" variable contents (uml.edu/sitemap.xml). Not an issue though because we already got everything we needed from uml.edu/sitemap.xml.
        page = requests.get(sub_url) 

        # Parse using HTML
        soup = BeautifulSoup(page.content, "html.parser") 

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

        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul']):
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
            else:  # For paragraphs and other text, write as regular text
                parsed_text += f"{text_content}\n\n"

        filename_base = url_to_filename(sub_url) + ".md"
        metadata_filename = f"{filename_base}.metadata.json"

        # Metadata dictionary
        metadata = {
            "metadataAttributes": {
                "url": sub_url
            }
        }

        json_content = json.dumps(metadata).encode('utf-8')

        # File writing logic

        # Initialize S3 Bucket. Then get the S3 bucket connected to the knowledge base
        s3 = boto3.client('s3', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
        bucket_name = getS3Address(os.getenv("KB_ID"))

        # Put parsed file into bucket
        s3.put_object(Bucket=bucket_name, Key=filename_base, Body=parsed_text)

        # Put metadata file into bucket
        s3.put_object(Bucket=bucket_name, Key=metadata_filename, Body=BytesIO(json_content))
        
        # Wait a bit before it requests the next URL in the loop
        sleep(3)

def ingest_data(knowledge_base):
    client = boto3.client('bedrock-agent', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    data_src_list = client.list_data_sources(knowledgeBaseId=knowledge_base, maxResults=123)['dataSourceSummaries']
    id = data_src_list[0]['dataSourceId']
    response = client.start_ingestion_job(
        dataSourceId=id,
        knowledgeBaseId=knowledge_base
    )

if __name__ == "__main__":
    main(["/thesolutioncenter/bill"])
    ingest_data(os.getenv("KB_ID"))

