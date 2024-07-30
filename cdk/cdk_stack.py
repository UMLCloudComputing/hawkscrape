from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3
)
from constructs import Construct
from dotenv import load_dotenv
load_dotenv()
import os

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self, 
            id=f"id{construct_id.lower()}", 
            bucket_name=f"xmlbucket{construct_id.lower()}" # Provide a bucket name here
        )

        dockerFunc = _lambda.DockerImageFunction(
            scope=self,
            id=f"ID{construct_id}",
            function_name=construct_id,
            environment= {
                "BUCKET" : bucket.bucket_name,
                "AWS_ID": os.getenv('AWS_ACCESS_KEY_ID'),
                "AWS_KEY": os.getenv('AWS_SECRET_ACCESS_KEY'),
                "KB_ID": os.getenv('KB_ID'),
            },            
            code=_lambda.DockerImageCode.from_image_asset(
                directory="src"
            ),
            timeout=Duration.seconds(900)
        )

        api = apigateway.LambdaRestApi(self, f"API{construct_id}",
            handler=dockerFunc,
            proxy=True,
        )

        
