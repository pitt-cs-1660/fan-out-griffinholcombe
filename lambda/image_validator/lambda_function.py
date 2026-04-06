import json
import os
import boto3

s3 = None

VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']

def is_valid_image(key):
    """check if the file has a valid image extension."""
    _, ext = os.path.splitext(key.lower())
    return ext in VALID_EXTENSIONS

def lambda_handler(event, context):
    """
    validates that uploaded files are images.
    raises exception for invalid files (triggers DLQ).

    for valid files, copies the object to the processed/valid/ prefix
    in the same bucket so grading can verify output via S3.

    event structure (SNS wraps the S3 event):
    {
        "Records": [{
            "Sns": {
                "Message": "{\"Records\":[{\"s3\":{...}}]}"  # this is a JSON string!
            }
        }]
    }

    required log format:
        [VALID] {key} is a valid image file
        [INVALID] {key} is not a valid image type

    required S3 output (valid files only):
        copies the file to processed/valid/{filename}
        e.g. uploads/test.jpg -> processed/valid/test.jpg

    important: to trigger the DLQ, you must raise an exception (not return an error).
    """

    global s3
    if s3 is None:
        s3 = boto3.client('s3')
    
    print("=== image validator invoked ===")

    for record in event['Records']:
        sns_message = record['Sns']['Message']
        s3_event = json.loads(sns_message)
        for s3_record in s3_event['Records']:
            bucket = s3_record['s3']['bucket']['name']
            
            key = s3_record['s3']['object']['key']
            
            if is_valid_image(key):
                print(f"[VALID] {key} is a valid image file")
                
                filename = key.split('/')[-1]
                
                s3.copy_object(
                    Bucket=bucket,
                    Key=f"processed/valid/{filename}",
                    CopySource={'Bucket': bucket, 'Key': key}
                )
            else:
                print(f"[INVALID] {key} is not a valid image type")
                raise ValueError(f"{key} is not a valid image type")

    return {'statusCode': 200, 'body': 'validation complete'}
