"""
Cost Explorer API Client

Handles all interactions with AWS Cost Explorer API
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CostExplorerClient:
    """Client for AWS Cost Explorer API"""
    
    def __init__(self):
        """Initialize Cost Explorer client"""
        self.client = boto3.client('ce')
        logger.info("Cost Explorer client initialized")
    
    def get_cost_and_usage(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get total cost and usage for date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with cost data
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            # Calculate total cost
            total_cost = 0.0
            daily_costs = []
            
            for result in response.get('ResultsByTime', []):
                day_cost = 0.0
                for group in result.get('Groups', []):
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    day_cost += cost
                
                daily_costs.append({
                    'date': result['TimePeriod']['Start'],
                    'cost': round(day_cost, 2)
                })
                total_cost += day_cost
            
            logger.info(f"Total cost for period: ${total_cost:.2f}")
            
            return {
                'total_cost': round(total_cost, 2),
                'daily_costs': daily_costs,
                'currency': 'USD'
            }
            
        except ClientError as e:
            logger.error(f"Error getting cost data: {str(e)}")
            raise
    
    def get_cost_by_service(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get cost breakdown by AWS service
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with service costs
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            services = {}
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service in services:
                        services[service] += cost
                    else:
                        services[service] = cost
            
            # Round costs and filter out zero costs
            services = {
                k: round(v, 2) 
                for k, v in services.items() 
                if v > 0.01
            }
            
            logger.info(f"Found costs for {len(services)} services")
            
            return {
                'services': services,
                'top_5_services': self._get_top_services(services, 5)
            }
            
        except ClientError as e:
            logger.error(f"Error getting service costs: {str(e)}")
            raise
    
    def get_cost_by_tags(self, start_date: str, end_date: str, 
                        tag_key: str) -> Dict[str, Any]:
        """
        Get cost breakdown by tag
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            tag_key: Tag key to group by (e.g., 'Environment', 'Team')
            
        Returns:
            Dictionary with tag-based costs
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'TAG', 'Key': tag_key}
                ]
            )
            
            tags = {}
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    tag_value = group['Keys'][0].replace(f'{tag_key}$', '')
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if tag_value in tags:
                        tags[tag_value] += cost
                    else:
                        tags[tag_value] = cost
            
            tags = {k: round(v, 2) for k, v in tags.items() if v > 0.01}
            
            return {
                'tag_key': tag_key,
                'breakdown': tags
            }
            
        except ClientError as e:
            logger.warning(f"Error getting costs by tag {tag_key}: {str(e)}")
            return {
                'tag_key': tag_key,
                'breakdown': {},
                'error': str(e)
            }
    
    def get_cost_trends(self, current_cost: float, start_date: str, 
                       end_date: str) -> Dict[str, Any]:
        """
        Calculate cost trends and comparisons
        
        Args:
            current_cost: Current period total cost
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with trend data
        """
        try:
            # Get previous period cost (same duration)
            end_dt = datetime.fromisoformat(end_date)
            start_dt = datetime.fromisoformat(start_date)
            duration = (end_dt - start_dt).days
            
            prev_end = start_dt - timedelta(days=1)
            prev_start = prev_end - timedelta(days=duration)
            
            prev_response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': prev_start.isoformat(),
                    'End': prev_end.isoformat()
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            prev_cost = 0.0
            for result in prev_response.get('ResultsByTime', []):
                prev_cost += float(result['Total']['UnblendedCost']['Amount'])
            
            # Calculate deltas
            delta_absolute = current_cost - prev_cost
            delta_percent = (delta_absolute / prev_cost * 100) if prev_cost > 0 else 0
            
            logger.info(f"Cost trend: ${current_cost:.2f} vs ${prev_cost:.2f} "
                       f"({delta_percent:+.1f}%)")
            
            return {
                'current_period': round(current_cost, 2),
                'previous_period': round(prev_cost, 2),
                'delta_absolute': round(delta_absolute, 2),
                'delta_percent': round(delta_percent, 2),
                'trend': 'increasing' if delta_absolute > 0 else 'decreasing'
            }
            
        except Exception as e:
            logger.warning(f"Error calculating trends: {str(e)}")
            return {
                'current_period': round(current_cost, 2),
                'error': 'Unable to calculate trend data'
            }
    
    def get_cost_forecast(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get AWS cost forecast
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with forecast data
        """
        try:
            response = self.client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
            
            forecast = float(response['Total']['Amount'])
            
            return {
                'forecasted_cost': round(forecast, 2),
                'period': f"{start_date} to {end_date}",
                'confidence_level': 'Medium'
            }
            
        except Exception as e:
            logger.warning(f"Error getting forecast: {str(e)}")
            return {
                'error': 'Forecast unavailable'
            }
    
    @staticmethod
    def _get_top_services(services: Dict[str, float], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get top N services by cost
        
        Args:
            services: Dictionary of service costs
            top_n: Number of top services to return
            
        Returns:
            List of top services with costs
        """
        sorted_services = sorted(
            services.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_n]
        
        return [
            {'service': service, 'cost': cost}
            for service, cost in sorted_services
        ]
