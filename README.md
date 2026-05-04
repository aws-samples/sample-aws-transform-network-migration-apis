# AWS Transform for VMWare Network Migration API Samples - Python

Python examples demonstrating the AWS Transform and AWS Application Migration Service Network Migration APIs using boto3.

## Prerequisites

- Python 3.13 or higher
- boto3 library
- AWS credentials configured
- AWS Application Migration Service access

## Installation

### macOS/Linux

```bash
# (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt
```

### Windows

```bash
# (Optional) Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt
```

## Configuration

### Environment Variables

Set the following environment variables:

#### macOS/Linux

```bash
export AWS_REGION=us-east-1
export SOURCE_ACCOUNT_ID=123456789012  # Replace with your source AWS account ID
export TARGET_ACCOUNT_ID=123456789012  # Replace with your target AWS account ID
```

#### Windows (PowerShell)

```powershell
$env:AWS_REGION="us-east-1"
$env:SOURCE_ACCOUNT_ID="123456789012"  # Replace with your source AWS account ID
$env:TARGET_ACCOUNT_ID="123456789012"  # Replace with your target AWS account ID
```

#### FIPS Endpoints (Optional)

To use FIPS 140-3 validated endpoints, set the `ENDPOINT_URL` environment variable:

```bash
# macOS/Linux
export ENDPOINT_URL=https://mgn-fips.us-east-2.amazonaws.com

# Windows (PowerShell)
$env:ENDPOINT_URL="https://mgn-fips.us-east-2.amazonaws.com"
```

