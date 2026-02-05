# 📘 Guida ai File Terraform

## 📁 Struttura Terraform

```
terraform/
├── providers.tf              # Configurazione provider AWS
├── variables.tf              # Variabili di input
├── s3.tf                     # Bucket S3 per i report
├── iam.tf                    # Ruoli e policy IAM
├── lambda.tf                 # Lambda function e EventBridge
├── outputs.tf                # Output values
└── terraform.tfvars.example  # Esempio configurazione
```

---

## 1️⃣ providers.tf

**Cosa fa**: Configura i provider Terraform necessari (AWS e Archive)

**Punti chiave**:
- Richiede Terraform >= 1.5.0
- AWS Provider v5.0
- Archive Provider (per creare lo zip della Lambda)
- **Default tags automatici** su tutte le risorse:
  - `Project`: multi-cloud-cost-optimizer
  - `ManagedBy`: terraform
  - `Environment`: dev/staging/prod
  - `Owner`: tuo nome

**Da modificare**:
```hcl
provider "aws" {
  region = var.aws_region  # Cambia in variables.tf o tfvars
}
```

---

## 2️⃣ variables.tf

**Cosa fa**: Definisce tutte le variabili configurabili del progetto

**Variabili principali**:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `aws_region` | eu-west-1 | Regione AWS |
| `environment` | dev | Ambiente (dev/staging/prod) |
| `owner` | nicola-bartolini | Proprietario infra |
| `lambda_runtime` | python3.11 | Versione Python |
| `lambda_memory` | 256 | MB di RAM per Lambda |
| `lambda_timeout` | 300 | Timeout in secondi (5 min) |
| `schedule_expression` | cron(0 2 * * ? *) | Schedule (ogni giorno 2 AM) |
| `s3_bucket_prefix` | cost-optimizer | Prefisso bucket S3 |
| `log_retention_days` | 7 | Giorni retention CloudWatch |

**Validazione inclusa**:
- Environment deve essere: dev, staging, o prod

**Da personalizzare**:
- `owner`: Inserisci il tuo nome
- `aws_region`: Se vuoi usare altra region
- `schedule_expression`: Se vuoi esecuzione diversa

---

## 3️⃣ s3.tf

**Cosa fa**: Crea e configura il bucket S3 per salvare i report di costo

**Risorse create**:

### 1. `aws_s3_bucket.cost_data`
- Nome: `cost-optimizer-dev-{AWS_ACCOUNT_ID}`
- Unico per account AWS

### 2. `aws_s3_bucket_versioning`
- **Versioning abilitato**: Protegge da cancellazioni accidentali
- Ogni modifica crea una nuova versione

### 3. `aws_s3_bucket_server_side_encryption_configuration`
- **Encryption AES-256**: Tutti i file criptati at-rest
- Gratuito (no KMS)

### 4. `aws_s3_bucket_public_access_block`
- **Blocca accesso pubblico**: Nessuno può accedere da internet
- Best practice security

### 5. `aws_s3_bucket_lifecycle_configuration`
- **Dopo 90 giorni**: Sposta in Glacier Instant Retrieval (risparmio 68%)
- **Dopo 365 giorni**: Cancella automaticamente

**Struttura dati salvata**:
```
s3://cost-optimizer-dev-123456789012/
├── reports/
│   ├── year=2025/
│   │   └── month=02/
│   │       └── day=04/
│   │           └── cost-report-2025-02-04.json
│   └── latest/
│       └── cost-report.json
```

---

## 4️⃣ iam.tf

**Cosa fa**: Crea il ruolo IAM per la Lambda con permessi minimi necessari

**Risorse create**:

### 1. `aws_iam_role.lambda_cost_ingestion`
Ruolo principale che la Lambda assume

### 2. Policy separate (principio least privilege):

