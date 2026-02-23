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
Start Network Migration Mapping

This script initiates the network mapping process that:
- Reads the source network configuration from S3
- Discovers network segments (VPCs, subnets, routing tables)
- Maps them to equivalent AWS constructs
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


def start_mapping(definition_id, execution_id):
    """
    Start network migration mapping process.
    
    Args:
        definition_id (str): Network migration definition ID from step 1
        execution_id (str): Unique execution ID (UUID) for tracking this migration
        
    Returns:
        str: Job ID for the mapping operation
    """
    params = {
        'networkMigrationDefinitionID': definition_id,
        'networkMigrationExecutionID': execution_id,
    }
    
    try:
        # Start the mapping job
        response = client.start_network_migration_mapping(**params)
        
        print("✓ Network Migration Mapping started")
        print(f"Job ID: {response['jobID']}")
        
        return response['jobID']
    except Exception as error:
        print(f"Error starting mapping: {str(error)}", file=sys.stderr)


if __name__ == '__main__':
    # Run if executed directly
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 02_start_mapping.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]
    
    try:
        job_id = start_mapping(definition_id, execution_id)
        print(f"\nJob ID: {job_id}")
    except Exception as error:
        print(f"Failed to start mapping: {str(error)}", file=sys.stderr)
        sys.exit(1)
