import os
import sys
from provisionpad.aws.aws_ec2 import AWSec2Funcs
# from provisionpad.helpers.namehelpers import vpc_name
from provisionpad.db.database import load_database, save_database

def create_vpc(env_vars, DB):
    region = env_vars['aws_region']
    access_key = env_vars['access_key']
    secret_key = env_vars['secret_key']
    awsf = AWSec2Funcs(region, access_key, secret_key)
    thename = env_vars['vpc_name']
    if thename in DB:
        print ('The VPC with the name: {0} exists.'.format(thename))
        sys.exit()

    # awsf.create_vpc(thename)
    # try:
    #     x = open('/sdfaqq/qwersadf')
    # except:
    #     raise Exception('Hey Dude')
    # try:
    vpc_params = awsf.create_vpc(thename)
    vpcid = vpc_params.vpc_id
    # vpcid = 'vpc-04757c1ab435658e8'
    if type(vpc_params.vpc_id)==type(-1):
        raise Exception('Was not able to create VPC. Check your permissions')
    elif type(vpc_params.sg_id)==type('s') and type(vpc_params.vpc_id)==type(-1):
        awsf.delete_vpc(vpcid)
        raise Exception('Was able to create basic VPC but fails further down with VPC dependencies')


    print (vpc_params.sg_id, vpc_params.subnet_id, vpc_params.vpc_id)
    DB[thename] = {}
    DB[thename]['vpc_id']    = vpc_params.vpc_id
    DB[thename]['sg_id']     = vpc_params.sg_id
    DB[thename]['subnet_id'] = vpc_params.subnet_id
    save_database(DB, env_vars['db_path'])

# if __name__ == "__main__":
#     create_vpc()