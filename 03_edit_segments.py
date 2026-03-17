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
Edit Network Migration Segments

This script demonstrates how to customize network segments and constructs:
- Modify CIDR blocks
- Update tags
"""

import boto3
import os
import sys
import json
import time

# Initialize MGN client
region = os.environ.get('AWS_REGION', 'us-east-1')
endpoint = os.environ.get('ENDPOINT_URL')
kwargs = {'region_name': region}
if endpoint:
    kwargs['endpoint_url'] = endpoint
client = boto3.client('mgn', **kwargs)

def edit_segments(definition_id, execution_id):
    """
    Edit network migration segments and update VPC CIDR blocks.
    
    Args:
        definition_id (str): Network migration definition ID
        execution_id (str): Network migration execution ID
        
    Returns:
        list: List of processed segments
    """
    try:
        list_response = client.list_network_migration_mapper_segments(
            networkMigrationDefinitionID=definition_id,
            networkMigrationExecutionID=execution_id
        )
        
        segments = list_response.get('items', [])
        print(f"✓ Found {len(segments)} segments")
        
        if len(segments) == 0:
            print("No segments to edit")
            return []
        
        cidr_mapping = {
            'segment-name-1': '10.10.0.0/24',    # (Optional) Update the segment-name-1 with the segment name to update CIDR block. Resizing CIDR is not supported
            'segment-name-2': '10.20.0.0/24',   # (Optional) Update the segment-name-2 with the segment name to update CIDR block. Resizing CIDR is not supported
        }
        
        # Update network segment tags
        for segment in segments:
            segment_id = segment['segmentID']
            print(f"\nUpdating segment {segment_id} tags")
            
            client.update_network_migration_mapper_segment(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id,
                segmentID=segment_id,
                scopeTags={'AWSTransform': 'Network-API-blog', 'ManagedBy': 'AWS-Transform-API'} # update the tags for network resources
            )
            print("✓ Segment tags updated")
        
        # Update VPC CIDR blocks
        constructs_to_update = []
        
        for segment in segments:
            segment_id = segment['segmentID']
            segment_name = segment.get('name', '')
            
            if segment_name not in cidr_mapping:
                continue
            
            constructs_response = client.list_network_migration_mapper_segment_constructs(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id,
                segmentID=segment_id
            )
            
            for construct in constructs_response.get('items', []):
                if construct.get('constructType') == 'AWS::EC2::VPC':
                    print(f"Updating {segment_name} -> {cidr_mapping[segment_name]}")
                    constructs_to_update.append({
                        'segmentID': segment_id,
                        'constructID': construct['constructID'],
                        'constructType': 'AWS::EC2::VPC',
                        'operation': {
                            'update': {
                                'properties': {
                                    'CidrBlock': cidr_mapping[segment_name]
                                }
                            }
                        }
                    })
        
        if constructs_to_update:
            print(f"\nUpdating {len(constructs_to_update)} VPC CIDR blocks")
            response = client.start_network_migration_mapping_update(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id,
                constructs=constructs_to_update
            )
            print(f"✓ Mapping update started. Job ID: {response['jobID']}")

            # Wait for the mapping update to complete
            job_id = response['jobID']
            print(f"Waiting for mapping update to complete...")
            for attempt in range(1, 61):
                updates = client.list_network_migration_mapping_updates(
                    networkMigrationDefinitionID=definition_id,
                    networkMigrationExecutionID=execution_id
                )
                for item in updates.get('items', []):
                    if item.get('jobID') == job_id:
                        status = item.get('status', 'UNKNOWN')
                        print(f"  Attempt {attempt}/60 — Job: {job_id} — Status: {status}")
                        if status == 'SUCCEEDED':
                            print("✓ Mapping update completed successfully")
                            break
                        elif status == 'FAILED':
                            raise RuntimeError(f"Mapping update failed: {item.get('statusDetails', 'No details')}")
                        break
                else:
                    print(f"  Attempt {attempt}/60 — Job not found yet")
                    time.sleep(10)
                    continue
                if status == 'SUCCEEDED':
                    break
                time.sleep(10)
            else:
                raise TimeoutError(f"Mapping update did not complete after 60 attempts")

        else:
            print("\nNo VPC constructs to update, using source mapped CIDR")

        return segments
    
    except Exception as error:
        print(f"Error editing segments: {str(error)}", file=sys.stderr)
        return []
    

if __name__ == '__main__':
    # Run if executed directly
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 03_edit_segments.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]
    
    try:
        segments = edit_segments(definition_id, execution_id)
        print(f"\n✓ Processed {len(segments)} segments")
    except Exception as error:
        print(f"Failed to edit segments: {str(error)}", file=sys.stderr)
        sys.exit(1)
