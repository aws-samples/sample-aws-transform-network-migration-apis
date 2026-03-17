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
- Adjust network properties
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


def edit_segments(definition_id, execution_id):
    """
    Edit network migration segments and constructs.

    Args:
        definition_id (str): Network migration definition ID
        execution_id (str): Network migration execution ID

    Returns:
        list: List of processed segments
    """
    try:
        # List segments
        list_response = client.list_network_migration_mapper_segments(
            networkMigrationDefinitionID=definition_id,
            networkMigrationExecutionID=execution_id
        )

        segments = list_response.get('items', [])
        print(f"✓ Found {len(segments)} segments")

        if len(segments) == 0:
            print("No segments to edit")
            return []

        # Collect all updates across segments for a single API call
        all_construct_updates = []
        all_segment_updates = []

        for segment_to_edit in segments:
            print(f"\nEditing constructs in segment: {segment_to_edit['segmentID']}")

            # List constructs in the segment
            constructs_response = client.list_network_migration_mapper_segment_constructs(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id,
                segmentID=segment_to_edit['segmentID']
            )

            constructs = constructs_response.get('items', [])
            print(f"✓ Found {len(constructs)} constructs")

            # Find VPC constructs and collect CIDR updates
            for construct in constructs:
                print(f"  - {construct['constructID']} ({construct.get('constructType', 'N/A')})")

                if construct.get('constructType', '').lower() != 'aws::ec2::vpc':
                    continue

                # Read the source CIDR to preserve the prefix length
                source_cidr = construct.get('properties', {}).get('CidrBlock', '')
                prefix = source_cidr.split('/')[-1] if '/' in source_cidr else '24'
                new_cidr = f'10.0.0.0/{prefix}'

                print(f"\n  Will update VPC construct: {construct['constructID']} ({source_cidr} -> {new_cidr})")
                all_construct_updates.append({
                    'segmentID': segment_to_edit['segmentID'],
                    'constructID': construct['constructID'],
                    'constructType': construct['constructType'],
                    'operation': {
                        'update': {
                            'properties': {
                                # The replacement CIDR prefix length must match
                                # the source VPC's prefix length
                                'CidrBlock': new_cidr
                            }
                        }
                    }
                })

            # Collect segment scope tags update
            all_segment_updates.append({
                'segmentID': segment_to_edit['segmentID'],
                'scopeTags': {
                    'Environment': 'Production',
                    'ManagedBy': 'NetworkMigration'
                }
            })

        # Submit all updates in a single API call to avoid job conflicts
        if all_construct_updates or all_segment_updates:
            update_params = {
                'networkMigrationDefinitionID': definition_id,
                'networkMigrationExecutionID': execution_id,
            }
            if all_construct_updates:
                update_params['constructs'] = all_construct_updates
            if all_segment_updates:
                update_params['segments'] = all_segment_updates

            client.start_network_migration_mapping_update(**update_params)
            print(f"\n✓ Submitted updates: {len(all_construct_updates)} construct(s), {len(all_segment_updates)} segment(s)")

        return segments
    except Exception as error:
        print(f"Error editing segments: {str(error)}", file=sys.stderr)


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