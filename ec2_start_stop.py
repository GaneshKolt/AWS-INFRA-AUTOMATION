import boto3
from collections import defaultdict

def lambda_handler(event, context):
    
    count = 0
    
    region = event['region']
    '''
    ec_2 = boto3.client('ec2')
    
    ec2_instance = ec_2.describe_instances(
        Filters = [
                {
                    'Name' : 'tag:ins',
                    'Values' : ['sch']
                }
            ]
        )
        
    print(ec2_instance)
        
    for reservation in ec2_instance['Reservations']:
        for instance in reservation['Instances']:
            id = [instance['InstanceId']]
            print(id)
            count+=1
    
    print(count)
    '''
    
    session = boto3.Session(region_name=region)

    ec2 = session.resource('ec2', region)
    
    instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}}])
    
    print(instances)
    
    for instance in instances:
        print(instance.id, instance.instance_type)
    
    
    '''
    a = []
    i = 1
    
    # Connect to EC2
    ec2 = boto3.resource('ec2')
    
    # Get information for all running instances
    running_instances = ec2.instances.filter(Filters=[{
        'Name': 'instance-state-name',
        'Values': ['stopped']}])
    
    ec2info = defaultdict()
    
    for instance in running_instances:
        for tag in instance.tags:
            if 'Name'in tag['Key']:
                name = tag['Value']
                a.append(name)
    a.sort() 
    '''
    #print('stopped')
    
