import boto3, os
from dotenv import load_dotenv
load_dotenv('/home/ec2-user/sanjaya/.env')

c = boto3.client('bedrock',
    region_name='ap-south-2',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# List inference profiles
try:
    profiles = c.list_inference_profiles(maxResults=100)
    for m in profiles.get('inferenceProfileSummaries', []):
        pid = m.get('inferenceProfileId', '')
        pname = m.get('inferenceProfileName', '')
        if 'claude' in pid.lower() or 'anthropic' in pid.lower():
            print(f'  PROFILE: {pid}  -> {pname}')
except Exception as e:
    print(f'Profile listing error: {e}')

# List foundation models
try:
    models = c.list_foundation_models()
    for m in models.get('modelSummaries', []):
        mid = m.get('modelId', '')
        mname = m.get('modelName', '')
        if 'claude' in mid.lower() or 'claude' in mname.lower():
            print(f'  MODEL: {mid}  -> {mname}')
except Exception as e:
    print(f'Model listing error: {e}')
