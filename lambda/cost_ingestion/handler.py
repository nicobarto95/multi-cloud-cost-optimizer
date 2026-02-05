"""
AWS Cost Optimizer - Lambda Ingestion Handler

This Lambda function:
1. Queries AWS Cost Explorer API for spending data
2. Scans for idle/unused resources (EC2, EBS, EIP, RDS)
3. Stores results in S3 for further processing
4. Sends metrics to CloudWatch
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

from utils.cost_explorer import CostExplorerClient
from utils.resource_scanner import ResourceScanner
from utils.s3_writer import S3Writer

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
S3_BUCKET = os.environ.get('COST_DATA_BUCKET')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Response with status and summary
    """
    try:
        logger.info("Starting cost optimization ingestion")
        logger.info(f"Environment: {ENVIRONMENT}")
        logger.info(f"S3 Bucket: {S3_BUCKET}")
        
        # Initialize clients
        cost_explorer = CostExplorerClient()
        resource_scanner = ResourceScanner()
        s3_writer = S3Writer(S3_BUCKET)
        
        # Get date range (last 30 days + today)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        logger.info(f"Analyzing costs from {start_date} to {end_date}")
        
        # 1. Get cost data from Cost Explorer
        cost_data = cost_explorer.get_cost_and_usage(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # 2. Get cost breakdown by service
        service_costs = cost_explorer.get_cost_by_service(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # 3. Scan for idle resources
        idle_resources = resource_scanner.scan_all_resources()
        
        # 4. Calculate cost trends
        cost_trends = cost_explorer.get_cost_trends(
            current_cost=cost_data.get('total_cost', 0),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # 5. Build comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'date': end_date.isoformat(),
            'environment': ENVIRONMENT,
            'summary': {
                'total_cost': cost_data.get('total_cost', 0),
                'idle_resources_count': sum(len(v) for v in idle_resources.values()),
                'potential_savings': calculate_potential_savings(idle_resources)
            },
            'cost_data': cost_data,
            'service_breakdown': service_costs,
            'idle_resources': idle_resources,
            'trends': cost_trends,
            'recommendations': generate_recommendations(idle_resources, service_costs)
        }
        
        logger.info(f"Report summary: {json.dumps(report['summary'], indent=2)}")
        
        # 6. Save to S3
        s3_key = s3_writer.write_daily_report(report, end_date)
        logger.info(f"Report saved to S3: s3://{S3_BUCKET}/{s3_key}")
        
        # 7. Send CloudWatch metrics
        send_cloudwatch_metrics(report)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost ingestion completed successfully',
                'summary': report['summary'],
                's3_location': f's3://{S3_BUCKET}/{s3_key}'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in cost ingestion: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Cost ingestion failed',
                'error': str(e)
            })
        }


def calculate_potential_savings(idle_resources: Dict[str, list]) -> float:
    """
    Calcola risparmi basati sul tipo effettivo di risorsa
    """
    total_savings = 0.0
    
    # EC2 stopped - calcola per tipo istanza
    for instance in idle_resources.get('ec2_stopped', []):
        instance_type = instance.get('type', 't3.medium')
        
        # Mappa prezzi per tipo (eu-west-1)
        ec2_pricing = {
            't3.micro': 10.0,
            't3.small': 15.0,
            't3.medium': 30.0,
            't3.large': 60.0,
            't3.xlarge': 120.0,
        }
        
        total_savings += ec2_pricing.get(instance_type, 30.0)
    
    # EBS - calcola per dimensione effettiva
    for volume in idle_resources.get('ebs_unattached', []):
        size_gb = volume.get('size', 100)
        volume_type = volume.get('type', 'gp3')
        
        # Prezzi per GB/mese
        ebs_pricing = {
            'gp3': 0.08,
            'gp2': 0.10,
            'io1': 0.125,
            'st1': 0.045,
        }
        
        price_per_gb = ebs_pricing.get(volume_type, 0.08)
        total_savings += size_gb * price_per_gb
    
    # EIP - fisso
    total_savings += len(idle_resources.get('eip_unassociated', [])) * 3.65
    
    # RDS - calcola per instance class
    for db in idle_resources.get('rds_stopped', []):
        instance_class = db.get('instance_class', 'db.t3.medium')
        storage_gb = db.get('storage', 100)
        
        # Costo istanza + storage
        rds_instance_pricing = {
            'db.t3.micro': 15.0,
            'db.t3.small': 30.0,
            'db.t3.medium': 60.0,
            'db.t3.large': 120.0,
        }
        
        instance_cost = rds_instance_pricing.get(instance_class, 60.0)
        storage_cost = storage_gb * 0.115  # $0.115/GB per RDS storage
        
        total_savings += instance_cost + storage_cost
    
    # ALB - fisso
    total_savings += len(idle_resources.get('elb_unused', [])) * 18.0
    
    return round(total_savings, 2)


