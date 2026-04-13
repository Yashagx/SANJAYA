import boto3, json, os, sys
from dotenv import load_dotenv
load_dotenv('/home/ec2-user/sanjaya/.env')

bedrock = boto3.client('bedrock-runtime', region_name='ap-south-2')

# Try each available model
models_to_try = [
    "apac.anthropic.claude-sonnet-4-20250514-v1:0",
    "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "apac.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "anthropic.claude-sonnet-4-6",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
]

body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 50,
    "system": "Reply with just 'OK'",
    "messages": [{"role": "user", "content": "Hello"}]
})

for model in models_to_try:
    try:
        response = bedrock.invoke_model(
            modelId=model, body=body,
            contentType='application/json', accept='application/json'
        )
        result = json.loads(response['body'].read())
        text = result['content'][0]['text']
        print(f"SUCCESS: {model} -> {text[:50]}")
        break
    except Exception as e:
        err = str(e)[:120]
        print(f"FAILED:  {model} -> {err}")
