import configparser
import boto3
import json
import pandas as pd

def get_config(filepath):
    """
    Get config object from config file

    Arg(s):
        filepath: path to the config file
    Return(s):
        config object
    """
    config = configparser.ConfigParser()
    try:
        config.read_file(open('cluster.cfg'))
    except Exception as e:
        print(e)

    return config


def create_iam_role(iam, config):
    """
    Create an IAM role to allow Redshift to access S3.
    Arg(s):
        iam: IAM resource/client
        config: an object that contains necessary information for setting up the cluster
    Return(s):
        AWS RoleARN
    """

    try:
        print('Creating IAM Role')
        dwhRole = iam.create_role(
            RoleName=config['DEFAULT']['ROLE_NAME'],
            Description='IAM Role that allows Redshift to access S3 bucket ReadOnly',
            AssumeRolePolicyDocument=json.dumps(
                {'Version': '2012-10-17',
                'Statement':
                [{'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {'Service': 'redshift.amazonaws.com'}
                }]}))
        # Wait for up to 30 seconds until the role is created successfully
        iam.get_waiter('role_exists').wait(
            RoleName=config['DEFAULT']['ROLE_NAME'],
            WaiterConfig={'Delay': 1, 'MaxAttempts': 30})
    except Exception as e:
        print(e)

    try:
        print('Attaching Policy')
        response = iam.attach_role_policy(
            RoleName=config['DEFAULT']['ROLE_NAME'], 
            PolicyArn='arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess')
    except Exception as e:
        print(e)

    try:
        roleArn = iam.get_role(RoleName=config['DEFAULT']['ROLE_NAME'])['Role']['Arn']
    except Exception as e:
        print(e)

    return roleArn


def create_redshift_cluster(redshift, config, roleArn):
    """
    Create a Redshfit cluster.

    Arg(s):
        redshift: a redshift resource/client
        config: an object that contains necessary information for setting up the cluster
        roleArn: created to be attached to the cluster
    Return(s):
        cluster_prop: a cluster descriptor
    """

    try:
        print('Creating a Redshift Cluster. This might take a few minutes ...')
        response = redshift.create_cluster(
            # parameters for hardware
            ClusterType=config['DEFAULT']['CLUSTER_TYPE'],
            NodeType=config['DEFAULT']['NODE_TYPE'],
            NumberOfNodes=int(config['DEFAULT']['NUM_NODES']),

            # parameters for identifiers & credentials
            ClusterIdentifier=config['DEFAULT']['CLUSTER_IDENTIFIER'],
            DBName=config['DEFAULT']['DB_NAME'],
            MasterUsername=config['DEFAULT']['DB_MASTER_USER'],
            MasterUserPassword=config['DEFAULT']['DB_MASTER_PASSWORD'],
            Port=int(config['DEFAULT']['CLUSTER_PORT']),

            # parameter for role (to allow s3 access)
            IamRoles=[roleArn])
        # Wait for up to 30 minutes until the cluster is created successfully
        redshift.get_waiter('cluster_available').wait(
            ClusterIdentifier=config['DEFAULT']['CLUSTER_IDENTIFIER'],
            WaiterConfig={'Delay': 30, 'MaxAttempts': 60})
    except Exception as e:
        print(e)

    # describe the cluster (codes borrowed from Lession 3 Exercise 2)
    try:
        cluster_props = redshift.describe_clusters(ClusterIdentifier=config['DEFAULT']['CLUSTER_IDENTIFIER'])['Clusters'][0]
    except Exception as e:
        print(e)

    pd.set_option('display.max_colwidth', None)
    keysToShow = ["ClusterIdentifier", "NodeType", "ClusterStatus", "MasterUsername", "DBName", "Endpoint", "NumberOfNodes", 'VpcId']
    x = [(k, v) for k,v in cluster_props.items() if k in keysToShow]
    df = pd.DataFrame(data=x, columns=["Key", "Value"])
    print(df)

    return cluster_props


def create_ec2_sg(ec2, config, cluster_props):
    """
    Create a security group for Redshift cluster

    Arg(s):
        ec2: an EC2 resource/client
        config: an object that contains necessary information for setting up the cluster
        cluster_props: an dict that describes the cluster
    Return(s):
        sg: a default security group
    """

    try:
        vpc = ec2.Vpc(id=cluster_props['VpcId'])
        defaultSg = list(vpc.security_groups.all())[0]

        defaultSg.authorize_ingress(
            GroupName= defaultSg.group_name,
            CidrIp='0.0.0.0/0', # allow traffic from any IP source
            IpProtocol='tcp',
            FromPort=int(config['DEFAULT']['CLUSTER_PORT']),
            ToPort=int(config['DEFAULT']['CLUSTER_PORT'])
            )
    except Exception as e:
        print(e)

    return defaultSg

def main():

    # parse config file
    config = get_config('cluster.cfg')

    # create resources/clients
    iam = boto3.client('iam', region_name=config['DEFAULT']['REGION_NAME'])
    redshift = boto3.client('redshift', region_name=config['DEFAULT']['REGION_NAME'])
    ec2 = boto3.resource('ec2', region_name=config['DEFAULT']['REGION_NAME'])

    roleArn = create_iam_role(iam, config)
    cluster_props = create_redshift_cluster(redshift, config, roleArn)
    sg = create_ec2_sg(ec2, config, cluster_props)

    print('Cluster Setup done.')
    print('RoleArn: {}'.format(roleArn))
    print('Cluster Endpoint: {}'.format(cluster_props['Endpoint']['Address']))
    print('SecurityGroup: {}'.format(sg))
    print("SecurityGroup's Name: {}".format(sg.group_name))
    print("SecurityGroup's IP permissions: {}".format(sg.ip_permissions))

if __name__ == "__main__":
    main()