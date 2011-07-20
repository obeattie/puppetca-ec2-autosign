#!/usr/bin/env python
import ConfigParser
import subprocess
import sys

from boto.ec2 import connect_to_region

CONFIG_LOCATION = '/etc/puppetca-ec2-autosign.conf'
PUPPETCA = '/usr/sbin/puppetca'

def sign(csr_name):
    """Authorises the CSR for the passed host."""
    return subprocess.check_output([PUPPETCA, '--sign', csr_name])

def list_csrs():
    """Returns a list of all outstanding CSRs."""
    csrs = subprocess.check_output([PUPPETCA, '--list'])
    csrs = csrs.split('\n')
    return [r for r in csrs if r]

def verify(csr_name, ec2, instances):
    """Verify the host should be granted the CSR. Do this by checking the host is valid (and running) in EC2."""
    instance_id = csr_name.split('.', 1)[0]
    return (instance_id in instances and instances[instance_id].state == 'running')

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_LOCATION)
    
    ec2 = connect_to_region(
        aws_access_key_id=config.get('aws', 'access_key'),
        aws_secret_access_key=config.get('aws', 'secret_key'),
        region_name=config.get('aws', 'region')
    )
    
    outstanding_csrs = list_csrs()
    if outstanding_csrs:
        reservations = ec2.get_all_instances()
        _instances = [i for r in reservations for i in r.instances]
        instances = {}
        for i in _instances:
            instances[i.id] = i
        
        for csr in outstanding_csrs:
            if verify(csr_name=csr, ec2=ec2, instances=instances):
                sign(csr)
    
    sys.exit(0)