The FIPS endpoint format is `https://mgn-fips.<region>.amazonaws.com`. See [AWS FIPS endpoints](https://aws.amazon.com/compliance/fips/) for more information and available regions.

### Update S3 Configuration

Copy the example configuration file and update it with your values:

```bash
cp config.json.example config.json
```

Then edit `config.json` with your actual values:

```json
{
    "name": "my-network-migration",
    "description": "Sample network migration to AWS",
    "sourceEnvironment": "VSPHERE",
    "sourceBucket": "YOUR-SOURCE-BUCKET-NAME",
    "sourceKey": "YOUR-NETWORK-EXPORT-FILE-NAME",
    "sourceAccountId": "123456789012",
    "targetBucket": "YOUR-TARGET-BUCKET-NAME",
    "targetAccountId": "123456789012",
    "targetDeployment": "SINGLE_ACCOUNT",
    "topology": "ISOLATED_VPC",
    "inboundCidr": "10.0.0.0/16"
}
```

Replace the following placeholders:
- `YOUR-SOURCE-BUCKET-NAME` - S3 bucket containing your network export file
- `YOUR-NETWORK-EXPORT-FILE-NAME` - Name of your network export file in S3
- `YOUR-TARGET-BUCKET-NAME` - S3 bucket where generated code will be stored
- `sourceAccountId` / `targetAccountId` - Your AWS account IDs
- `sourceEnvironment` - One of: `NSX`, `VSPHERE`, `FORTIGATE_FIREWALL`, `PALO_ALTO_FIREWALL`, `CISCO_ACI`, `LOGICAL_MODEL`, `MODELIZE_IT`
- `topology` - `ISOLATED_VPC` or `HUB_AND_SPOKE` based on your architecture needs
- `inboundCidr` - For hub and spoke topology, three VPCs are created (inbound, outbound, and inspection). This parameter allows you to define the CIDR range for the inbound VPC.

## Usage

### Run Complete Workflow

```bash
python complete_workflow.py
```

### Run Individual Steps

```bash
# Step 1: Create network migration definition
python 01_create_definition.py

# Step 1a: List executions
python 01a_list_execution.py

# Step 2: Start network mapping
python 02_start_mapping.py <definitionID> <executionID>

# Step 2a: Monitor the progress of network mapping
python 02a_wait_mapping.py <definitionID> <executionID>

# Step 2b: List network segments
python 02b_list_segments.py <definitionID> <executionID>

# Step 3: Edit network segments
python 03_edit_segments.py <definitionID> <executionID>

# Step 4: Generate infrastructure code
python 04_generate_code.py <definitionID> <executionID>

# Step 4a: Monitor the progress of code generation
python 04a_wait_code_generation.py <definitionID> <executionID>

# Step 5: Deploy network infrastructure
python 05_deploy_network.py <definitionID> <executionID>

# Step 6: Run network analysis
python 06_run_analysis.py <definitionID> <executionID>

# Step 6a: Monitor the progress of network analysis
python 06a_wait_analysis.py <definitionID> <executionID>
```

## File Descriptions

- `01_create_definition.py` - Create network migration definition
- `01a_list_execution.py` - Displays the latest execution ID of a migration definition
- `02_start_mapping.py` - Start network mapping process
- `02a_wait_mapping.py` - Monitors progress of the network mapping process
- `02b_list_segments.py` - List discovered network segments
- `03_edit_segments.py` - Edit and customize network segments
- `04_generate_code.py` - Generate CloudFormation/Terraform/CDK templates
- `04a_wait_code_generation.py` - Monitors progress of code generation
- `05_deploy_network.py` - Deploy network infrastructure to AWS
- `05a_wait_deployment.py` - Monitors progress of network infrastructure deployment
- `06_run_analysis.py` - Run connectivity analysis
- `06a_wait_analysis.py` - Monitors progress of connectivity analysis, displays results
- `07_delete_all_network_definitions.py` - Optional, there is a limit to the number of definitions you can create per account, you may need to delete definitions during your testing
- `complete_workflow.py` - Orchestrate all steps together. Does not execute the delete network definitions step.

## Important Notes

### Demo Code
These examples are for demonstration purposes only. For production use:
- Implement proper job status polling instead of fixed delays
- Add comprehensive error handling and retry logic
- Validate inputs and check for resource existence
- Use configuration files instead of hardcoded values

### S3 Configuration
Before running, update the S3 bucket names in `01_create_definition.py`:
```python
's3Bucket': 'my-source-bucket',  # Change to your actual bucket
's3Key': 'network-export.json',   # Change to your actual file
```

### Network Export
You must export your source network configuration to S3 before running:
- VMware NSX: Use Import/Export for AWS utility
- VMware vSphere: Use RVTools export (CSV or XLSX)
- Upload the export file to your S3 source bucket

## Example Workflow

### macOS/Linux

```bash
# 1. Set environment variables
export AWS_REGION=us-east-1
export SOURCE_ACCOUNT_ID=123456789012
export TARGET_ACCOUNT_ID=123456789012

# 2. Create definition and save the ID
python3 01_create_definition.py
export DEFINITION_ID="nmd-5008e67475506303e"

# 3. Retrieve execution ID
python3 01a_list_execution.py
export EXECUTION_ID="5abd09ae-4622-4874-8ddc-702ea2c87667"

# 4. Start mapping
python3 02_start_mapping.py 

# 5. Wait for mapping to complete
python3 02a_wait_mapping.py 

# 6. List segments
python3 02b_list_segments.py 

# 7. Edit segments (optional)
python3 03_edit_segments.py 

# 8. Generate code
python3 04_generate_code.py

# 9. Wait for code generation
python3 04a_wait_code_generation.py

# 10. Deploy network
python3 05_deploy_network.py

# 11. Wait for network deployment
python3 05a_wait_deployment.py

# 12. Run analysis
python3 06_run_analysis.py

# 13. Wait for analysis
python3 06a_wait_analysis.py
```

### Windows (PowerShell)

```powershell
# 1. Set environment variables
$env:AWS_REGION="us-east-1"
$env:SOURCE_ACCOUNT_ID="123456789012"
$env:TARGET_ACCOUNT_ID="123456789012"

# 2. Create definition and save the ID
python .\01_create_definition.py 
$env:DEFINITION_ID="nmd-5008e67475506303e"

# 3. Retrieve execution ID
python .\01a_list_execution.py
$env:EXECUTION_ID="5abd09ae-4622-4874-8ddc-702ea2c87667"

# 4. Start mapping
python .\02_start_mapping.py 

# 5. Wait for mapping to complete 
python .\02a_wait_mapping.py 

# 6. List segments
python .\02b_list_segments.py

# 7. Edit segments (optional)
python .\03_edit_segments.py

# 8. Generate code
python .\04_generate_code.py

# 9. Wait for code generation
python .\04a_wait_code_generation.py

# 10. Deploy network
python .\05_deploy_network.py

# 11. Wait for network deployment
python .\05a_wait_deployment.py

# 12. Run analysis
python .\06_run_analysis.py

# 13. Run analysis
python .\06a_wait_analysis.py
```

## Troubleshooting

### Import Errors
If you get import errors in `complete_workflow.py`, ensure you're running from the examples-python directory:
```bash
cd examples-python
python complete_workflow.py
```

### AWS Credentials
Verify your AWS credentials are configured:
```bash
aws sts get-caller-identity
```

### S3 Access
Verify your S3 buckets and files exist:
```bash
aws s3 ls s3://my-source-bucket/
aws s3 ls s3://my-target-bucket/
```

## License

MIT
