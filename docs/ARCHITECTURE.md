# Architecture Documentation

## System Overview

The Multi-Cloud Cost Optimizer is a serverless application designed to monitor, analyze, and optimize cloud spending across AWS environments.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS Account                                    │
│                                                                          │
│  ┌────────────────┐                                                     │
│  │  EventBridge   │  Triggers daily at 2 AM UTC                        │
│  │  (Scheduler)   │────────────────────┐                               │
│  └────────────────┘                    │                               │
│                                        ▼                                │
│                              ┌──────────────────┐                       │
│                              │  Lambda Function │                       │
│                              │  cost_ingestion  │                       │
│                              └────────┬─────────┘                       │
│                                       │                                 │
│                    ┌──────────────────┼──────────────────┐              │
│                    │                  │                  │              │
│                    ▼                  ▼                  ▼              │
│           ┌────────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│           │ Cost Explorer  │  │     EC2     │  │      RDS        │    │
│           │      API       │  │   Scanner   │  │    Scanner      │    │
│           └────────────────┘  └─────────────┘  └─────────────────┘    │
│                    │                  │                  │              │
│                    └──────────────────┼──────────────────┘              │
│                                       │                                 │
│                                       ▼                                 │
│                              ┌──────────────────┐                       │
│                              │   Data Layer     │                       │
│                              ├──────────────────┤                       │
│                              │ • Aggregate Data │                       │
│                              │ • Calculate Recs │                       │
│                              │ • Format Report  │                       │
│                              └────────┬─────────┘                       │
│                                       │                                 │
│                    ┌──────────────────┼──────────────────┐              │
│                    │                  │                  │              │
│                    ▼                  ▼                  ▼              │
│           ┌────────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│           │   S3 Bucket    │  │ CloudWatch  │  │   CloudWatch    │    │
│           │  (JSON Reports)│  │   Metrics   │  │      Logs       │    │
│           └────────────────┘  └─────────────┘  └─────────────────┘    │
│                    │                  │                                 │
└────────────────────┼──────────────────┼─────────────────────────────────┘
                     │                  │
                     ▼                  ▼
            ┌─────────────────┐  ┌──────────────┐
            │   Prometheus    │  │   Grafana    │
            │  (Pushgateway)  │  │  Dashboard   │
            └─────────────────┘  └──────────────┘
```

## Component Details

### 1. EventBridge Scheduler

**Purpose**: Triggers Lambda function on a schedule

**Configuration**:
- Schedule: Daily at 2 AM UTC (configurable)
- Expression: `cron(0 2 * * ? *)`
- Target: Lambda function

**Why this approach?**:
- Cost-effective (no EC2/containers needed)
- Reliable scheduling
- Serverless (no maintenance)

### 2. Lambda Function (`cost_ingestion`)

**Purpose**: Orchestrates data collection and processing

**Runtime**: Python 3.11
**Memory**: 256 MB (configurable)
**Timeout**: 5 minutes (300 seconds)

**Execution Flow**:
```python
1. Initialize clients (Cost Explorer, EC2, RDS, S3)
2. Define date range (last 30 days)
3. Query Cost Explorer API
   ├─ Get total costs
   ├─ Get costs by service
   └─ Calculate trends
4. Scan for idle resources
   ├─ Stopped EC2 instances
   ├─ Unattached EBS volumes
   ├─ Unassociated Elastic IPs
   ├─ Stopped RDS instances
   └─ Unused load balancers
