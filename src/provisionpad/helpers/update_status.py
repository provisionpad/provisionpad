import os
import sys
from provisionpad.db.database import load_database, save_database
from provisionpad.aws.aws_ec2 import AWSec2Funcs
from provisionpad.helpers.texthelpers import delete_text_from_file, write_into_text
from copy import deepcopy
from provisionpad.helpers.namehelpers import get_box_name

# 0 : pending # 16 : running # 32 : shutting-down
# 48 : terminated  # 64 : stopping # 80 : stopped

def update_status(env_vars, DB):

    region = env_vars['aws_region']
    home_folder = env_vars['HOME']
    access_key = env_vars['access_key']
    secret_key = env_vars['secret_key']
    awsec2f = AWSec2Funcs(region, access_key, secret_key)
    aws_inst_info = awsec2f.instance_state(env_vars['your_name'])

    for ins in aws_inst_info:
        if not (aws_inst_info[ins][0] == 'stopped' and 
                aws_inst_info[ins][0] == 'running' and
                aws_inst_info[ins][0] == 'terminated'):
            print ('try a little bit later there is a transition going on')
            sys.exit()

    print (aws_inst_info)
    DBD = deepcopy(DB)
    for ins, ins_info in DBD['running_instances'].items():
        print (ins, ins_info)
        if ins_info['id'] not in aws_inst_info:
            print ('seems like the instance you have created ')
            print ('has been removed from the aws manually most likely')
            print ('removing it from the database')
            del(DB['running_instances'][ins])
            if ins[0:3] == 'box':
                DB['available_names'].append(ins)
            save_database(DB, env_vars['db_path'])
            delete_text_from_file(ins, os.path.join(home_folder,'.ssh/config'))
        elif ins_info['id'] in aws_inst_info and aws_inst_info[ins_info['id']][0]=='stopped':
            print ('seems like the instance has been stopped')
            print ('removing it from the running instances') 
            DB['stopped_instances'][ins] = DB['running_instances'][ins]
            del(DB['running_instances'][ins])
            save_database(DB, env_vars['db_path'])
            delete_text_from_file(ins, os.path.join(home_folder,'.ssh/config'))
        else:
            print ('{0} is fine as expected'.format(ins))

    DBD = deepcopy(DB)
    for ins, ins_info in DBD['stopped_instances'].items():
        print (ins, ins_info)
        if ins_info['id'] not in aws_inst_info:
            print ('seems like the instance you have created ')
            print ('has been removed from the aws manually most likely')
            print ('removing it from the database')
            del(DB['stopped_instances'][ins])
            if ins[0:3] == 'box':
                DB['available_names'].append(ins)
            save_database(DB, env_vars['db_path'])
            delete_text_from_file(ins, os.path.join(home_folder,'.ssh/config'))
        elif ins_info['id'] in aws_inst_info and aws_inst_info[ins_info['id']][0]=='running':
            print ('seems like the instance has started manually')
            print ('moving from stopped to running') 
            DB['running_instances'][ins] = DB['stopped_instances'][ins]
            DB['running_instances'][ins]['public_ip'] = aws_inst_info[ins_info['id']][1]
            del(DB['stopped_instances'][ins])
            save_database(DB, env_vars['db_path'])
            write_into_text(ins,
'''
Host {0}
    HostName {1}
    User ubuntu
    IdentityFile {2}
    ForwardAgent yes
    StrictHostKeyChecking no
'''.format(ins, DB['running_instances'][ins]['public_ip'], env_vars['key_pair_path']), 
os.path.join(home_folder,'.ssh/config'))
        else:
            print ('{0} is fine as expected'.format(ins))

    ids_db = set([])
    for x in DB['running_instances']:
        ids_db.add(DB['running_instances'][x]['id'])
    for x in DB['stopped_instances']:
        ids_db.add(DB['stopped_instances'][x]['id'])

    to_create = set(aws_inst_info) - ids_db 
    for x in to_create:
        get_box_name(DB, env_vars['db_path'])
        thekeyname = 'stopped_instances'
        if aws_inst_info[x][0] == 'running':
            thekeyname = 'running_instances' 
        boxname = get_box_name(DB, env_vars['db_path'])
        DB[thekeyname][boxname] = awsec2f.get_instance_info(x)
        write_into_text(ins,
'''
Host {0}
    HostName {1}
    User ubuntu
    IdentityFile {2}
    ForwardAgent yes
    StrictHostKeyChecking no
'''.format(ins, DB[thekeyname][boxname]['public_ip'], env_vars['key_pair_path']), 
os.path.join(home_folder,'.ssh/config'))
            
    if len(ids_db - set(aws_inst_info))>0:
        print ('this should not happen in status')
        sys.exit()
    
    save_database(DB, env_vars['db_path'])