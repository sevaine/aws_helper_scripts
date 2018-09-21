#!/usr/bin/env python
"""
orphaned_security_groups.py - report on security groups in an account
that are not in use by any resource
"""
import os
import boto3

EC2 = boto3.client('ec2', region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))
ELB = boto3.client('elb', region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))
ALB = boto3.client('elbv2', region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))
RDS = boto3.client('rds', region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))
EB = boto3.client('elasticbeanstalk', region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))

def aws_regions():
    """Return a list of available AWS regions"""
    return [x['RegionName'] for x in EC2.describe_regions()['Regions']]

def security_groups():
    """return a dict of all security groups and their names"""
    return {x['GroupId']:x['GroupName'] for x in EC2.describe_security_groups()['SecurityGroups']}

def instance_security_groups():
    """ Generator function to return security group ids for all instances """
    for reservation in EC2.describe_instances()['Reservations']:
        for instance in reservation['Instances']:
            for security_group in instance['SecurityGroups']:
                yield security_group['GroupId']

def network_interface_security_groups():
    """ Generator function to return sg ids associated with ENIs """
    for eni in EC2.describe_network_interfaces()['NetworkInterfaces']:
        for group in eni['Groups']:
            yield group['GroupId']

def elb_security_groups():
    """ Generator function to return sg ids for ELBs"""
    for elb in ELB.describe_load_balancers()['LoadBalancerDescriptions']:
        for sg in elb['SecurityGroups']:
            yield sg

def alb_security_groups():
    """ Generator function to retirn sg ids for ALBs """
    for alb in ALB.describe_load_balancers()['LoadBalancers']:
        if 'SecurityGroups' in alb.keys():
            for sg in alb['SecurityGroups']:
                yield sg

def rds_security_groups():
    """ Generator function to return sg ids for RDS """
    for rds in RDS.describe_db_instances()['DBInstances']:
        sg_ids = []
        if rds['DBSecurityGroups']:
            for sg_id in rds['DBSecurityGroups']:
                sg_ids.append(sg_id)
        if rds['VpcSecurityGroups']:
            for vpc_sg in rds['VpcSecurityGroups']:
                sg_ids.append(vpc_sg['VpcSecurityGroupId'])
        for sg_id in sg_ids:
            yield sg_id

def beanstalk_security_groups():
    """ return in-use security groups for EB environments """
    for environment in EB.describe_environments()['Environments']:
        env_name = environment['EnvironmentName']
        resources = EB.describe_environment_resources(EnvironmentName=env_name)
        for instance in resources['EnvironmentResources']['Instances']:
            instance_id = instance['Id']
            instance_data = EC2.describe_instances(InstanceIds=[instance_id])
            instance_data = instance_data['Reservations'][0]['Instances'][0]
            for sg_data in instance_data['SecurityGroups']:
                yield sg_data['GroupId']


if __name__ == '__main__':
    in_use = []

    print("Loading in-use security groups for EC2 instances")
    for x in instance_security_groups():
        in_use.append(x)

    print("Loading in-use security groups for ENIs")
    for x in network_interface_security_groups():
        in_use.append(x)

    print("Loading in-use security groups for ELBs")
    for x in elb_security_groups():
        in_use.append(x)

    print("Loading in-use security groups for ALBs")
    for x in alb_security_groups():
        in_use.append(x)

    print("Loading in-use security groups for RDS instances")
    for x in rds_security_groups():
        in_use.append(x)

    print("Loading in-use security groups for ElasticBeanstalk instances")
    for x in beanstalk_security_groups():
        in_use.append(x)

    print("Loading list of all security groups")
    all_sgs = security_groups()

    print("Filtering for default and AWS internal security groups")
    for group_id, group_name in all_sgs.items():
        if group_name == 'default' or group_name.startswith('d-') or group_name.startswith('AWS'):
            in_use.append(group_id)

    print("constructing Set of in-use security groups")
    IN_USE_SG = set(in_use)

    print("{} security groups identified as in-use".format(len(IN_USE_SG)))
    print("{} security groups total".format(len(all_sgs.keys())))

    print("\n\n")
    print("Constructing list of security group candidates for removal")
    print("Output file: orphaned_security_groups.txt")
    with open('orphaned_security_groups.txt', 'w') as out_file:
        for group_id, group_name in all_sgs.items():
            if group_id in IN_USE_SG:
                continue
            out_file.write("{}: {}\n".format(group_id, group_name))
