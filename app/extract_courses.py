import json
import requests
import re
import boto3
import os
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()

CHUNK_SIZE = 10

DEPARTMENT_PREFIXES = [
    "ACCT",
    "AERO",
    "AEST",
    "AMHE",
    "AMST",
    "ARCH",
    "ARHI",
    "ARTS",
    "ASAM",
    "ATMO",
    "BIOL",
    "BMBT",
    "BMEN",
    "BMSC",
    "BOST",
    "BUSI",
    "CHEM",
    "CHEN",
    "CIVE",
    "COMP",
    "CONT",
    "CORE",
    "CRIM",
    "DART",
    "DGMD",
    "DPTH",
    "ECON",
    "EDUC",
    "EECE",
    "ENGL",
    "ENGN",
    "ENGY",
    "ENTR",
    "ENVE",
    "ENVI",
    "ENVS",
    "ETEC",
    "EXER",
    "FAHS",
    "FINA",
    "GEOL",
    "GLST",
    "GNDR",
    "GRFX",
    "HIST",
    "HONR",
    "HSCI",
    "IENG",
    "IM",
    "INFO",
    "LABR",
    "LGST",
    "LIFE",
    "LMUCM",
    "MARI",
    "MATH",
    "MECH",
    "MGMT",
    "MIST",
    "MKTG",
    "MLSC",
    "MPAD",
    "MSIT",
    "MTEC",
    "MUAP",
    "MUBU",
    "MUCM",
    "MUED",
    "MUEN",
    "MUHI",
    "MUPF",
    "MUSR",
    "MUTH",
    "NONC",
    "NURS",
    "NUTR",
    "PCST",
    "PHIL",
    "PHRM",
    "PHYS",
    "PLAS",
    "POLI",
    "POLY",
    "POMS",
    "PSMA",
    "PSYC",
    "PTEC",
    "PUBH",
    "RADI",
    "ROTC",
    "SCIE",
    "SOCI",
    "THEA",
    "UGTC",
    "UMLO",
    "UNCR",
    "UTCH",
    "WLAN",
    "WLAR",
    "WLCH",
    "WLFR",
    "WLGE",
    "WLIT",
    "WLKH",
    "WLLA",
    "WLPO",
    "WLSP",
    "WORC",
]

AWS_ID = os.getenv("AWS_ID")
AWS_KEY = os.getenv("AWS_KEY")

def getS3Address(kbID: str) -> str:
    s3 = boto3.client('s3', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY, region_name='us-east-1')
    kb = boto3.client('bedrock-agent', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY, region_name='us-east-1')

    data_src_list = kb.list_data_sources(knowledgeBaseId=kbID, maxResults=123)['dataSourceSummaries']
    id = data_src_list[0]['dataSourceId']

    s3_bucket_arn = kb.get_data_source(dataSourceId=id, knowledgeBaseId=kbID)['dataSource']['dataSourceConfiguration']['s3Configuration']['bucketArn']
    
    pattern = re.compile(r'arn:aws:s3:::(.*)')
    match = pattern.search(s3_bucket_arn)

    s3_bucket = match.group(1)
    return s3_bucket

# Function to convert JSON to Markdown
def json_to_markdown(course):
    title = course["Title"]
    title = re.sub(r'\s*\(Formerly.*?\)', '', title)
    course_id = course["Department"] + "." + course["CatalogNumber"]
    description = course["Description"]
    credits = course["UnitsMinimum"]
    career = course["AcademicCareer"]["Description"]

    markdown = f"# {title} (course ID: {course_id})\n\n"
    markdown += f"## Description:\n{description}\n\n"
    markdown += f"## Credits: {credits}\n\n"
    markdown += f"## This is an {career.lower()} course\n"

    return markdown

def catch():
    s3 = boto3.client('s3', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    bucket_name = getS3Address(os.getenv("KB_ID"))

    for prefix in DEPARTMENT_PREFIXES:
        result = requests.get(f"https://www.uml.edu/api/registrar/course_catalog/v1.0/courses?field=subject&query={prefix}")
        courses = result.json()
        
        
        for i in range(0, len(courses), CHUNK_SIZE):
            chunk = courses[i:i + CHUNK_SIZE]
            markdown_output = ""
            for course in chunk:
                # Json to markdown
                markdown_output += json_to_markdown(course)
                markdown_output += "\n\n"
            
            # Write to file
            chunk_number = i // CHUNK_SIZE + 1

            filename_base = f"{prefix}_courses_{chunk_number}.md"
            s3.put_object(Bucket=bucket_name, Key=filename_base, Body=markdown_output)

            # Metadata dictionary
            metadata = {
                "metadataAttributes": {
                    "url": f"https://www.uml.edu/Catalog/Advanced-Search.aspx?prefix={prefix}&type=prefix"
                }
            }
            
            # Write metadata to file
            metadata_filename = f"{prefix}_courses_{chunk_number}.md.metadata.json"
            json_content = json.dumps(metadata).encode('utf-8')
            s3.put_object(Bucket=bucket_name, Key=metadata_filename, Body=BytesIO(json_content))

            print(f"Finished processing {prefix} chunk {chunk_number}")

if __name__ == "__main__":
    catch()