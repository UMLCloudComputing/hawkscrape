import boto3
import os
import re
from dotenv import load_dotenv
load_dotenv()

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def getS3Address(kbID: str) -> str:
    s3 = boto3.client('s3', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    kb = boto3.client('bedrock-agent', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

    data_src_list = kb.list_data_sources(knowledgeBaseId=kbID, maxResults=123)['dataSourceSummaries']
    id = data_src_list[0]['dataSourceId']

    s3_bucket_arn = kb.get_data_source(dataSourceId=id, knowledgeBaseId=kbID)['dataSource']['dataSourceConfiguration']['s3Configuration']['bucketArn']
    
    pattern = re.compile(r'arn:aws:s3:::(.*)')
    match = pattern.search(s3_bucket_arn)

    s3_bucket = match.group(1)
    return s3_bucket

if __name__ == "__main__":
    print(getS3Address(os.getenv("KB_ID")))