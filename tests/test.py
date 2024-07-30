import boto3
import requests
import re
import os
from dotenv import load_dotenv
load_dotenv()
from bs4 import BeautifulSoup

def extract_tags(soup, pattern):
    loc_tags = soup.find_all('loc', string=pattern)
    lastmod_tags = soup.find_all('lastmod')
    
    tags_dict = {}
    for loc_tag in loc_tags:
        loc_text = loc_tag.get_text()
        lastmod_tag = loc_tag.find_next_sibling('lastmod')
        if lastmod_tag:
            tags_dict[loc_text] = lastmod_tag.get_text()
    return tags_dict

def main(substrings : list) -> None:
    s3 = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"), region_name='us-east-1')
    bucket_name = "xmlbuckethawkscrapetest"
    sitemap = s3.get_object(Bucket=bucket_name, Key="sitemap.xml")['Body'].read()
    local_soup = BeautifulSoup(sitemap, features="xml")

    origin_url = 'https://www.uml.edu/sitemap.xml' 
    page = requests.get(origin_url)
    remote_soup = BeautifulSoup(page.content, features = "xml")

    s3_tags = extract_tags(local_soup, re.compile('|'.join(substrings)))
    remote_tags = extract_tags(remote_soup, re.compile('|'.join(substrings)))

    modified_urls = {
        url: remote_tags[url] 
        for url in remote_tags 
        if url not in s3_tags or remote_tags[url] != s3_tags[url]
    }

    print(modified_urls)

if __name__ == "__main__":
    main(["/thesolutioncenter/"])