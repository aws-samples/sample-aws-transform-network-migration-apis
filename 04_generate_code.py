#
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


#!/usr/bin/env python3
"""
Generate Infrastructure Code

This script generates infrastructure as code templates for the network migration:
- CloudFormation templates
- Terraform configurations
- CDK code (optional)

Generated templates are automatically stored in the target S3 bucket that was
specified in the 'targetS3Configuration' when creating the definition (Step 1).

Example: If you specified 'my-target-bucket' in Step 1, the generated templates
will be uploaded to s3://my-target-bucket/ by the AWS MGN service.
"""

import boto3
import os
import sys

# Initialize MGN client
region = os.environ.get('AWS_REGION', 'us-east-1')
endpoint = os.environ.get('ENDPOINT_URL')
kwargs = {'region_name': region}
if endpoint:
    kwargs['endpoint_url'] = endpoint
client = boto3.client('mgn', **kwargs)


def generate_code(definition_id, execution_id):
    """
    Generate infrastructure as code for the network migration.
    
    Args:
        definition_id (str): Network migration definition ID from step 1
        execution_id (str): Network migration execution ID
        
    Returns:
        str: Job ID for the code generation operation
    """
    params = {
        'networkMigrationDefinitionID': definition_id,
        'networkMigrationExecutionID': execution_id,
        'codeGenerationOutputFormatTypes': ['CDK_L1', 'TERRAFORM']
    }
    
    try:
        # Start code generation
        response = client.start_network_migration_code_generation(**params)
        
        print("✓ Code generation started")
        print(f"Job ID: {response['jobID']}")
        
        return response['jobID']
    except Exception as error:
        print(f"Error generating code: {str(error)}", file=sys.stderr)


if __name__ == '__main__':
    # Run if executed directly
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 04_generate_code.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]

    try:
        job_id = generate_code(definition_id, execution_id)
        print(f"\nJob ID: {job_id}")
    except Exception as error:
        print(f"Failed to generate code: {str(error)}", file=sys.stderr)
        sys.exit(1)
