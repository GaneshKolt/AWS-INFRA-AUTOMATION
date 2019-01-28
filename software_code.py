import json
import boto3
import csv
import email
import base64
import copy

def lambda_handler(event, context):
    
    print(event)
    
    #GLOBAL VARIABLE DECLARATIONS
    
    global LinuxServer
    LinuxServer = {
                  "LinuxServerInstance": {
                  "Type": "AWS::EC2::Instance",
                  "DependsOn" : "",
                  "Properties" : {
                    "InstanceType": "",
                    "ImageId": { "Fn::FindInMap" : [ "Linux2ImageId", { "Ref" : "AWS::Region" }, ""]},
                    "NetworkInterfaces" : [{
                      "GroupSet"                 : [{"Ref": "InstanceSecurityGroup"}],
                      "AssociatePublicIpAddress" : "true",
                      "DeviceIndex"              : "0",
                      "DeleteOnTermination"      : "true",
                      "SubnetId"                 : {"Ref": ""}
                    }],
                    "KeyName": "new",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "VolumeSize": "",
                                "VolumeType": ""
                            }
                        }
                    ],
                    "Tags": [
                        {
                            "Key": "inframind",
                            "Value": "Scheduled"
                        },
                        {
                            "Key" : "Name",
                            "Value" : ""
                        }
                    ]
                  }
                }
            }
    
    global windowsServer
    windowsServer = {
                  "WindowsServerInstance": {
                  "Type": "AWS::EC2::Instance",
                  "DependsOn" : "",
                  "Properties": {
                    "InstanceType": "",
                    "ImageId": { "Fn::FindInMap" : [ "Linux2ImageId", { "Ref" : "AWS::Region" }, ""]},
                    "NetworkInterfaces" : [{
                      "GroupSet"                 : [{"Ref": "InstanceSecurityGroup"}],
                      "AssociatePublicIpAddress" : "true",
                      "DeviceIndex"              : "0",
                      "DeleteOnTermination"      : "true",
                      "SubnetId"                 : {"Ref": ""}
                    }],
                    "KeyName": "infra1",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "VolumeSize": "",
                                "VolumeType": ""
                            }
                        }
                    ],
                    "Tags": [
                        {
                            "Key": "inframind",
                            "Value": "Scheduled"
                        },
                        {
                            "Key" : "Name",
                            "Value" : "Windows Server"
                        }
                    ]
                  }
                }
            }
    
    global linchrome
    linchrome = {
              "UserData": {
                "Fn::Base64": {
                  "Fn::Join": [
                    "\n",
                    [
                      "#!/bin/bash",
                      "wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
                      "sudo dpkg -i google-chrome-stable_current_amd64.deb",
                      "sudo apt-get update"
                    ]
                  ]
                }
              }
            }
            
    global linfirefox
    linfirefox = {
              "UserData": {
                "Fn::Base64": {
                  "Fn::Join": [
                    "\n",
                    [
                      "#!/bin/bash",
                      "sudo apt install firefox",
                      "sudo apt-get update"
                    ]
                  ]
                }
              }
            }
            
    global linopera
    linopera = linfirefox = {
              "UserData": {
                "Fn::Base64": {
                  "Fn::Join": [
                    "\n",
                    [
                      "#!/bin/bash",
                      "wget -qO- https://deb.opera.com/archive.key | sudo apt-key add -",
                      "sudo add-apt-repository deb [arch=i386,amd64] https://deb.opera.com/opera-stable/ stable non-free",
                      "sudo apt-get update",
                      "sudo apt-get install -y opera-stable",
                      "sudo apt-get update"
                    ]
                  ]
                }
              }
            }
            
    global publicsubnet
    publicsubnet = {
                    "PublicSubnet": {
                      "Type": "AWS::EC2::Subnet",
                      "Properties": {
                        "VpcId": {
                          "Ref": "VPC"
                        },
                        "Tags": [
                          {
                            "Key": "Name",
                            "Value": ""
                          }
                        ],
                        "CidrBlock": ""
                      }
                    }
                  }
    
    global publicroutetableassociation
    publicroutetableassociation = {
                                    "PublicSubnetRouteTableAssociation": {
                                      "Type": "AWS::EC2::SubnetRouteTableAssociation",
                                      "Properties": {
                                        "SubnetId": {
                                          "Ref": ""
                                        },
                                        "RouteTableId": {
                                          "Ref": "PublicRouteTable"
                                        }
                                      }
                                    }
                                }
            
    global publicsubnetnetworkacl
    publicsubnetnetworkacl = {
                                "PublicSubnetNetworkAclAssociation": {
                                  "Type": "AWS::EC2::SubnetNetworkAclAssociation",
                                  "Properties": {
                                    "SubnetId": {
                                      "Ref": ""
                                    },
                                    "NetworkAclId": {
                                      "Fn::GetAtt": [
                                        "VPC",
                                        "DefaultNetworkAcl"
                                      ]
                                    }
                                  }
                                }
                            }
    global cpualaram
    cpualaram = {
                  "CPUAlarm": {
                  "Type": "AWS::CloudWatch::Alarm",
                  "Properties": {
                    "AlarmActions": [
                      {
                        "Ref": "SNS"
                      }
                    ],
                    "MetricName": "CPUUtilization",
                    "Namespace": "AWS/EC2",
                    "Statistic": "Average",
                    "Period": "300",
                    "EvaluationPeriods": "2",
                    "Threshold": "80",
                    "ComparisonOperator": "GreaterThanOrEqualToThreshold",
                    "Dimensions": [
                      {
                        "Name": "InstanceId",
                        "Value": {
                          "Ref": "LinuxServerInstance"
                        }
                      }
                    ]
                  }
                }
            }
    
    #Getting client and resource
  
    s3 = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    cf = boto3.client('cloudformation')
    
    #getting bucket and key
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(bucket)
    print(key)
    
    #Reading the JSon Template 
    template = s3_resource.Object('infra-mail', 'template.json')
    file_content = template.get()['Body'].read().decode('utf-8')
    Master_template = json.loads(file_content)
    
    #Assign master template
    stack_template = Master_template
    
    #Reading email content
    file = s3.get_object(Bucket=bucket, Key=key)
    email_content = email.message_from_string(file['Body'].read().decode('utf-8'))
    attachment = base64.b64decode(email_content.get_payload()[1].get_payload()).decode('utf-8')
    lines = []
    
    for line in attachment.split('\r\n'):
        lines.append(line.split(','))
        
    #Variables for logic
    count = 0
    i = 1
    lin_server = {}
    win_server = {}
    public_subnet = {}
    public_route_table_association = {}
    public_network_acl = {}
    cloud_watch_alaram = {}
    
    for row in lines:
      
        if len(row) > 1:
            
            if count == 0:
                count += 1
                continue
        
            if row[0].lower() == 'linux':
                lin_server['LinuxServerInstance'+str(i)] = copy.deepcopy(LinuxServer['LinuxServerInstance'])
                lin_server['LinuxServerInstance'+str(i)]['Properties']['InstanceType'] = row[1]
                lin_server['LinuxServerInstance'+str(i)]['Properties']['ImageId']['Fn::FindInMap'][2] = row[0]
                lin_server['LinuxServerInstance'+str(i)]['Properties']['BlockDeviceMappings'][0]['Ebs']['VolumeSize'] = row[2]
                lin_server['LinuxServerInstance'+str(i)]['Properties']['BlockDeviceMappings'][0]['Ebs']['VolumeType'] = row[3]
                lin_server['LinuxServerInstance'+str(i)]['Properties']['Tags'][1]['Value'] = 'Linux Server'+str(i)
                lin_server['LinuxServerInstance'+str(i)]['Properties']['NetworkInterfaces'][0]['SubnetId']['Ref'] = 'publicsubnet'+str(i)
                lin_server['LinuxServerInstance'+str(i)]['DependsOn'] = 'publicsubnet' + str(i)
                lin_server['LinuxServerInstance'+str(i)]['Properties'].update(linchrome)
                
                
                #Cloud Watch Alaram
                cloud_watch_alaram['CPUAlarm'+str(i)] =copy.deepcopy(cpualaram['CPUAlarm'])
                cloud_watch_alaram['CPUAlarm'+str(i)]['Properties']['Dimensions'][0]['Value']['Ref'] = 'LinuxServerInstance'+str(i)
                
                #Public subnet
                public_subnet['publicsubnet'+str(i)] =copy.deepcopy(publicsubnet['PublicSubnet'])
                public_subnet['publicsubnet'+str(i)]['Properties']['CidrBlock'] = row[11]
                public_subnet['publicsubnet'+str(i)]['Properties']['Tags'][0]['Value'] = 'public subnet' + str(i)
                
                #Public route table assciation
                public_route_table_association['publicroutetableassociation'+str(i)] = copy.deepcopy(publicroutetableassociation['PublicSubnetRouteTableAssociation'])
                public_route_table_association['publicroutetableassociation'+str(i)]['Properties']['SubnetId']['Ref'] = 'publicsubnet'+str(i)
               
                #public network acl
                public_network_acl['publicsubnetnetworkacl'+str(i)] = copy.deepcopy(publicsubnetnetworkacl['PublicSubnetNetworkAclAssociation'])
                public_network_acl['publicsubnetnetworkacl'+str(i)]['Properties']['SubnetId']['Ref'] = 'publicsubnet'+str(i)
            
                #Add Resources to stack template
                stack_template['Resources'].update(lin_server)
                stack_template['Resources'].update(public_subnet)
                stack_template['Resources'].update(public_route_table_association)
                stack_template['Resources'].update(public_network_acl)
                stack_template['Resources'].update(cloud_watch_alaram)
    
            i = i + 1
            
            
            #VPC Configuration
            stack_template['Resources']['VPC']['Properties']['CidrBlock'] = row[10]
            
            stack_template['Resources']['InstanceSecurityGroup']['Properties']['SecurityGroupIngress'][4]['FromPort'] = '-1'
            stack_template['Resources']['InstanceSecurityGroup']['Properties']['SecurityGroupIngress'][4]['ToPort'] = '-1'
    
    #Uploading template to s3 bucket        
    obj = s3_resource.Object('inframindsolution','inframindsolution.json')
    obj.put(Body=json.dumps(stack_template))
    a = json.dumps(stack_template)
    #Pushing template into cloudformation template
    try:
        stack = cf.create_stack(StackName='InframindSolution',TemplateURL= 'https://s3-us-west-2.amazonaws.com/inframindsolution/inframindsolution.json')
    except Exception as e:
        print(e)
    
    #printing the template   
    print(stack_template)
    print('success')
