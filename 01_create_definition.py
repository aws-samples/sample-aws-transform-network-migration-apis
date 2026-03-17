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
import json

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
    # Load configuration from config.json if available, otherwise use defaults
    config = {}
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        print(f"✓ Loaded configuration from {config_path}")
    else:
        print("⚠ No config.json found, using placeholder values. See README for setup instructions.")

    # Define migration parameters
    params = {
        'name': config.get('name', 'my-network-migration'),
        'description': config.get('description', 'Sample network migration to AWS'),
        'targetDeployment': config.get('targetDeployment', 'SINGLE_ACCOUNT'),
        'sourceConfigurations': [
            {
                'sourceEnvironment': config.get('sourceEnvironment', 'NSX'),
                'sourceS3Configuration': {
                    's3Bucket': config.get('sourceBucket', 'SOURCE-BUCKET-NAME'),
                    's3Key': config.get('sourceKey', 'NETWORK-EXPORT-FILE-NAME'),
                    's3BucketOwner': config.get('sourceAccountId', os.environ.get('SOURCE_ACCOUNT_ID', '123456789012'))
                }
            }
        ],
        'targetS3Configuration': {
            's3Bucket': config.get('targetBucket', 'TARGET-BUCKET-NAME'),
            's3BucketOwner': config.get('targetAccountId', os.environ.get('TARGET_ACCOUNT_ID', '123456789012'))
        },
        'targetNetwork': {
            'topology': config.get('topology', 'ISOLATED_VPC'),
            'inboundCidr': config.get('inboundCidr', '10.0.0.0/16')
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
