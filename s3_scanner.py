import boto3
import json
import os
import google.generativeai as genai
from botocore.exceptions import ClientError

# Configuration - It is safer to store the API key in environment variables
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def lambda_handler(event, context):
    """Scan S3 buckets for encryption and use AI to explain risks"""
    
    s3_client = boto3.client('s3')
    scan_results = []

    try:
        response = s3_client.list_buckets()
        buckets = response['Buckets']
    except ClientError as e:
        return {"error": str(e)}

    for bucket in buckets:
        bucket_name = bucket['Name']
        status = "Encrypted"
        
        try:
            # Check for server-side encryption configuration
            s3_client.get_bucket_encryption(Bucket=bucket_name)
        except ClientError as e:
            # If a 404 error is returned, encryption is not enabled
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                status = "Unencrypted"
            else:
                status = f"Error: {str(e)}"

        if status == "Unencrypted":
            # Use AI to generate a specific risk explanation
            prompt = f"Explain the security risk of an AWS S3 bucket named '{bucket_name}' not having server-side encryption enabled."
            ai_response = model.generate_content(prompt)
            risk_explanation = ai_response.text
        else:
            risk_explanation = "No immediate risk detected."

        scan_results.append({
            "bucket": bucket_name,
            "status": status,
            "risk_analysis": risk_explanation
        })

    return {
        "statusCode": 200,
        "body": json.dumps(scan_results)
    }