5. Generate recommendations
6. Build comprehensive report
7. Write to S3 (partitioned by date)
8. Send metrics to CloudWatch
9. Return success/failure
```

**Key Modules**:

#### `handler.py`
- Main entry point
- Orchestrates workflow
- Error handling

#### `utils/cost_explorer.py`
- Cost Explorer API wrapper
- Methods:
  - `get_cost_and_usage()`: Total costs
  - `get_cost_by_service()`: Service breakdown
  - `get_cost_by_tags()`: Tag-based costs
  - `get_cost_trends()`: Period comparisons
  - `get_cost_forecast()`: Future predictions

#### `utils/resource_scanner.py`
- AWS resource scanning
- Methods:
  - `scan_stopped_ec2()`: Stopped instances
  - `scan_unattached_ebs()`: Orphaned volumes
  - `scan_unassociated_eips()`: Unused IPs
  - `scan_stopped_rds()`: Stopped databases
  - `scan_unused_load_balancers()`: Empty LBs

#### `utils/s3_writer.py`
- S3 report writing
- Methods:
  - `write_daily_report()`: Save daily data
  - `write_summary_report()`: Monthly aggregation
  - `read_latest_report()`: Fetch latest
  - `list_reports()`: List all reports

### 3. S3 Bucket

**Purpose**: Persistent storage for cost reports

**Structure**:
```
cost-optimizer-dev-123456789012/
├── reports/
│   ├── year=2025/
│   │   ├── month=01/
│   │   │   ├── day=15/
│   │   │   │   └── cost-report-2025-01-15.json
│   │   │   ├── day=16/
│   │   │   └── ...
│   │   └── month=02/
│   └── latest/
│       └── cost-report.json  (symlink to latest)
└── summaries/
    └── year=2025/
        └── month=01/
            └── monthly-summary-2025-01.json
```

**Features**:
- ✅ Versioning enabled (data protection)
- ✅ Encryption at rest (AES-256)
- ✅ Public access blocked
- ✅ Lifecycle policy:
  - Day 0-90: S3 Standard
  - Day 90+: Glacier Instant Retrieval
  - Day 365+: Deleted

**Why partitioning?**:
- Efficient queries (scan only needed dates)
- Better organization
- Supports future analytics (Athena/Glue)

### 4. IAM Role

**Purpose**: Least-privilege access for Lambda

**Permissions**:

| Policy | Purpose | Actions |
|--------|---------|---------|
| Cost Explorer | Read cost data | `ce:GetCostAndUsage`, `ce:GetCostForecast` |
| EC2 Read | Scan EC2 resources | `ec2:Describe*` |
| RDS Read | Scan RDS instances | `rds:DescribeDBInstances` |
| ELB Read | Scan load balancers | `elasticloadbalancing:Describe*` |
| S3 Write | Save reports | `s3:PutObject`, `s3:GetObject` |
| CloudWatch | Send metrics/logs | `cloudwatch:PutMetricData`, `logs:*` |

**Security Best Practices**:
- No wildcards in Resource ARNs (where possible)
- Separate policy per service
- No inline credentials
- Regular review/audit

### 5. CloudWatch

#### Logs
- **Log Group**: `/aws/lambda/cost-ingestion-dev`
- **Retention**: 7 days (configurable)
- **Format**: JSON structured logs

**Sample Log Entry**:
```json
{
  "timestamp": "2025-02-04T02:00:15.234Z",
  "level": "INFO",
  "message": "Cost ingestion completed",
  "total_cost": 245.32,
  "idle_resources": 7,
  "execution_time": 45.2
}
```

#### Metrics
- **Namespace**: `CostOptimizer`
- **Metrics**:
  - `TotalDailyCost`: Current day spend
  - `IdleResourcesCount`: Number of idle resources
  - `PotentialSavings`: Estimated monthly savings

#### Alarms
- **Lambda Errors**: Alert if function fails
- **Threshold**: > 1 error in 5 minutes
- **Action**: (Future) SNS notification

### 6. Report Structure

**Daily Report Schema**:
```json
{
  "timestamp": "2025-02-04T02:00:15.234Z",
  "date": "2025-02-04",
  "environment": "dev",
  "summary": {
    "total_cost": 245.32,
    "idle_resources_count": 7,
    "potential_savings": 85.50
  },
  "cost_data": {
    "total_cost": 245.32,
    "daily_costs": [...],
    "currency": "USD"
  },
  "service_breakdown": {
    "services": {
      "EC2": 123.45,
      "RDS": 67.89,
      "S3": 23.98
    }
  },
  "idle_resources": {
    "ec2_stopped": [
      {
        "id": "i-abc123",
        "type": "t3.medium",
        "name": "dev-server",
        "launch_time": "2025-01-15T10:30:00Z"
      }
    ],
    "ebs_unattached": [...],
    "eip_unassociated": [...],
    "rds_stopped": [...],
    "elb_unused": [...]
  },
  "trends": {
    "current_period": 245.32,
    "previous_period": 280.45,
    "delta_absolute": -35.13,
    "delta_percent": -12.53,
    "trend": "decreasing"
  },
  "recommendations": [
    {
      "priority": "HIGH",
      "category": "Idle Resources",
      "title": "Terminate 3 stopped EC2 instances",
      "impact": "~$90/month",
      "action": "Review and terminate unused instances"
    }
  ]
}
```

## Data Flow

### Ingestion Pipeline

```
Event Trigger
    ↓
