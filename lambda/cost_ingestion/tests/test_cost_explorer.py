"""
Unit tests for cost_explorer module

Run with: python -m pytest tests/
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.cost_explorer import CostExplorerClient


class TestCostExplorerClient:
    """Test suite for CostExplorerClient"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Cost Explorer client"""
        with patch('boto3.client') as mock_boto:
            client = CostExplorerClient()
            yield client, mock_boto
    
    def test_get_cost_and_usage_success(self, mock_client):
        """Test successful cost retrieval"""
        client, mock_boto = mock_client
        
        # Mock response
        mock_response = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2025-01-01', 'End': '2025-01-02'},
                    'Groups': [
                        {
                            'Keys': ['Amazon EC2'],
                            'Metrics': {
                                'UnblendedCost': {'Amount': '100.50', 'Unit': 'USD'},
                                'UsageQuantity': {'Amount': '10', 'Unit': 'N/A'}
                            }
                        }
                    ]
                }
            ]
        }
        
        client.client.get_cost_and_usage = Mock(return_value=mock_response)
        
        # Execute
        result = client.get_cost_and_usage(
            start_date='2025-01-01',
            end_date='2025-01-02'
        )
        
        # Assert
        assert result['total_cost'] == 100.50
        assert len(result['daily_costs']) == 1
        assert result['currency'] == 'USD'
    
    def test_get_cost_by_service(self, mock_client):
        """Test cost breakdown by service"""
        client, mock_boto = mock_client
        
        mock_response = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2025-01-01', 'End': '2025-02-01'},
                    'Groups': [
                        {
                            'Keys': ['Amazon EC2'],
                            'Metrics': {'UnblendedCost': {'Amount': '150.00'}}
                        },
                        {
                            'Keys': ['Amazon RDS'],
                            'Metrics': {'UnblendedCost': {'Amount': '80.00'}}
                        }
                    ]
                }
            ]
        }
        
        client.client.get_cost_and_usage = Mock(return_value=mock_response)
        
        result = client.get_cost_by_service(
            start_date='2025-01-01',
            end_date='2025-02-01'
        )
        
        assert 'Amazon EC2' in result['services']
        assert result['services']['Amazon EC2'] == 150.00
        assert len(result['top_5_services']) <= 5
    
    def test_get_cost_trends(self, mock_client):
        """Test cost trend calculation"""
        client, mock_boto = mock_client
        
        # Mock previous period response
        mock_response = {
            'ResultsByTime': [
                {
                    'Total': {'UnblendedCost': {'Amount': '200.00'}}
                }
            ]
        }
        
        client.client.get_cost_and_usage = Mock(return_value=mock_response)
        
        result = client.get_cost_trends(
            current_cost=245.32,
            start_date='2025-02-01',
            end_date='2025-02-04'
        )
        
        assert result['current_period'] == 245.32
        assert result['previous_period'] == 200.00
        assert result['delta_absolute'] == 45.32
        assert result['trend'] == 'increasing'
    
    def test_get_top_services(self, mock_client):
        """Test top services extraction"""
        client, _ = mock_client
        
        services = {
            'EC2': 150.00,
            'RDS': 80.00,
            'S3': 20.00,
            'Lambda': 5.00,
            'DynamoDB': 15.00,
            'CloudWatch': 3.00
        }
        
        top_services = client._get_top_services(services, top_n=3)
        
        assert len(top_services) == 3
        assert top_services[0]['service'] == 'EC2'
        assert top_services[1]['service'] == 'RDS'
        assert top_services[2]['service'] == 'S3'


class TestResourceScanner:
    """Test suite for ResourceScanner"""
    
    @pytest.fixture
    def mock_scanner(self):
        """Create a mock resource scanner"""
        with patch('boto3.client'):
            from utils.resource_scanner import ResourceScanner
            scanner = ResourceScanner()
            yield scanner
    
    def test_scan_stopped_ec2(self, mock_scanner):
        """Test stopped EC2 instance detection"""
        mock_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-abc123',
                            'InstanceType': 't3.medium',
                            'LaunchTime': datetime.now(),
                            'Tags': [
                                {'Key': 'Name', 'Value': 'test-instance'},
                                {'Key': 'Environment', 'Value': 'dev'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        mock_scanner.ec2.describe_instances = Mock(return_value=mock_response)
        
        result = mock_scanner.scan_stopped_ec2()
        
        assert len(result) == 1
        assert result[0]['id'] == 'i-abc123'
        assert result[0]['type'] == 't3.medium'
        assert result[0]['name'] == 'test-instance'


class TestS3Writer:
    """Test suite for S3Writer"""
    
    @pytest.fixture
    def mock_writer(self):
        """Create a mock S3 writer"""
        with patch('boto3.client'):
            from utils.s3_writer import S3Writer
            writer = S3Writer('test-bucket')
            yield writer
    
    def test_write_daily_report(self, mock_writer):
        """Test daily report writing"""
        report = {
            'date': '2025-02-04',
            'total_cost': 245.32,
            'summary': {}
        }
        
        mock_writer.s3.put_object = Mock(return_value={})
        
        result = mock_writer.write_daily_report(
            report,
            datetime(2025, 2, 4).date()
        )
        
        assert 'year=2025' in result
        assert 'month=02' in result
        assert 'day=04' in result
        assert result.endswith('.json')


# Fixture for pytest configuration
@pytest.fixture(scope="session")
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
