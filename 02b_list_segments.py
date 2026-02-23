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
List Network Migration Segments

This script retrieves all network segments discovered during the mapping process.
Segments include VPCs, subnets, route tables, and other network constructs.
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


def list_segments(definition_id, execution_id):
    """
    List all network migration segments with pagination support.
    
    Args:
        definition_id (str): Network migration definition ID from step 1
        execution_id (str): Network migration execution ID
        
    Returns:
        list: List of all network segments
    """
    params = {
        'networkMigrationDefinitionID': definition_id,
        'networkMigrationExecutionID': execution_id,
        'maxResults': 50
    }
    
    try:
        all_segments = []
        next_token = None
        
        # Handle pagination
        while True:
            if next_token:
                params['nextToken'] = next_token
            
            response = client.list_network_migration_mapper_segments(**params)
            
            items = response.get('items', [])
            all_segments.extend(items)
            
            print(f"✓ Retrieved {len(items)} segments")
            
            next_token = response.get('nextToken')
            if not next_token:
                break
        
        print(f"\nTotal segments found: {len(all_segments)}")
        
        # Display segment details
        for index, segment in enumerate(all_segments, 1):
            print(f"\nSegment {index}:")
            print(f"  ID: {segment.get('segmentID')}")
            print(f"  Name: {segment.get('name', 'N/A')}")
            print(f"  Type: {segment.get('segmentType')}")
            print(f"  Status: {segment.get('status')}")
            if 'cidr' in segment:
                print(f"  CIDR: {segment.get('cidr')}")
        
        return all_segments
    except Exception as error:
        print(f"Error listing segments: {str(error)}", file=sys.stderr)


if __name__ == '__main__':
    # Run if executed directly
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 02b_list_segments.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]
    
    try:
        segments = list_segments(definition_id, execution_id)
        print(f"\n✓ Listed {len(segments)} segments")
    except Exception as error:
        print(f"Failed to list segments: {str(error)}", file=sys.stderr)
        sys.exit(1)
