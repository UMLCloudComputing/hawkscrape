import boto3
import re
from dotenv import load_dotenv
import os
load_dotenv()


def delete_course_mds():
    AWS_ID = os.getenv("AWS_ID")
    AWS_KEY = os.getenv("AWS_KEY")

    # Initialize a session using Amazon S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY, region_name='us-east-1')

    # Define the bucket name
    bucket_name = ''

    # Define the regex pattern
    pattern = re.compile(r'.*_courses_.*\.md')

    # List objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name)

    # Check if the bucket contains any objects
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            # Check if the object key matches the regex pattern
            if pattern.match(key):
                print(f'Deleting {key}')
                s3.delete_object(Bucket=bucket_name, Key=key)
    else:
        print('No objects found in the bucket.')

    print('Deletion process completed.')

if __name__ == '__main__':
    delete_course_mds("SET_YOUR_BUCKET_NAME")
