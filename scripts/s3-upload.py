import logging
import boto3
from botocore.exceptions import ClientError
import os


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def receiveSqsMessage(queueUrl):
    sqs_client = boto3.client('sqs', region_name="us-west-1")
    response = sqs_client.receive_message(
        QueueUrl=queueUrl,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=0,
    )

    if "Messages" in response:
        
        # TODO capture image here

        sqs_client.delete_message(
            QueueUrl=queueUrl,
            ReceiptHandle=response['Messages'][0]['ReceiptHandle'],
        )
    else:
        print("No messages")


queueUrl = '.'
bucketName = "not-my-bucket"
#upload_file('sadge.jpg', bucketName)
receiveSqsMessage(queueUrl)