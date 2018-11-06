"""
    list_instance_profiles - list iam instance profiles
"""
from os import environ
import re
import boto3

IAM = boto3.client('iam', region_name=environ.get('AWS_REGION', 'ap-southeast-2'))
EC2 = boto3.client('ec2', region_name=environ.get('AWS_REGION', 'ap-southeast-2'))

def list_instance_profile_arns():
    """
    return a list of all instance profile arns.
    """
    marker = None
    ec2_instance_profile_re = '^arn:aws:iam::\d+:instance-profile\/.+InstanceProfile-[A-Z0-9]{10,100}'
    instance_profile_arns = []
    while True:
        if marker:
            resp = IAM.list_instance_profiles(Marker=marker)
        else:
            resp = IAM.list_instance_profiles()
        if not resp['InstanceProfiles']:
            break
        for profile in resp['InstanceProfiles']:
            arn = profile['Arn']
            if re.match(ec2_instance_profile_re, arn):
                instance_profile_arns.append(profile['Arn'])
        if 'Marker' in resp.keys():
            marker = resp['Marker']
        else:
            break
    return instance_profile_arns

def list_attached_ec2_instance_profiles():
    """
    return a list of in-use instance profile arns
    """
    arns = []
    for res in EC2.describe_instances()['Reservations']:
        for instance in res['Instances']:
            if 'IamInstanceProfile' in instance.keys():
                arns.append(instance['IamInstanceProfile']['Arn'])
    arns = set(arns)
    return arns


print("Loading list of instance profile arns for region {}".format(
    environ.get('AWS_REGION', 'ap-southeast-2')))
INSTANCE_PROFILES = list_instance_profile_arns()

print("Loading list of in-use instance profile arns for region {}".format(
    environ.get('AWS_REGION', 'ap-southeast-2')))
IN_USE = list_attached_ec2_instance_profiles()

print("Finding unused instance profile ARNs")
UNUSED = [x for x in INSTANCE_PROFILES if x not in IN_USE]

print("Unused EC2 Instance Profiles:")
for arn in UNUSED:
    print(arn)