def generate_recommendations(idle_resources: Dict[str, list], 
                            service_costs: Dict[str, Any]) -> list:
    """
    Generate actionable cost optimization recommendations
    
    Args:
        idle_resources: Dictionary of idle resources
        service_costs: Cost breakdown by service
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Idle EC2 instances
    if idle_resources.get('ec2_stopped'):
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Idle Resources',
            'title': f"Terminate {len(idle_resources['ec2_stopped'])} stopped EC2 instances",
            'impact': f"~${len(idle_resources['ec2_stopped']) * 30}/month",
            'action': 'Review and terminate unused instances or convert to reserved instances'
        })
    
    # Unattached EBS volumes
    if idle_resources.get('ebs_unattached'):
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Storage Optimization',
            'title': f"Delete {len(idle_resources['ebs_unattached'])} unattached EBS volumes",
            'impact': f"~${len(idle_resources['ebs_unattached']) * 10}/month",
            'action': 'Create snapshots if needed, then delete volumes'
        })
    
    # Unassociated Elastic IPs
    if idle_resources.get('eip_unassociated'):
        recommendations.append({
            'priority': 'LOW',
            'category': 'Network Optimization',
            'title': f"Release {len(idle_resources['eip_unassociated'])} unassociated Elastic IPs",
            'impact': f"~${len(idle_resources['eip_unassociated']) * 3.65}/month",
            'action': 'Release unused Elastic IPs immediately'
        })
    
    # High-cost services
    top_services = sorted(
        service_costs.get('services', {}).items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:3]
    
    if top_services:
        for service, cost in top_services:
            if cost > 100:  # Only flag if cost > $100
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Cost Review',
                    'title': f"Review {service} spending (${cost:.2f}/month)",
                    'impact': 'Variable',
                    'action': f'Analyze {service} usage patterns for optimization opportunities'
                })
    
    return recommendations


def send_cloudwatch_metrics(report: Dict[str, Any]) -> None:
    """
    Send custom metrics to CloudWatch
    
    Args:
        report: Cost report dictionary
    """
    try:
        cloudwatch = boto3.client('cloudwatch')
        
        metrics = [
            {
                'MetricName': 'TotalDailyCost',
                'Value': report['summary']['total_cost'],
                'Unit': 'None',
                'Timestamp': datetime.now()
            },
            {
                'MetricName': 'IdleResourcesCount',
                'Value': report['summary']['idle_resources_count'],
                'Unit': 'Count',
                'Timestamp': datetime.now()
            },
            {
                'MetricName': 'PotentialSavings',
                'Value': report['summary']['potential_savings'],
                'Unit': 'None',
                'Timestamp': datetime.now()
            }
        ]
        
        for metric in metrics:
            cloudwatch.put_metric_data(
                Namespace='CostOptimizer',
                MetricData=[metric]
            )
        
        logger.info("CloudWatch metrics sent successfully")
        
    except Exception as e:
        logger.warning(f"Failed to send CloudWatch metrics: {str(e)}")
