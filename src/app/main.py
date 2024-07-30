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

def ingest_data(knowledge_base):
    client = boto3.client('bedrock-agent', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    data_src_list = client.list_data_sources(knowledgeBaseId=knowledge_base, maxResults=123)['dataSourceSummaries']
    id = data_src_list[0]['dataSourceId']
    response = client.start_ingestion_job(
        dataSourceId=id,
        knowledgeBaseId=knowledge_base
    )

if __name__ == "__main__":
    main(["/thesolutioncenter/"])
    ingest_data(os.getenv("KB_ID"))

