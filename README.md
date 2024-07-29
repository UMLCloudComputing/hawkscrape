# rowdybot-scraper
RowdyBot's Data Collector

# Setup Instructions
In order to setup ingestion of data into a knowledge base, you will need to create a `.env` file in the root directory of the project. The `.env` file should contain the following variables:
```
AWS_ACCESS_KEY_ID =
AWS_SECRET_ACCESS_KEY =
KB_ID =
```
You can run the file with `python3 main.py`. The program will automatically upload results to the S3 Bucket connected to the knowledge base, then sync the connected knowledge base. To see the logic for determining the connected S3 Bucket, view the s3.py file.

# Installation
`pip install -r requirements.txt`
