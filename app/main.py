from bs4 import BeautifulSoup
import requests
import re
from extract import extract
from time import sleep
from urllib.parse import urlparse
import json
import os
import boto3
from io import BytesIO
from s3 import getS3Address
from dotenv import load_dotenv
load_dotenv()

AWS_ID = os.getenv("AWS_ID")
AWS_KEY = os.getenv("AWS_KEY")
BUCKET = os.getenv("BUCKET")


def handler(event, context):
    main(["/thesolutioncenter/"])
    ingest_data(os.getenv("KB_ID"))

def url_to_filename(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    path = parsed_url.path
    safe_path = re.sub(r'[^a-zA-Z0-9\-_\.]', '', path.replace('/', '_'))
    filename = f"{netloc}_{safe_path}".strip("_")
    filename = (filename[:252] + '...') if len(filename) > 255 else filename
    return filename

def extract_tags(soup, substrings, usePattern):
    print("Extracting tags")
    tags_dict = {}
    loc_text = None

    # Logic for usePattern. If function call does not want to use the substring pattern, then set local variable of substrings (which is passed as an argument) to None so that no re.search filtering occurs
   # if usePattern == False:
        #substrings = None

        # Searches using <url> tag
    for element in soup.find_all(lambda tag: tag.name == 'url' and any(re.search(substring, subtag.text) for subtag in tag.find_all('loc') for substring in substrings)):
        loc_tag = element.find('loc').get_text()
        lastmod_tag = element.find('lastmod')

        # Checks if lastmod tag exists within current url tag. If it does not exist, set lastmod_tag to None. If it exists, set lastmod_tag to its content
        if lastmod_tag is None:
            lastmod_tag = None
        else:
            lastmod_tag = lastmod_tag.get_text()
        tags_dict[loc_tag] = lastmod_tag

    return tags_dict

def main(substrings: list) -> None: 
    
    s3 = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ID"), aws_secret_access_key=os.getenv("AWS_KEY"), region_name='us-east-1')

    origin_url = 'https://www.uml.edu/sitemap.xml' 

    page = requests.get(origin_url)

    print("Successfully downloaded webpage")

    remote_soup = BeautifulSoup(page.content, features = "lxml")


    print("Finished parsing with BeautifulSoup.")
   
    sitemap_file_to_create = ""

 
    remote_tags = ""

    # The "try" will fully execute if there is a sitemap.xml file in the specified bucket (BUCKET env variable)
    try:

        sitemap = s3.get_object(Bucket=BUCKET, Key="sitemap.xml")['Body'].read()
        local_soup = BeautifulSoup(sitemap, features="lxml")
        s3_tags = extract_tags(local_soup, substrings, False)

      
        # Urls that need to be updated
        urls = {
            url: remote_tags[url] 
            for url in remote_tags 
            if url not in s3_tags or remote_tags[url] != s3_tags[url]
        }
    
        urls_whose_content_doesnt_need_to_be_updated = ""
        for url in s3_tags:
            if url not in urls:
                urls_whose_content_doesnt_need_to_be_updated += f"<url>\n  <loc>{url}</loc>\n  <lastmod>{s3_tags[url]}</lastmod> \n</url>"

        sitemap_file_to_create+=urls_whose_content_doesnt_need_to_be_updated
        
       

    # If the "try" doesn't fully execute, meaning that there is no sitemap.xml file in the specified bucket, then the below "exception" will execute
    except Exception as e:
        
        remote_tags = extract_tags(remote_soup, substrings, True)
        urls = remote_tags.keys()

    try:
        #print(remote_tags.keys())
        for sub_url in urls:
            # Note: Will override former "soup" variable contents (uml.edu/sitemap.xml). Not an issue though because we already got everything we needed from uml.edu/sitemap.xml.
            page = requests.get(sub_url) 

            # Parse using HTML
            soup = BeautifulSoup(page.content, "html.parser") 

            parsed_text = extract(soup)

            # parsed_csv = getTable(sub_url)

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
           
            bucket_name = getS3Address(os.getenv("KB_ID"))
            
            # Put parsed file into bucket
            #s3.put_object(Bucket=bucket_name, Key=filename_base, Body=parsed_text)

            # Put metadata file into bucket
            #s3.put_object(Bucket=bucket_name, Key=metadata_filename, Body=BytesIO(json_content))

           
            sitemap_file_to_create += (
    f"  <url>\n"
f"    <loc>{sub_url}</loc>\n"
    f"    <lastmod>{remote_tags[sub_url]}</lastmod>\n"
    f"  </url>\n"
)
           
           
            sleep(0.5)
    except KeyboardInterrupt:
            s3.put_object(Bucket=BUCKET, Key="sitemap.xml", Body=sitemap_file_to_create)
    s3.put_object(Bucket=BUCKET, Key="sitemap.xml", Body=sitemap_file_to_create)   # Executes at the end -- meaning, once every new or updated link page has been uploaded to the knowledge-base-connected s3 bucket.

def ingest_data(knowledge_base):
    client = boto3.client('bedrock-agent', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY, region_name='us-east-1')
    data_src_list = client.list_data_sources(knowledgeBaseId=knowledge_base, maxResults=123)['dataSourceSummaries']
    id = data_src_list[0]['dataSourceId']
    response = client.start_ingestion_job(
        dataSourceId=id,
        knowledgeBaseId=knowledge_base
    )

if __name__ == "__main__":
    main(["tuition"])
    ingest_data(os.getenv("KB_ID"))

