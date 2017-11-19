import os
import sys
import re
import datetime
import boto3
import certifi

from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from botocore.exceptions import ClientError

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

def get_domain_endpoint(dn, region):
    try:
        c = boto3.client('es',region_name=region)
        r = c.describe_elasticsearch_domain(DomainName=dn)
        return r['DomainStatus']['Endpoint']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            LOGGER.error("Unable to find endpoint for ES domain {0} in region {1}".format(
                dn,region))
            return None
        else:
            raise


def lambda_handler(event, context):
    session = boto3.session.Session()
    region = session.region_name
    credentials = session.get_credentials().get_frozen_credentials()
    dn = os.getenv('DOMAIN_NAME')
    endpoint = get_domain_endpoint(dn,region)
    if endpoint == None:
        return
    LOGGER.info("Connecting to ES domain {0} and listing indices".format(dn))
    
    awsauth = AWSRequestsAuth(
        aws_access_key=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_token=credentials.token,
        aws_host=endpoint,
        aws_region=region,
        aws_service='es'
    )
    es = Elasticsearch(["https://"+endpoint],
                       http_auth=awsauth,
                       connection_class=RequestsHttpConnection,
                       ca_certs=certifi.where(),
                       verify_certs=True)
    indices = es.indices.get_alias("*").keys()
    # filter for ones matching the regex
    pattern = re.compile(os.getenv('INDEX_REGEX'))
    cutoff = datetime.datetime.now() - datetime.timedelta(days=int(os.getenv('DAYS_TO_SAVE'))+1)
    for idx in indices:
        m = pattern.match(idx)
        if m == None:
            continue
        dt = datetime.datetime(int(m.groupdict()['y']),
                               int(m.groupdict()['m']),
                               int(m.groupdict()['d']))
        if dt < cutoff:
            LOGGER.info("Deleting index {0}".format(idx))
            es.indices.delete(index=idx,ignore=[400,404])
                
                
    
