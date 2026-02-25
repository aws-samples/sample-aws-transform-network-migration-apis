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
List Network Migration Executions

This script lists all executions for a given network migration definition.
It retrieves execution IDs that can be used in subsequent migration steps
(mapping, code generation, deployment, analysis).
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

def list_executions(definition_id):
    """
    List all network migration executions for a given definition.
    
    Args:
        definition_id (str): Network migration definition ID from step 1
        
    Returns:
        list: List of all execution objects
    """
    params = {
        'networkMigrationDefinitionID': definition_id,
        'maxResults': 50
    }

    try:
        all_executions = []
        next_token = None

        # Handle pagination
        while True:
            if next_token:
                params['nextToken'] = next_token

            response = client.list_network_migration_executions(**params)

            items = response.get('items', [])
            all_executions.extend(items)

            print(f"✓ Retrieved {len(items)} executions")

            next_token = response.get('nextToken')
            if not next_token:
                break

        print(f"\nTotal executions found: {len(all_executions)}")

        # Display execution details
        for index, execution in enumerate(all_executions, 1):
            print(f"\nExecution {index}:")
            print(f"  Execution ID: {execution.get('networkMigrationExecutionID')}")
            print(f"  Status: {execution.get('status', 'N/A')}")
            print(f"  Created: {execution.get('createdAt', 'N/A')}")

        return all_executions
    except Exception as error:
        print(f"Error listing executions: {str(error)}", file=sys.stderr)


def get_latest_execution_id(definition_id):
    """
    Get the most recent execution ID for a given definition.
    
    Args:
        definition_id (str): Network migration definition ID
        
    Returns:
        str: The latest execution ID, or None if no executions found
    """
    executions = list_executions(definition_id)

    if not executions:
        print("No executions found for this definition.")
        return None

    # Return the first (most recent) execution ID
    latest = executions[0]
    execution_id = latest.get('networkMigrationExecutionID')
    print(f"\n✓ Latest execution ID: {execution_id}")
    return execution_id


if __name__ == '__main__':
    # Run if executed directly
    definition_id = os.environ.get('DEFINITION_ID')
    
    if not definition_id:
        if len(sys.argv) < 2:
            print("Usage: python 01a_list_execution.py <definitionID>", file=sys.stderr)
            print("Or set DEFINITION_ID environment variable", file=sys.stderr)
            sys.exit(1)
        definition_id = sys.argv[1]

    try:
        executions = list_executions(definition_id)
        if executions:
            latest_id = executions[0].get('networkMigrationExecutionID')
            print(f"\nLatest Execution ID: {latest_id}")
            print("\nTo make it easier to run the rest of the Python scripts, you can set the execution ID as an environment variable:")
            print(f"  Windows (PowerShell): $env:EXECUTION_ID=\"{latest_id}\"")
            print(f"  Linux/Mac:            export EXECUTION_ID=\"{latest_id}\"")
    except Exception as error:
        print(f"Failed to list executions: {str(error)}", file=sys.stderr)
        sys.exit(1)
