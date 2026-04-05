import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    extracts metadata from S3 upload events received via SNS.
    logs file information to CloudWatch and writes a JSON metadata
    file to the processed/metadata/ prefix in the same bucket.

    event structure (SNS wraps the S3 event):
    {
        "Records": [{
            "Sns": {
                "Message": "{\"Records\":[{\"s3\":{...}}]}"  # this is a JSON string!
            }
        }]
    }

    required log format:
        [METADATA] File: {key}
        [METADATA] Bucket: {bucket}
        [METADATA] Size: {size} bytes
        [METADATA] Upload Time: {timestamp}

    required S3 output:
        writes a JSON file to processed/metadata/{filename}.json containing:
        {
            "file": "{key}",
            "bucket": "{bucket}",
            "size": {size},
            "upload_time": "{timestamp}"
        }
    """

    print("=== metadata extractor invoked ===")

    for record in event['Records']:
        sns_message = record['Sns']['Message']
        s3_event = json.loads(sns_message)
    
        for s3_record in s3_event['Records']:
            bucket = s3_record['s3']['bucket']['name']
            key = s3_record['s3']['object']['key']
            size = s3_record['s3']['object']['size']
            event_time = s3_record['eventTime']
            print(f"[METADATA] File: {key}")
            print(f"[METADATA] Bucket: {bucket}")
            print(f"[METADATA] Size: {size} bytes")
            print(f"[METADATA] Upload Time: {event_time}")
            
            metadata = {
                "file": key,
                "bucket": bucket,
                "size": size,
                "upload_time": event_time
            }
            
            filename = os.path.splitext(key.split('/')[-1])[0]
            
            s3.put_object(
                Bucket=bucket,
                Key=f"processed/metadata/{filename}.json",
                Body=json.dumps(metadata),
                ContentType='application/json'
            )

    return {'statusCode': 200, 'body': 'metadata extracted'}
