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
import json_log_formatter

formatter = json_log_formatter.VerboseJSONFormatter()

json_handler = logging.StreamHandler(stream=sys.stdout)
json_handler.setFormatter(formatter)

logger = logging.getLogger('my_json')
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

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
        logger.error(e)
        return False
    return True

def receiveSqsMessage(bucketName, queueUrl, queueRegion):
    sqs_client = boto3.client('sqs', region_name=queueRegion)
    response = sqs_client.receive_message(
        QueueUrl=queueUrl
    )

    if "Messages" in response:
        message = json.loads(response['Messages'][0]['Body'])
        logger.info(message)

        lightSettings = message.get('LightSettings')
        if lightSettings is not None:
            setSmartLight(SMART_LIGHT_API_URL, lightSettings)

        if "WebcamSettings" in message:
            captureImage(bucketName, message)
        
        logger.info("Deleting message from sqs")
        sqs_client.delete_message(
            QueueUrl=queueUrl,
            ReceiptHandle=response['Messages'][0]['ReceiptHandle'],
        )
    else:
        logger.debug("No messages in SQS")

cameraProperties = {
    "Brightness": cv2.CAP_PROP_BRIGHTNESS,
    "Contrast": cv2.CAP_PROP_CONTRAST
}

def setVideoCapturePropery(propName, settings, propId, vid):
    if propName in settings:
        x = settings[propName]
        if x is not None:
            logger.info("{}: {}".format(propName, x))
            vid.set(propId, x)
        
def captureImage(bucketName, message):
    vid = cv2.VideoCapture(0)

    settings = message['WebcamSettings']
    for prop in cameraProperties:
        setVideoCapturePropery(prop, settings, cameraProperties[prop], vid)
    if "printSettings" in settings and settings[printSettings] == True:
        printSettings()

    # TODO fix this double call, which seems necessary for image quality
    ret, frame = vid.read()
    ret, frame = vid.read()
    
    if ret:
        imageId = message['ImageId']
        fileName = "{0}.png".format(imageId)

        frame = cv2.flip(frame, 0)
        
        encoded, buf = cv2.imencode('.png', frame)
        
        if encoded:
            logger.info("Uploading " + fileName)
            uploadFile(buf.tobytes(), bucketName, fileName)
        else:
            logger.error("Something went wrong encoding image...")

        vid.release()

        cv2.destroyAllWindows()
    else:
        logger.error('Could not read video capture')

def printSettings():
    logger.info("\nAuto settings")
    logger.info("CAP_PROP_AUTO_EXPOSURE {}".format(vid.get(cv2.CAP_PROP_AUTO_EXPOSURE)))
    logger.info("CAP_PROP_AUTOFOCUS {}".format(vid.get(cv2.CAP_PROP_AUTOFOCUS)))
    logger.info("CAP_PROP_AUTO_WB {}".format(vid.get(cv2.CAP_PROP_AUTO_WB)))
    logger.info("\nManually set")
    logger.info("CAP_PROP_BRIGHTNESS {}".format(vid.get(cv2.CAP_PROP_BRIGHTNESS)))
    logger.info("CAP_PROP_CONTRAST {}".format(vid.get(cv2.CAP_PROP_CONTRAST)))
    logger.info("CAP_PROP_GAMMA {}".format(vid.get(cv2.CAP_PROP_GAMMA)))
    logger.info("CAP_PROP_SATURATION {}".format(vid.get(cv2.CAP_PROP_SATURATION)))
    logger.info("CAP_PROP_MODE {}".format(vid.get(cv2.CAP_PROP_MODE)))
    logger.info("CAP_PROP_SHARPNESS {}".format(vid.get(cv2.CAP_PROP_SHARPNESS)))


BUCKET_NAME = sys.argv[1]
QUEUE_URL = sys.argv[2]
SMART_LIGHT_API_URL=sys.argv[3]
QUEUE_REGION=sys.argv[4]

while True:
    receiveSqsMessage(BUCKET_NAME, QUEUE_URL, QUEUE_REGION)
