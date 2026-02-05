"""
Resource Scanner

Scans AWS account for idle and unused resources
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ResourceScanner:
    """Scanner for idle and unused AWS resources"""
    
    def __init__(self):
        """Initialize AWS clients"""
        self.ec2 = boto3.client('ec2')
        self.rds = boto3.client('rds')
        self.elbv2 = boto3.client('elbv2')
        self.cloudwatch = boto3.client('cloudwatch')
        logger.info("Resource scanner initialized")
    
    def scan_all_resources(self) -> Dict[str, List[str]]:
        """
        Scan all resource types for idle/unused instances
        
        Returns:
            Dictionary mapping resource type to list of resource IDs
        """
        idle_resources = {
            'ec2_stopped': self.scan_stopped_ec2(),
            'ebs_unattached': self.scan_unattached_ebs(),
            'eip_unassociated': self.scan_unassociated_eips(),
            'rds_stopped': self.scan_stopped_rds(),
            'elb_unused': self.scan_unused_load_balancers(),
        }
        
        total_idle = sum(len(v) for v in idle_resources.values())
        logger.info(f"Found {total_idle} total idle resources")
        
        return idle_resources
    
    def scan_stopped_ec2(self) -> List[str]:
        """
        Find EC2 instances in 'stopped' state
        
        Returns:
            List of stopped instance IDs
        """
        try:
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['stopped']}
                ]
            )
            
            stopped_instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    
                    # Get instance tags for context
                    tags = {tag['Key']: tag['Value'] 
                           for tag in instance.get('Tags', [])}
                    
                    stopped_instances.append({
                        'id': instance_id,
                        'type': instance['InstanceType'],
                        'name': tags.get('Name', 'N/A'),
                        'environment': tags.get('Environment', 'N/A'),
                        'launch_time': instance['LaunchTime'].isoformat()
                    })
            
            logger.info(f"Found {len(stopped_instances)} stopped EC2 instances")
            return stopped_instances
            
        except ClientError as e:
            logger.error(f"Error scanning stopped EC2: {str(e)}")
            return []
    
    def scan_unattached_ebs(self) -> List[str]:
        """
        Find EBS volumes not attached to any instance
        
        Returns:
            List of unattached volume IDs
        """
        try:
            response = self.ec2.describe_volumes(
                Filters=[
                    {'Name': 'status', 'Values': ['available']}
                ]
            )
            
            unattached_volumes = []
            for volume in response.get('Volumes', []):
                volume_id = volume['VolumeId']
                
                # Get volume tags
                tags = {tag['Key']: tag['Value'] 
                       for tag in volume.get('Tags', [])}
                
                unattached_volumes.append({
                    'id': volume_id,
                    'size': volume['Size'],
                    'type': volume['VolumeType'],
                    'name': tags.get('Name', 'N/A'),
                    'created': volume['CreateTime'].isoformat()
                })
            
            logger.info(f"Found {len(unattached_volumes)} unattached EBS volumes")
            return unattached_volumes
            
        except ClientError as e:
            logger.error(f"Error scanning unattached EBS: {str(e)}")
            return []
    
    def scan_unassociated_eips(self) -> List[str]:
        """
        Find Elastic IPs not associated with any instance
        
        Returns:
            List of unassociated EIP allocation IDs
        """
        try:
            response = self.ec2.describe_addresses()
            
            unassociated_eips = []
            for address in response.get('Addresses', []):
                # EIP is unassociated if it has no AssociationId
                if 'AssociationId' not in address:
                    allocation_id = address.get('AllocationId', 'N/A')
                    public_ip = address.get('PublicIp', 'N/A')
                    
                    unassociated_eips.append({
                        'allocation_id': allocation_id,
                        'public_ip': public_ip,
                        'domain': address.get('Domain', 'N/A')
                    })
            
            logger.info(f"Found {len(unassociated_eips)} unassociated Elastic IPs")
            return unassociated_eips
            
        except ClientError as e:
            logger.error(f"Error scanning unassociated EIPs: {str(e)}")
            return []
    
    def scan_stopped_rds(self) -> List[str]:
        """
        Find RDS instances in 'stopped' state
        
        Returns:
            List of stopped RDS instance identifiers
        """
        try:
            response = self.rds.describe_db_instances()
            
            stopped_instances = []
            for db_instance in response.get('DBInstances', []):
                if db_instance['DBInstanceStatus'] == 'stopped':
                    db_id = db_instance['DBInstanceIdentifier']
                    
                    stopped_instances.append({
                        'id': db_id,
                        'instance_class': db_instance['DBInstanceClass'],
                        'engine': db_instance['Engine'],
                        'storage': db_instance['AllocatedStorage']
                    })
            
            logger.info(f"Found {len(stopped_instances)} stopped RDS instances")
            return stopped_instances
            
        except ClientError as e:
            logger.error(f"Error scanning stopped RDS: {str(e)}")
            return []
    
    def scan_unused_load_balancers(self) -> List[str]:
        """
        Find load balancers with no active targets
        
        Returns:
            List of unused load balancer ARNs
        """
        try:
            response = self.elbv2.describe_load_balancers()
            
            unused_lbs = []
            for lb in response.get('LoadBalancers', []):
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                
                # Get target groups for this LB
                tg_response = self.elbv2.describe_target_groups(
                    LoadBalancerArn=lb_arn
                )
                
                has_healthy_targets = False
                for tg in tg_response.get('TargetGroups', []):
                    tg_arn = tg['TargetGroupArn']
                    
                    # Check target health
                    health_response = self.elbv2.describe_target_health(
                        TargetGroupArn=tg_arn
                    )
                    
                    for target in health_response.get('TargetHealthDescriptions', []):
                        if target['TargetHealth']['State'] == 'healthy':
                            has_healthy_targets = True
                            break
                    
                    if has_healthy_targets:
                        break
                
                # If no healthy targets, mark as unused
                if not has_healthy_targets:
                    unused_lbs.append({
                        'arn': lb_arn,
                        'name': lb_name,
                        'type': lb['Type'],
                        'scheme': lb['Scheme']
                    })
            
            logger.info(f"Found {len(unused_lbs)} unused load balancers")
            return unused_lbs
            
        except ClientError as e:
            logger.error(f"Error scanning unused load balancers: {str(e)}")
            return []
    
    def scan_low_utilization_ec2(self, threshold_percent: float = 10.0) -> List[str]:
        """
        Find EC2 instances with low CPU utilization (< threshold %)
        
        Args:
            threshold_percent: CPU utilization threshold percentage
            
        Returns:
            List of low-utilization instance IDs
        """
        try:
            # Get all running instances
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            low_util_instances = []
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    
                    # Get CloudWatch metrics for CPU utilization
                    metrics_response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[
                            {'Name': 'InstanceId', 'Value': instance_id}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1 day
                        Statistics=['Average']
                    )
                    
                    # Calculate average CPU over period
                    datapoints = metrics_response.get('Datapoints', [])
                    if datapoints:
                        avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                        
                        if avg_cpu < threshold_percent:
                            tags = {tag['Key']: tag['Value'] 
                                   for tag in instance.get('Tags', [])}
                            
                            low_util_instances.append({
                                'id': instance_id,
                                'type': instance['InstanceType'],
                                'avg_cpu': round(avg_cpu, 2),
                                'name': tags.get('Name', 'N/A')
                            })
            
            logger.info(f"Found {len(low_util_instances)} low-utilization instances")
            return low_util_instances
            
        except Exception as e:
            logger.error(f"Error scanning low-utilization EC2: {str(e)}")
            return []
