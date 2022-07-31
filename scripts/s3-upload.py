import logging
import boto3
from botocore.exceptions import ClientError
import os
import sys
import cv2
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from smartlight import setSmartLight

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

        if "SmartLightSettings" in message:
            settings = message['SmartLightSettings']
            setSmartLight(SMART_LIGHT_API_URL, settings)

        if "WebcamSettings" in message:
            captureImage(bucketName, message)
        
        print("Deleting message from sqs")
        sqs_client.delete_message(
            QueueUrl=queueUrl,
            ReceiptHandle=response['Messages'][0]['ReceiptHandle'],
        )
    else:
        print("No messages in SQS")

cameraProperties = {
    "Brightness": cv2.CAP_PROP_BRIGHTNESS,
    "Contrast": cv2.CAP_PROP_CONTRAST
}

def setVideoCapturePropery(propName, settings, propId, vid):
    if propName in settings:
        x = settings[propName]
        if x is not None:
            print(propName, x)
            vid.set(propId, x)
        
def captureImage(bucketName, message):
    vid = cv2.VideoCapture(0)

    settings = message['WebcamSettings']
    for prop in cameraProperties:
        setVideoCapturePropery(prop, settings, cameraProperties[prop], vid)
    if "printSettings" and settings[printSettings] == True in settings:
        printSettings()

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

def printSettings():
    print("\nAuto settings")
    print("CAP_PROP_AUTO_EXPOSURE", vid.get(cv2.CAP_PROP_AUTO_EXPOSURE))
    print("CAP_PROP_AUTOFOCUS", vid.get(cv2.CAP_PROP_AUTOFOCUS))
    print("CAP_PROP_AUTO_WB", vid.get(cv2.CAP_PROP_AUTO_WB))
    print("\nManually set")
    print("CAP_PROP_BRIGHTNESS", vid.get(cv2.CAP_PROP_BRIGHTNESS))
    print("CAP_PROP_CONTRAST", vid.get(cv2.CAP_PROP_CONTRAST))
    print("CAP_PROP_GAMMA", vid.get(cv2.CAP_PROP_GAMMA))
    print("CAP_PROP_SATURATION", vid.get(cv2.CAP_PROP_SATURATION))
    print("CAP_PROP_MODE", vid.get(cv2.CAP_PROP_MODE))
    print("CAP_PROP_SHARPNESS", vid.get(cv2.CAP_PROP_SHARPNESS))


BUCKET_NAME = sys.argv[1]
QUEUE_URL = sys.argv[2]
SMART_LIGHT_API_URL=sys.argv[3]

while True:
    receiveSqsMessage(BUCKET_NAME, QUEUE_URL)
