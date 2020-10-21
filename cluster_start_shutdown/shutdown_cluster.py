import configparser
import boto3
import json
from start_cluster import get_config

def main():

	# parse config file
	config = get_config('cluster.cfg')

	# create resources/clients
	iam = boto3.client('iam', region_name=config['DEFAULT']['REGION_NAME'])
	redshift = boto3.client('redshift', region_name=config['DEFAULT']['REGION_NAME'])
	ec2 = boto3.resource('ec2', region_name=config['DEFAULT']['REGION_NAME'])

	try:
		# delete cluster
		print('Deleting Redshift cluster {}. This might take a few minutes ...'.format(config['DEFAULT']['CLUSTER_IDENTIFIER']))
		response = redshift.delete_cluster( ClusterIdentifier=config['DEFAULT']['CLUSTER_IDENTIFIER'],  
											SkipFinalClusterSnapshot=True)
		# Wait for up to 30 minutes until the cluster is deleted successfully
		redshift.get_waiter('cluster_deleted').wait(ClusterIdentifier=config['DEFAULT']['CLUSTER_IDENTIFIER'],
													WaiterConfig={'Delay': 30, 'MaxAttempts': 60})

		# delete role and attached policy
		print('Deleting IAM Role {}'.format(config['DEFAULT']['ROLE_NAME']))
		iam.detach_role_policy(RoleName=config['DEFAULT']['ROLE_NAME'],
						   	   PolicyArn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess")
		iam.delete_role(RoleName=config['DEFAULT']['ROLE_NAME'])

		# revoke ingress rules
		sg = ec2.security_groups.all()[0]
		print('Revoking Ingress rules for SecurityGroup {}'.format(sg))
		sg.revoke_ingress(GroupName=sg.group_name,
						  CidrIp='0.0.0.0/0',
						  IpProtocol='tcp',
						  FromPort=int(config['DEFAULT']['CLUSTER_PORT']),
						  ToPort=int(config['DEFAULT']['CLUSTER_PORT']))
	except Exception as e:
		print(e)

	print('Clean up completed. All resources deleted.')

if __name__ == "__main__":
	main()