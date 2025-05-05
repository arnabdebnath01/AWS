import json
import boto3

def lambda_handler(event, context):
    print("Starting Lambda execution")
    
    # Initialize boto3 EC2 client
    ec2_client = boto3.client('ec2')
    print("Initialized EC2 client")
    
    # Get instance ID and name from event payload
    instance_id = event.get('instance_id')
    instance_name = event.get('instance_name', 'unnamed-instance')
    print(f"Received instance_id: {instance_id}, instance_name: {instance_name}")
    
    if not instance_id:
        print("Error: instance_id is required")
        return {
            'statusCode': 400,
            'body': json.dumps('Error: instance_id is required')
        }
    
    try:
        # Verify instance exists
        print(f"Describing instance: {instance_id}")
        response = ec2_client.describe_instances(
            InstanceIds=[instance_id]
        )
        
        if not response['Reservations']:
            print(f"Error: Instance {instance_id} not found")
            return {
                'statusCode': 404,
                'body': json.dumps(f'Error: Instance {instance_id} not found')
            }
        
        # Create AMI from the EC2 instance
        ami_name = f'AMI-from-{instance_name}-{context.aws_request_id}'
        print(f"Creating AMI with name: {ami_name}")
        response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            Description=f'AMI created from instance {instance_id} ({instance_name})',
            NoReboot=True
        )
        
        # Get the AMI ID
        ami_id = response['ImageId']
        print(f"AMI created with ID: {ami_id}")
        
        # Add tags to the AMI
        print(f"Adding tags to AMI: {ami_id}")
        ec2_client.create_tags(
            Resources=[ami_id],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': ami_name
                },
                {
                    'Key': 'SourceInstanceId',
                    'Value': instance_id
                },
                {
                    'Key': 'SourceInstanceName',
                    'Value': instance_name
                },
                {
                    'Key': 'CreatedBy',
                    'Value': 'Lambda'
                }
            ]
        )
        
        print("AMI creation and tagging completed")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'AMI creation started successfully',
                'ami_id': ami_id,
                'instance_id': instance_id,
                'instance_name': instance_name
            })
        }
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error creating AMI: {str(e)}')
        }