| Policy | Permessi | Perché serve |
|--------|----------|--------------|
| `cost_explorer_access` | ce:GetCostAndUsage, ce:GetCostForecast | Leggere dati di costo |
| `ec2_read_access` | ec2:Describe* | Scansionare istanze EC2, volumi EBS, Elastic IP |
| `rds_read_access` | rds:DescribeDBInstances | Scansionare database RDS |
| `elb_read_access` | elasticloadbalancing:Describe* | Scansionare load balancer |
| `s3_write_access` | s3:PutObject, s3:GetObject | Salvare report in S3 |
| `cloudwatch_metrics` | cloudwatch:PutMetricData | Inviare metriche custom |

### 3. `AWSLambdaBasicExecutionRole` (managed policy)
- CloudWatch Logs (scrivere log)
- Networking base

**Sicurezza**:
- ✅ Nessun wildcard inutile
- ✅ Policy separate per service
- ✅ Solo azioni read (tranne S3 write)
- ✅ No admin permissions

---

## 5️⃣ lambda.tf

**Cosa fa**: Crea la Lambda function, lo scheduler, e il monitoring

**Risorse create**:

### 1. `data.archive_file.lambda_package`
- Crea automaticamente lo ZIP con il codice Python
- Esclude: `__pycache__`, `*.pyc`, `tests/`
- Path: `lambda/cost_ingestion/`

### 2. `aws_lambda_function.cost_ingestion`
Lambda function principale:
```hcl
function_name: cost-ingestion-dev
handler: handler.lambda_handler
runtime: python3.11
memory: 256 MB
timeout: 300 secondi (5 minuti)
```

**Environment variables**:
- `COST_DATA_BUCKET`: Nome bucket S3 (auto)
- `ENVIRONMENT`: dev/staging/prod
- `LOG_LEVEL`: INFO

### 3. `aws_cloudwatch_log_group.lambda_logs`
- Nome: `/aws/lambda/cost-ingestion-dev`
- Retention: 7 giorni (configurable)

### 4. `aws_cloudwatch_event_rule.lambda_schedule`
**EventBridge Scheduler**:
- Schedule: `cron(0 2 * * ? *)` = Ogni giorno 2 AM UTC
- Trigger automatico della Lambda

### 5. `aws_cloudwatch_event_target.lambda`
Collega EventBridge → Lambda

### 6. `aws_lambda_permission.allow_eventbridge`
Permesso per EventBridge di invocare la Lambda

### 7. `aws_cloudwatch_metric_alarm.lambda_errors`
**Allarme CloudWatch**:
- Scatta se Lambda va in errore
- Threshold: > 1 errore in 5 minuti
- (Puoi aggiungere SNS notification dopo)

---

## 6️⃣ outputs.tf

**Cosa fa**: Espone informazioni utili dopo il deploy

**Output disponibili**:

```bash
terraform output
```

Mostra:
- `lambda_function_name`: Nome Lambda (per invoke)
- `lambda_function_arn`: ARN Lambda
- `s3_bucket_name`: Nome bucket (per access)
- `s3_bucket_arn`: ARN bucket
- `lambda_role_arn`: ARN ruolo IAM
- `schedule_expression`: Schedule configurato
- `cloudwatch_log_group`: Log group path
- `environment`: Ambiente deployed
- `aws_region`: Region AWS

**Uso pratico**:
```bash
# Get bucket name
BUCKET=$(terraform output -raw s3_bucket_name)

# List reports
aws s3 ls s3://$BUCKET/reports/latest/
```

---

## 7️⃣ terraform.tfvars.example

**Cosa fa**: Template di configurazione da copiare

**Come usare**:
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Modifica con i tuoi valori
```

**Valori da personalizzare**:
```hcl
owner = "nicola-bartolini"  # ← TUO NOME

