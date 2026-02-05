"""
S3 Writer

Handles writing cost reports to S3
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Writer:
    """Writer for S3 cost data storage"""
    
    def __init__(self, bucket_name: str):
        """
        Initialize S3 writer
        
        Args:
            bucket_name: S3 bucket name for storing reports
        """
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')
        logger.info(f"S3 writer initialized for bucket: {bucket_name}")
    
    def write_daily_report(self, report: Dict[str, Any], date: datetime.date) -> str:
        """
        Write daily cost report to S3
        
        Args:
            report: Cost report dictionary
            date: Report date
            
        Returns:
            S3 key where report was saved
        """
        try:
            # Generate S3 key with date-based partitioning
            # Format: reports/year=YYYY/month=MM/day=DD/report.json
            s3_key = (
                f"reports/"
                f"year={date.year}/"
                f"month={date.month:02d}/"
                f"day={date.day:02d}/"
                f"cost-report-{date.isoformat()}.json"
            )
            
            # Convert report to JSON
            report_json = json.dumps(report, indent=2, default=str)
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=report_json,
                ContentType='application/json',
                ServerSideEncryption='AES256',
                Metadata={
                    'report-date': date.isoformat(),
                    'generated-at': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Report saved to s3://{self.bucket_name}/{s3_key}")
            
            # Also save as "latest" for easy access
            latest_key = "reports/latest/cost-report.json"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=latest_key,
                Body=report_json,
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Latest report updated: s3://{self.bucket_name}/{latest_key}")
            
            return s3_key
            
        except ClientError as e:
            logger.error(f"Error writing report to S3: {str(e)}")
            raise
    
    def write_summary_report(self, summaries: list, month: str) -> str:
        """
        Write monthly summary report aggregating daily reports
        
        Args:
            summaries: List of daily summary dictionaries
            month: Month in YYYY-MM format
            
        Returns:
            S3 key where summary was saved
        """
        try:
            year, month_num = month.split('-')
            
            s3_key = (
                f"summaries/"
                f"year={year}/"
                f"month={month_num}/"
                f"monthly-summary-{month}.json"
            )
            
            summary_data = {
                'month': month,
                'generated_at': datetime.now().isoformat(),
                'daily_summaries': summaries,
                'totals': self._calculate_monthly_totals(summaries)
            }
            
            summary_json = json.dumps(summary_data, indent=2, default=str)
            
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=summary_json,
                ContentType='application/json',
                ServerSideEncryption='AES256',
                Metadata={
                    'report-month': month,
                    'generated-at': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Monthly summary saved to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Error writing summary to S3: {str(e)}")
            raise
    
    def read_latest_report(self) -> Dict[str, Any]:
        """
        Read the latest cost report from S3
        
        Returns:
            Latest report dictionary
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key="reports/latest/cost-report.json"
            )
            
            report_json = response['Body'].read().decode('utf-8')
            report = json.loads(report_json)
            
            logger.info("Latest report retrieved from S3")
            return report
            
        except ClientError as e:
            logger.warning(f"Could not read latest report: {str(e)}")
            return {}
    
    def list_reports(self, start_date: str = None, end_date: str = None) -> list:
        """
        List all reports in S3 within date range
        
        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            List of S3 keys for reports
        """
        try:
            prefix = "reports/year="
            
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            reports = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith('.json') and 'latest' not in key:
                    reports.append({
                        'key': key,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            logger.info(f"Found {len(reports)} reports in S3")
            return reports
            
        except ClientError as e:
            logger.error(f"Error listing reports: {str(e)}")
            return []
    
    @staticmethod
    def _calculate_monthly_totals(summaries: list) -> Dict[str, float]:
        """
        Calculate monthly totals from daily summaries
        
        Args:
            summaries: List of daily summary dictionaries
            
        Returns:
            Dictionary with monthly totals
        """
        total_cost = sum(s.get('total_cost', 0) for s in summaries)
        total_savings = sum(s.get('potential_savings', 0) for s in summaries)
        avg_daily_cost = total_cost / len(summaries) if summaries else 0
        
        return {
            'total_cost': round(total_cost, 2),
            'total_potential_savings': round(total_savings, 2),
            'average_daily_cost': round(avg_daily_cost, 2),
            'days_analyzed': len(summaries)
        }
