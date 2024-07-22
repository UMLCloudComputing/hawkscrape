from bs4 import BeautifulSoup
import requests
import re
from time import sleep
from urllib.parse import urlparse

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
    return filename + ".txt"

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

        with open(f"Content{url_to_filename(sub_url)}.md", "a") as content_file:    
            # Check and write the <title> tag content if present
            title_tag = soup.find('title')
            if title_tag:
                content_file.write(f"# {title_tag.get_text(strip=True)}\n\n")

            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                # Determine the tag name
                tag_name = element.name
                text_content = element.get_text(strip=True)

                # Check if the element is a header and prefix accordingly
                if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content_file.write(f"## {text_content}\n\n")
                else:  # For paragraphs and other text, write as regular text
                    content_file.write(f"{text_content}\n\n")

        #Wait a bit before it requests the next URL in the loop
        sleep(3)

if __name__ == "__main__":
    main(["/about/", "/student-life", "/admissions-aid", "/thesolutioncenter/bill"])