# Opzionale, cambia solo se necessario:
aws_region = "eu-west-1"    # O us-east-1, etc.
lambda_memory = 256         # O 512 se più dati
schedule_expression = "cron(0 2 * * ? *)"  # O altro orario
```

**⚠️ IMPORTANTE**: 
- `terraform.tfvars` è in `.gitignore`
- NON committare credenziali o info sensibili

---

## 🚀 Workflow di Deploy

### 1. Prima volta (setup):
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Modifica terraform.tfvars

terraform init
```

### 2. Preview delle modifiche:
```bash
terraform plan
```

### 3. Deploy:
```bash
terraform apply
# Type: yes
```

### 4. Verifica output:
```bash
terraform output
```

### 5. Test manuale:
```bash
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{}' \
  response.json

cat response.json | jq .
```

---

## 💰 Costo Mensile delle Risorse

| Risorsa | Costo Mensile |
|---------|---------------|
| Lambda (30 invocations, 60s avg, 256MB) | $0.00 (free tier) |
| S3 Storage (< 1GB) | $0.02 |
| S3 Requests (~100/month) | $0.01 |
| CloudWatch Logs (1GB) | $0.50 |
| Cost Explorer API (30 calls) | $0.30 |
| EventBridge | $0.00 (free) |
| **TOTALE** | **~$0.83/month** |

---

## 🔧 Modifiche Comuni

### Aumentare timeout Lambda:
```hcl
# In variables.tf o terraform.tfvars
lambda_timeout = 600  # 10 minuti
```

### Cambiare schedule (es. ogni ora):
```hcl
schedule_expression = "rate(1 hour)"
# O cron specifico:
schedule_expression = "cron(0 * * * ? *)"  # Ogni ora
```

### Aumentare retention log (da 7 a 30 giorni):
```hcl
log_retention_days = 30
```

### Ridurre memoria Lambda (risparmio):
```hcl
lambda_memory = 128  # 128 MB invece di 256
```

---

## 🧹 Cleanup (Distruggere tutto)

```bash
cd terraform
terraform destroy
# Type: yes

# Questo cancellerà:
# - Lambda function
# - S3 bucket (e TUTTI i dati!)
# - IAM roles
# - CloudWatch logs
# - EventBridge rules
```

⚠️ **WARNING**: I dati in S3 verranno persi!

---

## 🆘 Troubleshooting Terraform

### Errore: "Backend initialization required"
```bash
terraform init
```

### Errore: "Error creating S3 bucket: BucketAlreadyExists"
Il nome bucket deve essere globalmente unico. Cambia `s3_bucket_prefix`.

### Errore: "AccessDenied" durante apply
Verifica permessi AWS CLI:
```bash
aws sts get-caller-identity
```

Serve IAM user con permessi per creare Lambda, S3, IAM roles.

### Errore: Lambda package troppo grande
```bash
cd lambda/cost_ingestion
pip install -r requirements.txt -t ./package
# Rimuovi packages non necessari
```

---

## ✅ Best Practices Implementate

- ✅ **State management**: Terraform state locale (upgradeabile a S3 remote)
- ✅ **Modularità**: Ogni servizio in file separato
- ✅ **Variabili**: Tutto parametrizzato
- ✅ **Tags**: Auto-tagging su tutte le risorse
- ✅ **Encryption**: S3 encrypted by default
- ✅ **Least Privilege**: IAM policies separate e minime
- ✅ **Lifecycle**: S3 lifecycle per cost optimization
- ✅ **Monitoring**: CloudWatch logs e alarms
- ✅ **Documentation**: Commenti in ogni file

---

## 📚 Prossimi Step

1. ✅ Deploy infrastructure → `terraform apply`
2. ⏳ Aggiungi remote backend S3 (per team)
3. ⏳ Aggiungi SNS topic per allarmi
4. ⏳ Multi-account con AWS Organizations
5. ⏳ Terraform modules riutilizzabili

---

**Hai tutto il necessario per deployare! 🚀**

Prossimo comando da eseguire:
```bash
cd terraform
terraform init
terraform plan
```
