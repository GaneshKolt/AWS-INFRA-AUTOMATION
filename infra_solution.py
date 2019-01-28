import boto3,csv
import json
import email
import base64
def lambda_handler(event, context):
    
    
    ##Declarations
    
    global WinServer
    WinServer = {
                "WinInstance": {
                "Type": "AWS::EC2::Instance",
                "Metadata": {
                    "AWS::CloudFormation::Init": {
                        "config": {
                            "commands": {
                                "1_install_roles": {
                                    "command": {
                                        "Fn::Sub": "powershell.exe -ExecutionPolicy Unrestricted Install-WindowsFeature -Name Web-Server -IncludeAllSubFeature -IncludeManagementTool"
                                    }
                                },
                                "2_install_features": {
                                    "command": {
                                        "Fn::Sub": "powershell.exe -ExecutionPolicy Unrestricted Install-WindowsFeature Telnet-Client"
                                    }
                                },
                                "3_restart": {
                                    "command": "powershell.exe Restart-Computer",
                                    "waitAfterCompletion": "forever"
                                }
                            }
                        },
                        "files": {
                            "c:\\cfn\\cfn-hup.conf": {
                                "content": {
                                    "Fn::Join": [
                                        "",
                                        [
                                            "[main] ",
                                            "stack=",
                                            {
                                                "Ref": "AWS::StackId"
                                            },
                                            " ",
                                            "region=",
                                            {
                                                "Ref": "AWS::Region"
                                            },
                                            " "
                                        ]
                                    ]
                                }
                            },
                            "c:\\cfn\\hooks.d\\cfn-auto-reloader.conf": {
                                "content": {
                                    "Fn::Join": [
                                        "",
                                        [
                                            "[cfn-auto-reloader-hook] ",
                                            "triggers=post.update ",
                                            "path=Resources.WinInstance1.Metadata.AWS::CloudFormation::Init ",
                                            "action=cfn-init.exe -v -s ",
                                            {
                                                "Ref": "AWS::StackId"
                                            },
                                            " -r WinInstance1",
                                            " --region ",
                                            {
                                                "Ref": "AWS::Region"
                                            },
                                            " "
                                        ]
                                    ]
                                }
                            },
                            "services": {
                                "windows": {
                                    "fn-hup": {
                                        "enabled": "true",
                                        "ensureRunning": "true",
                                        "files": [
                                            "c:\\cfn\\cfn-hup.conf",
                                            "c:\\etc\\cfn\\hooks.d\\cfn-auto-reloader.conf"
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                "Properties": {
                    "ImageId": {
                        "Fn::FindInMap": [
                            "Linux2ImageId",
                            {
                                "Ref": "AWS::Region"
                            },
                            ""
                        ]
                    },
                    "InstanceType": "",
                    "SubnetId": {
                        "Ref": "PublicSubnet"
                    },
                    "SecurityGroupIds": [
                        {
                            "Ref": "InstanceSecurityGroup"
                        }
                    ],
                    "KeyName": "infra1",
                    "Tags": [
                        {
                            "Key": "instanceStartStop",
                            "Value": "Scheduled"
                        }
                    ],
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "VolumeSize": "",
                                "VolumeType": ""
                            }
                        }
                    ],
                    "UserData": {
                        "Fn::Base64": {
                            "Fn::Join": [
                                "",
                                [
                                    "<script>\n",
                                    "cfn-init.exe -v -s ",
                                    {
                                        "Ref": "AWS::StackId"
                                    },
                                    " -r WinInstance1",
                                    " --region ",
                                    {
                                        "Ref": "AWS::Region"
                                    },
                                    "\n",
                                    "</script>"
                                ]
                            ]
                        }
                    }
                }
            }
          }
    
    global LinuxServer
    LinuxServer = {
                  "LinuxServerInstance": {
                  "Type": "AWS::EC2::Instance",
                  "Properties": {
                    "InstanceType": "",
                    "ImageId": { "Fn::FindInMap" : [ "Linux2ImageId", { "Ref" : "AWS::Region" }, ""]},
                    "NetworkInterfaces" : [{
                      "GroupSet"                 : [{"Ref": "InstanceSecurityGroup"}],
                      "AssociatePublicIpAddress" : "true",
                      "DeviceIndex"              : "0",
                      "DeleteOnTermination"      : "true",
                      "SubnetId"                 : {"Ref": "PublicSubnet"}
                    }],
                    "KeyName": "infra1",
                    "BlockDeviceMappings": [
                      {
                        "DeviceName": "/dev/xvda",
                        "Ebs": {
                          "VolumeSize": "",
                          "VolumeType": "gp2"
                        }
                      }
                    ],
                    "UserData": {
                      "Fn::Base64": {
                        "Fn::Join": [
                          "\n",
                          [
                            "#!/bin/bash -xe",
                            "sudo yum update -y",
                            "sudo yum install httpd -y",
                            "sudo /etc/init.d/httpd start",
                            "echo \"<html><body><h1>Awesome !!!</h1>\" > /var/www/html/index.html",
                            "echo \"</body></html>\" >> /var/www/html/index.html"
                          ]
                        ]
                      }
                    }
                  }
                }
              }
    
    global CpuAlaram
    CpuAlaram = {
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
    
    global MsSQLInstance
    MsSQLInstance = {
                    "WindowsDBInstance": {
                      "Type": "AWS::RDS::DBInstance",
                      "DependsOn": [
                        "DBSubnetGroup",
                        "RDSAccessSecurityGroup"
                      ],
                      "Properties": {
                        "DBName": "",
                        "LicenseModel": "license-included",
                        "Engine": "sqlserver-ex",
                        "EngineVersion": "14.00.3035.2.v1",
                        "MasterUsername": "",
                        "MasterUserPassword": "",
                        "DBInstanceClass": "",
                        "AllocatedStorage": "",
                        "DBSubnetGroupName": {"Ref" : "DBSubnetGroup"},
                        "VPCSecurityGroups": [
                          {"Ref" : "RDSAccessSecurityGroup"}
                        ],
                      }
                    }
                  }
    global MySQLInstance
    MySQLDBInstance = {
                      "LinuxDBInstance": {
                        "Type": "AWS::RDS::DBInstance",
                        "DependsOn": [
                          "DBSubnetGroup",
                          "RDSAccessSecurityGroup"
                        ],
                        "Properties": {
                          "DBInstanceIdentifier": "",
                          "Engine": "",
                          "MasterUsername": "",
                          "DBInstanceClass": "",
                          "AllocatedStorage": "",
                          "MasterUserPassword": "",
                          "DBSubnetGroupName": {"Ref" : "DBSubnetGroup"},
                          "VPCSecurityGroups": [
                            {"Ref" : "RDSAccessSecurityGroup"}
                          ],
                          "Tags": [
                            {
                              "Key": "database",
                              "Value": "Scheduled"
                            }
                          ]
                        }
                      }
                  }
    #Getting boto3 Client and Resource
    s3 = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    cf = boto3.client('cloudformation')
    
    #Getting Bucket Name and Key form event 
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    #Reading the content of email
    file = s3.get_object(Bucket=bucket, Key=key)

    email_content = email.message_from_string(file['Body'].read().decode('utf-8'))
    attachment = base64.b64decode(email_content.get_payload()[1].get_payload()).decode('utf-8')
    lines = []
    
    for line in attachment.split('\r\n'):
        lines.append(line.split(','))
    
    #Reading the JSon Template 
    template = s3_resource.Object('infra-mail', 'sol.json')
    file_content = template.get()['Body'].read().decode('utf-8')
    Master_template = json.loads(file_content)
    
    #Variables for logic
    count = 0
    i = 1
    ins_lin_server = {}
    ins_win_server = {}
    cloud_watch_alaram = {}
    
    lin_db_count = 0
    win_db_count = 0
    
    #Assign master template
    stack_template = Master_template
    
    
    for row in lines:
        if len(row) > 1:
            #Skip first row - header
            if count == 0:
                count = count+1
                continue
            
            if row[0].lower() == 'linux':
            
                #Linux server instance
                ins_lin_server['LinuxServerInstance'+str(i)] = LinuxServer['LinuxServerInstance']
                ins_lin_server['LinuxServerInstance'+str(i)]['Properties']['InstanceType'] = row[1]
                ins_lin_server['LinuxServerInstance'+str(i)]['Properties']['ImageId']['Fn::FindInMap'][2] = row[0]
                ins_lin_server['LinuxServerInstance'+str(i)]['Properties']['BlockDeviceMappings'][0]['Ebs']['VolumeSize'] = row[2]
                ins_lin_server['LinuxServerInstance'+str(i)]['Properties']['BlockDeviceMappings'][0]['Ebs']['VolumeType'] = row[3]
                

                
                if lin_db_count == 0:
                
                    #MySQL DB Instance
                    MySQLDBInstance['LinuxDBInstance']['Properties']['DBInstanceIdentifier'] = row[6]
                    MySQLDBInstance['LinuxDBInstance']['Properties']['Engine'] = row[4]
                    MySQLDBInstance['LinuxDBInstance']['Properties']['MasterUsername'] = row[8]
                    MySQLDBInstance['LinuxDBInstance']['Properties']['DBInstanceClass'] = row[5]
                    MySQLDBInstance['LinuxDBInstance']['Properties']['AllocatedStorage'] = row[7]
                    MySQLDBInstance['LinuxDBInstance']['Properties']['MasterUserPassword'] = row[9]
                    lin_db_count =  lin_db_count + 1
                
                #Cloud Watch Alaram
                cloud_watch_alaram['CPUAlarm'+str(i)] = CpuAlaram['CPUAlarm']
                cloud_watch_alaram['CPUAlarm'+str(i)]['Properties']['Dimensions'][0]['Value']['Ref'] = 'LinuxServerInstance'+str(i)
                
                #Adding resource to the template
                stack_template['Resources'].update(ins_lin_server)
                stack_template['Resources'].update(MySQLDBInstance)
                stack_template['Resources'].update(cloud_watch_alaram)
                
            elif row[0].lower() == 'windows':
            
                #Windows server instance
                ins_win_server['WinServer'+str(i)] = WinServer['WinInstance']
                ins_win_server['WinServer'+str(i)]['Properties']['InstanceType'] = row[1]
                ins_win_server['WinServer'+str(i)]['Properties']['InstanceType']['ImageId']['Fn::FindInMap'][2] = row[0]
                ins_win_server['WinServer'+str(i)]['Properties']['BlockDeviceMappings'][0]['Ebs']['VolumeSize'] = row[2]
                ins_win_server['WinServer'+str(i)]['Properties']['BlockDeviceMappings'][0]['Ebs']['VolumeType'] = row[3]
                
                if win_db_count == 0:
                
                    #MsSQL DB Instance
                    MsSQLInstance['WindowsDBInstance']['Properties']['DBName'] = row[6]
                    MsSQLInstance['WindowsDBInstance']['Properties']['Engine'] = row[4]
                    MsSQLInstance['WindowsDBInstance']['Properties']['MasterUsername'] = row[8]
                    MsSQLInstance['WindowsDBInstance']['Properties']['AllocatedStorage'] = row[7]
                    MsSQLInstance['WindowsDBInstance']['Properties']['MasterUserPassword'] = row[9]
                    win_db_count = win_db_count + 1
                    
                #Cloud Watch Alaram
                cloud_watch_alaram['CPUAlarm'+str(i)] = CpuAlaram['CPUAlarm']
                cloud_watch_alaram['CPUAlarm'+str(i)]['Properties']['Dimensions'][0]['Value']['Ref'] = 'WinServer'+str(i)
                
                #Adding resource to the template
                stack_template['Resources'].update(ins_win_server)
                stack_template['Resources'].update(MsSQLInstance)
                stack_template['Resources'].update(cloud_watch_alaram)
            i = i + 1
            
            #VPC and Subnet Configuration
            stack_template['Resources']['VPC']['Properties']['CidrBlock'] = row[10]
            stack_template['Resources']['PublicSubnet']['Properties']['CidrBlock'] = row[11]
            stack_template['Resources']['PrivateSubnet1']['Properties']['CidrBlock'] = row[12]
            stack_template['Resources']['PrivateSubnet2']['Properties']['CidrBlock'] = row[13]
            
            
            #Cron Expression
            start = 'cron(m h * * ? *)'
            start_time = row[14].split(':')
            
            end = 'cron(m h * * ? *)'
            end_time = row[15].split(':')
            
            start = start.replace('h',start_time[0]).replace('m', start_time[1])
            end = end.replace('h',end_time[0]).replace('m', end_time[1])
            
            stack_template['Resources']['RDSStopRule']['Properties']['ScheduleExpression'] = end
            stack_template['Resources']['RDSStartRule']['Properties']['ScheduleExpression'] = start
            
            stack_template['Resources']['EC2StopRule']['Properties']['ScheduleExpression'] = end
            stack_template['Resources']['EC2StartRule']['Properties']['ScheduleExpression'] = start
    print('here')
            
    obj = s3_resource.Object('inframindsolution','inframindsolution.json')
    obj.put(Body=json.dumps(stack_template))
    a = json.dumps(stack_template)
    try:
        stack = cf.create_stack(StackName='InframindSolution',TemplateURL= 'https://s3-us-west-2.amazonaws.com/inframindsolution/inframindsolution.json', Capabilities=['CAPABILITY_IAM'])
    except Exception as e:
        print(e)
        
    print("success")
