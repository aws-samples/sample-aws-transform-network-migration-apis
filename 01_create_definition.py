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
Create Network Migration Definition

This script creates a network migration definition that specifies:
- Source network location (S3 bucket with exported network config)
- Target deployment model (single or multi-account)
- Target network topology (isolated VPC or hub-and-spoke)
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


def create_definition():
    """
    Create a network migration definition.
    
    Returns:
        str: The network migration definition ID
    """
    # Define migration parameters
    # TODO: Update these values with your actual configuration
    params = {
        'name': 'my-network-migration',
        'description': 'Sample network migration from NSX to AWS',
        'targetDeployment': 'SINGLE_ACCOUNT',
        'sourceConfigurations': [
            {
                'sourceEnvironment': 'NSX',
                'sourceS3Configuration': {
                    's3Bucket': 'SOURCE-BUCKET_NAME',  # Replace with your S3 bucket containing network export
                    's3Key': 'NETWORK-EXPORT-FILE-NAME',  # Replace with your network export file name
                    's3BucketOwner': os.environ.get('SOURCE_ACCOUNT_ID', '123456789012')
                }
            }
        ],
        'targetS3Configuration': {
            's3Bucket': 'TARGET-BUCKET-NAME',  # Replace with your S3 bucket for generated code
            's3BucketOwner': os.environ.get('TARGET_ACCOUNT_ID', '123456789012')
        },
        'targetNetwork': {
            'topology': 'ISOLATED_VPC',  # Options: ISOLATED_VPC or HUB_AND_SPOKE
            'inboundCidr': '10.0.0.0/16'  # Replace with your desired CIDR range
        },
        'tags': {
            'AWSTransform': 'Network-API-blog',
            'ManagedBy': 'AWS-Transform-API'
        }
    }
    
    try:
        # Create the network migration definition
        response = client.create_network_migration_definition(**params)
        
        print("✓ Network Migration Definition created")
        print(f"Definition ID: {response['networkMigrationDefinitionID']}")
        
        return response['networkMigrationDefinitionID']
    except Exception as error:
        print(f"Error creating definition: {str(error)}", file=sys.stderr)


if __name__ == '__main__':
    # Run if executed directly
    try:
        definition_id = create_definition()
        print(f"\nDefinition ID: {definition_id}")
        print("\nTo make it easier to run the rest of the Python scripts, you can set the definition ID as an environment variable:")
        print(f"  Windows (PowerShell): $env:DEFINITION_ID=\"{definition_id}\"")
        print(f"  Linux/Mac:            export DEFINITION_ID=\"{definition_id}\"")
    except Exception as error:
        print(f"Failed to create definition: {str(error)}", file=sys.stderr)
        sys.exit(1)
