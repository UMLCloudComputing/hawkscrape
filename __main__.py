from bs4 import BeautifulSoup
import requests
import re
from time import sleep

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


        # Go through all text content on page (p, h1, h2, etc) using .strings instance variable
        for p_tag in soup.stripped_strings:
        
            #Open txt file in append mode. Will not truncate contents if file with that name is created. If not created, will create new file.
            with open ("optimization_content.txt", "a") as content_file:
                
                #File is automatically closed once done
                content_file.write(p_tag)

        #Wait a bit before it requests the next URL in the loop
        sleep(3)

if __name__ == "__main__":
    main(["/about/", "/student-life", "/admissions-aid", "/thesolutioncenter/bill"])

