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
Run Network Migration Analysis

This script runs analysis on the deployed network infrastructure:
- Uses VPC Reachability Analyzer to verify connectivity
- Validates routing configurations
- Checks security group rules
- Identifies potential connectivity issues
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


def run_analysis(definition_id, execution_id):
    """
    Run network migration analysis.
    
    Args:
        definition_id (str): Network migration definition ID from step 1
        execution_id (str): Network migration execution ID
        
    Returns:
        str: Job ID for the analysis operation
    """
    params = {
        'networkMigrationDefinitionID': definition_id,
        'networkMigrationExecutionID': execution_id
    }
    
    try:
        # Start network analysis
        response = client.start_network_migration_analysis(**params)
        
        print("✓ Network migration analysis started")
        print(f"Job ID: {response['jobID']}")
        
        return response['jobID']
    except Exception as error:
        print(f"Error running analysis: {str(error)}", file=sys.stderr)


if __name__ == '__main__':
    # Run if executed directly
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 06_run_analysis.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]
    
    try:
        job_id = run_analysis(definition_id,execution_id)
        print(f"\nJob ID: {job_id}")
    except Exception as error:
        print(f"Failed to run analysis: {str(error)}", file=sys.stderr)
        sys.exit(1)
