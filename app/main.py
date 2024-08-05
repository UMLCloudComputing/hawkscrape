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

print(BUCKET)

def url_to_filename(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    path = parsed_url.path
    safe_path = re.sub(r'[^a-zA-Z0-9\-_\.]', '', path.replace('/', '_'))
    filename = f"{netloc}_{safe_path}".strip("_")
    filename = (filename[:252] + '...') if len(filename) > 255 else filename
    return filename

def extract_tags(soup, pattern):
    print("Extracting tags")
    tags_dict = {}
    loc_text = None

    for element in soup.find_all(['loc', 'lastmod']):
        if element.name == 'loc' and pattern.search(element.get_text()):
            loc_text = element.get_text()
        elif element.name == 'lastmod' and loc_text:
            tags_dict[loc_text] = element.get_text()
            loc_text = None

    print("Tags extracted and dictionary created")
    return tags_dict

def main(substrings: list) -> None: 
    
    s3 = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ID"), aws_secret_access_key=os.getenv("AWS_KEY"), region_name='us-east-1')
    
    try:
        sitemap = s3.get_object(Bucket=BUCKET, Key="sitemap.xml")['Body'].read()
        local_soup = BeautifulSoup(sitemap, features="lxml")
        s3_tags = extract_tags(local_soup, re.compile('|'.join(substrings)))

        origin_url = 'https://www.uml.edu/sitemap.xml' 

        page = requests.get(origin_url)

        print("Successfully downloaded webpage")

        remote_soup = BeautifulSoup(page.content, features = "lxml")

        print("Finished parsing with BeautifulSoup.")
        remote_tags = extract_tags(remote_soup, re.compile('|'.join(substrings)))

        urls = {
            url: remote_tags[url] 
            for url in remote_tags 
            if url not in s3_tags or remote_tags[url] != s3_tags[url]
        }

    except Exception as e:
        s3.put_object(Bucket=BUCKET, Key="sitemap.xml", Body=BytesIO(requests.get('https://www.uml.edu/sitemap.xml').content))
        origin_url = 'https://www.uml.edu/sitemap.xml' 

        # Call get method to request that page
        page = requests.get(origin_url)

        # Parse using XML 
        soup = BeautifulSoup(page.content, features = "xml")

        # Compile a regular expression pattern to match any of the substrings. Read more about RegEx expressions if interested.
        pattern = re.compile('|'.join(substrings))

        # Find all <loc> tags that contain any of the substrings using the compiled pattern 
        filtered_loc_tags = soup.find_all('loc', string=pattern)

        urls = [sub_url.get_text() for sub_url in filtered_loc_tags]

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
        s3 = boto3.client('s3', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
        bucket_name = getS3Address(os.getenv("KB_ID"))

        # Put parsed file into bucket
        s3.put_object(Bucket=bucket_name, Key=filename_base, Body=parsed_text)

        # Put metadata file into bucket
        s3.put_object(Bucket=bucket_name, Key=metadata_filename, Body=BytesIO(json_content))

        # for index, csv_content in enumerate(parsed_csv):
        #     csv_filename = f"{url_to_filename(sub_url)}_{index}.csv"
        #     s3.put_object(Bucket=bucket_name, Key=csv_filename, Body=BytesIO(csv_content.encode('utf-8')))
        #     s3.put_object(Bucket=bucket_name, Key=f"{csv_filename}.metadata.json", Body=BytesIO(json_content))

        # Wait a bit before it requests the next URL in the loop
        print(f"Finished processing {sub_url}")
        sleep(0.5)
    s3.put_object(Bucket=BUCKET, Key="sitemap.xml", Body=BytesIO(requests.get('https://www.uml.edu/sitemap.xml').content))

def ingest_data(knowledge_base):
    client = boto3.client('bedrock-agent', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY, region_name='us-east-1')
    data_src_list = client.list_data_sources(knowledgeBaseId=knowledge_base, maxResults=123)['dataSourceSummaries']
    id = data_src_list[0]['dataSourceId']
    response = client.start_ingestion_job(
        dataSourceId=id,
        knowledgeBaseId=knowledge_base
    )

if __name__ == "__main__":
    main(["/thesolutioncenter/", "/catalog/undergraduate"])
    ingest_data(os.getenv("KB_ID"))

