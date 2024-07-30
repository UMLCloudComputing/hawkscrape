from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
)
from constructs import Construct
from dotenv import load_dotenv
load_dotenv()
import os

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dockerFunc = _lambda.DockerImageFunction(
            scope=self,
            id=f"ID{construct_id}",
            function_name=construct_id,
            environment= {
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
