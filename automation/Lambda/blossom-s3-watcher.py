import json
import logging
import boto3
import time
import os
from pprint import pprint

### Ideally - these values should be in SecretManager, 
### but it would increase the budget for this RESEARCH project
S3_AKID = os.environ.get('S3_AKID_VALUE')
S3_SAK = os.environ.get('S3_SAK_VALUE')
EC2_ID = os.environ.get('EC2_INSTANCE_ID')
OUR_REGION = os.environ.get('BLOSSOM_REGION')
WORK_DIR = os.environ.get('WORK_DIR') # DIR ends with 'dir-name' !!! NO SLASH !!!
USER_DIR = os.environ.get('USER_DIR')
REPO_SSH = os.environ.get('REPO_SSH')
#------------------------------------------------
dGIT_PATH = os.environ.get('dGit_DIR') 


# Create client instance for S3 Bucket
s3_bucket='aws:s3:::b-blossom-nist-gate'
s3_client = boto3.client(
    's3',
    aws_access_key_id = S3_AKID,
    aws_secret_access_key = S3_SAK
    )
    

# Create client instance for EC2 Instance
# The EC2 Target ID: 'i-033da04a63408423f'
ec2_instances = [EC2_ID] # Array in case DHS wants to split their members to different EC2 instances
ec2_client = boto3.client('ec2', region_name=OUR_REGION)

# Create SSM Client
ssm_ec2_client = boto3.client('ssm')

def event_name_exists(event, context) -> bool:
    return ( # Shorthand for making sure that eventName is not a DUD
        event 
        and event['Records'] 
        and event['Records'][0] 
        and event['Records'][0]['eventName']
        )
        
def s3_file_as_dict(file_name:str, bucket_name:str ) -> dict:
    """ Parses the file content using ": " as separator 
        done as YAML package would eat much more time/memory
        and is a hustle to pull into the environment
    Args:
        file_name (str): File name in S3 bucket
        bucket_name (str): S3 bucket name
    Returns:
        dict: _description_
    """
    file_dict={}
    s3 = s3_client
    data = s3.get_object(Bucket=bucket_name, Key=file_name)
    if data:
        content =  data['Body'].read().decode('utf-8')
        lines = list(filter(None, content.split("\n", -1)))
        for line in lines:
            if line:
                p = line.split(': ')
                if len(p)==2:
                    file_dict[p[0]]=p[1]
    return file_dict
        
def run_ec2_commands(file_name:str='X.test', file_dict:dict={}):
    """ Run the commands on EC2 from Lambda
    Args:
        file_name (str, optional): The file-name of the new S3-file that triggered event. Defaults to 'X.test'.
        file_dict (str, optional): The dict of the file content. Defaults to {}.
    """
    print(f'Run-Test\n{"="*64}')
    ### Hand-parsed reference-file values
    branch_name = file_dict["branch_name"] if 'branch_name' in file_dict.keys() else ''
    cmd_file_name = file_dict["file"]  if 'file' in file_dict.keys() else ''

    cmd_process_s3_file = " ".join(
                    [   'python',f'{WORK_DIR}/ops_common.py',
                        'process-s3-file', 
                        '-e', f'{WORK_DIR}/env-ec2-test.yaml', 
                        '-s3', f'{file_name}'
                    ]
                )      
    client = ssm_ec2_client
    response = client.send_command(
      
        InstanceIds=ec2_instances,
        DocumentName='AWS-RunShellScript',
        Parameters={            
            'commands': [
                ### 1. Run the S3-Bucket Handler
                (f' runuser -l  ec2-user -c "{cmd_process_s3_file}"'),
            ],
            'workingDirectory': [WORK_DIR],
            # 'id': ['BloSS@M-Test'],
            ### !!! The script executes a long-running chunk of work !!! 
            ### !!! Be super-careful playing with the timeout value !!! 
            'executionTimeout':['99'] 
        }
    )
    command_id = response['Command']['CommandId']
    tries = 0
    output = 'False'
    Statuses=[]
    Contexts=[]
    while tries < 100:
        tries = tries + 1
        try:
            time.sleep(0.9)  # some delay always required...
            
            result = client.get_command_invocation(
                CommandId=command_id,
                InstanceId=ec2_instances[0] ,
            )
            # print(f"{result['Status']=}")
            # print(f"{result['StandardOutputContent']=}")
            Statuses.append(f"{result['Status']=}")
            Contexts.append(f"{result['StandardOutputContent']=}")
            if result['Status'] == 'InProgress':
                continue
            output = result['StandardOutputContent']
            break
        except client.exceptions.InvocationDoesNotExist:
            continue

    pprint(Statuses)
    pprint(Contexts)
    pprint(result)
    print('\n\n')
    print(f'{"="*64}')
    return(output, Statuses, Contexts)
    
def lambda_handler(event, context):       
    # CASE #1 - File(Object) Was Dropped Into the S3-Bucket 
    # Handle the Put/Post/COPY/Multipart-Upload-Complete. 
    # I.e. All ObjectCreated* Events:
    if (    event_name_exists(event, context)
            and event['Records'][0]['eventName'].startswith('ObjectCreated:')
    ):
        # Carve out the bucket and key
        bucket = event['Records'][0]['s3']['bucket']['name']
        file_name = event['Records'][0]['s3']['object']['key']
        print(f'{"*"*60}')
        file_content_dict = s3_file_as_dict(file_name, bucket)
        print(f'File Content={file_content_dict}')
        print(f'{"*"*60}')
        print(f'{bucket=}')
        print(f'{file_name=}')

        test_result = run_ec2_commands(file_name, file_content_dict)

        print(f'{"*"*60}')
        
        print('\n\tEvent=\n')
        pprint(event)
        print('\n\tContext=\n')
        pprint(context)
        
        response = None
        ## Get Object [Requires s3-Object Access-Rights]
        response = s3_client.get_object(Bucket = bucket, Key = file_name)
    
    
        ## Pull The Data
        data = response['Body'].read().decode('utf-8')
        print(data)
        ec2_client.start_instances(InstanceIds=ec2_instances)
        return 
        {
            'statusCode': 200,
            'body': json.dumps(f'\n\t{bucket=},\n\t{file_name=}\n\t{event}\n{response}')
        }
        
    # CASE #2 - - File(Object) Was DELETED from S3-Bucket     
    # Reacting to "eventName": "ObjectRemoved:Delete"
    elif (  event_name_exists(event, context)
            and event['Records'][0]['eventName'].startswith('ObjectCreated:')
        ):
        ec2_client.stop_instances(InstanceIds=ec2_instances)

    # This is a weirdly impossible case by the configuration, 
    # but we should log this "Loch-Ness Monster", just in case
    else:
        pass
    # TODO implement