Lambda Invocation
    ↓
Initialize Clients
    ↓
Query Cost Explorer API ──→ Get cost data (30 days)
    ↓
Scan EC2 Resources ────────→ Find stopped instances
    ↓
Scan EBS Volumes ──────────→ Find unattached volumes
    ↓
Scan Elastic IPs ──────────→ Find unassociated IPs
    ↓
Scan RDS Instances ────────→ Find stopped databases
    ↓
Scan Load Balancers ───────→ Find unused LBs
    ↓
Calculate Trends ──────────→ Compare with previous period
    ↓
Generate Recommendations ──→ Prioritize by impact
    ↓
Build Report ──────────────→ Aggregate all data
    ↓
Write to S3 ───────────────→ Partitioned by date
    ↓
Send CloudWatch Metrics ───→ For dashboards
    ↓
Return Response
```

## Design Decisions

### Why Lambda over EC2/ECS?

**Pros**:
- ✅ No server management
- ✅ Pay only for execution time
- ✅ Auto-scaling
- ✅ Built-in retry logic

**Cons**:
- ❌ 15-minute max execution
- ❌ Cold start latency
- ❌ Limited to AWS SDK

**Verdict**: Lambda is perfect for this use case (short, scheduled tasks)

### Why S3 over DynamoDB/RDS?

**Pros**:
- ✅ Cheapest storage ($0.023/GB)
- ✅ Unlimited scalability
- ✅ Native integration with analytics tools
- ✅ Lifecycle policies for archival

**Cons**:
- ❌ Not queryable without Athena
- ❌ No built-in indexing

**Verdict**: S3 is ideal for append-only historical data

### Why Python over Node.js/Go?

**Pros**:
- ✅ Rich AWS SDK (boto3)
- ✅ Easy JSON manipulation
- ✅ Pandas available for future analytics

**Cons**:
- ❌ Slightly slower cold starts than Go
- ❌ Larger package size

**Verdict**: Python provides best developer experience

## Scalability

### Current Limitations
- Single AWS account
- Daily execution only
- ~5 minutes max execution
- 30-day lookback window

### Future Improvements
1. **Multi-account support**: Use AWS Organizations
2. **Hourly execution**: Real-time cost tracking
3. **Custom date ranges**: Flexible reporting
4. **Advanced analytics**: Athena queries on S3 data
5. **Anomaly detection**: ML-based cost spikes

## Security Considerations

### Data Protection
- ✅ S3 encryption at rest
- ✅ S3 versioning for recovery
- ✅ Public access blocked
- ✅ IAM least privilege

### Network Security
- Lambda runs in AWS VPC (optional)
- No internet access required (AWS APIs via VPC endpoints)

### Audit Trail
- All actions logged in CloudWatch
- S3 access logs (optional, can enable)
- CloudTrail for API calls

## Monitoring & Alerts

### Current Monitoring
- Lambda execution logs
- CloudWatch metrics
- Error alarms

### Recommended Additions
1. SNS notifications on errors
2. Slack/email daily reports
3. Cost anomaly alerts (>20% spike)
4. SLA monitoring (execution time)

## Cost Breakdown

### Per Execution
- Lambda: $0.00 (free tier: 1M requests/month)
- Cost Explorer API: $0.01
- S3 PUT: $0.0001
- CloudWatch: $0.0001

**Total per execution**: ~$0.01

### Monthly
- 30 executions × $0.01 = $0.30
- S3 storage (1 GB): $0.02
- CloudWatch logs: $0.50

**Total monthly**: ~$0.82

### Annual
- $0.82 × 12 = **$9.84/year**

**ROI**: If you save just $10/month on idle resources, this pays for itself!
