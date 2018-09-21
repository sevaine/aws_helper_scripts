"""
    cloudformation.py - functions for interacting with cloudformation
"""
from os import environ
from boto3 import client as boto3_client

CFN = boto3_client('cloudformation', region_name=environ.get('AWS_REGION', 'ap-southeast-2'))

def all_stacks():
    """ generator construct for all stacks """
    next_token = None
    while True:
        if next_token is None:
            resp = CFN.list_stacks()
        else:
            resp = CFN.list_stacks(NextToken=next_token)
        if not resp['StackSummaries']:
            break
        for summary in resp['StackSummaries']:
            yield summary
        if 'NextToken' in resp.keys():
            next_token = resp['NextToken']
        else:
            break

def stack_parameters(stack_detail):
    """
        Convert stack parameters from stack detail into a dict()
        @param stack_detail: The output of lookup_stack
    """
    parameters = {x['ParameterKey']:x['ParameterValue'] for x in stack_detail['Parameters']}
    return parameters

if __name__ == '__main__':
    for stack in all_stacks():
        print(stack['StackName'])
