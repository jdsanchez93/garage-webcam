import logging
import boto3
from botocore.exceptions import ClientError
import os
import sys
import cv2
from datetime import datetime
from zoneinfo import ZoneInfo
import json

def uploadFile(file_name, bucket, object_name):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name.
    :return: True if file was uploaded, else False
    """

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.put_object(Body=file_name, Bucket=bucket, Key=object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def receiveSqsMessage(bucketName, queueUrl):
    sqs_client = boto3.client('sqs', region_name="us-west-1")
    response = sqs_client.receive_message(
        QueueUrl=queueUrl
    )

    if "Messages" in response:
        message = json.loads(response['Messages'][0]['Body'])
        print(message)
        
        captureImage(bucketName, message)
        
        print("Deleting message from sqs")
        sqs_client.delete_message(
            QueueUrl=queueUrl,
            ReceiptHandle=response['Messages'][0]['ReceiptHandle'],
        )
    else:
        print("No messages in SQS")
        
def captureImage(bucketName, message):
    vid = cv2.VideoCapture(0)
    if "Brightness" in message:
        brightness = message['Brightness']
        if brightness is not None:
            print("Setting brightness")
            vid.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    # TODO fix this double call, which seems necessary for image quality
    ret, frame = vid.read()
    ret, frame = vid.read()
    
    if ret:
        imageId = message['ImageId']
        fileName = "{0}.png".format(imageId)
        
        encoded, buf = cv2.imencode('.png', frame)
        
        if encoded:
            print("Uploading " + fileName)
            uploadFile(buf.tobytes(), bucketName, fileName)
        else:
            print("Something went wrong encoding image...")

        vid.release()

        cv2.destroyAllWindows()
    else:
        print('Could not read video capture')


BUCKET_NAME = sys.argv[1]
QUEUE_URL = sys.argv[2]

while True:
    receiveSqsMessage(BUCKET_NAME, QUEUE_URL)
