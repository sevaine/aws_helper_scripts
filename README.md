AWS Helper Scripts:
-------------------

# Content

this repo contains simple helper scripts I use from time to time when supporting AWS environments

## orphaned-security-groups.py

Simple script to load all referenced security groups for:
 - EC2
 - RDS
 - ELB
 - ALB
 - ElasticBeanstalk
and write out a `group_id: group_name` list of any security group id not refernced by a resource in the list above to a txt file for review and consideration for removal
