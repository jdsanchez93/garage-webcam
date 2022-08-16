# garage-webcam

Usage

Build docker image with:
`docker build -t my-python-app .`

1. Add env-file.txt with environment variables for aws credentials:
```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

Run script with:
`sudo docker run -it --rm --mount type=bind,source="$(pwd)"/scripts,target=/usr/src/app -w /usr/src/app --env-file ./env-file.txt --device /dev/video0 -v /opt/vc:/opt/vc my-python-app python s3-upload.py my-bucket-name mySqsUrl`

To deploy the stack:
`sam deploy --guided --capabilities CAPABILITY_NAMED_IAM`