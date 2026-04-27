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

This script demonstrates how to customize network segments and constructs.

VPC operations:
- Change IP address: Change the base IP of a VPC CIDR (subnets shift automatically)
- Delete: Permanently remove a VPC from the configuration
- Exclude/Include: Temporarily remove or re-add a VPC for phased migration
- Merge: Combine two VPCs into one (target absorbs source)
- Rename: Change a VPC name
- Resize: Change the prefix length of a VPC CIDR (expand or reduce IP range)
- Split: Divide a VPC into two based on CIDR boundaries

Subnet operations:
- Change IP address: Change the base IP of a subnet CIDR
- Delete: Remove a subnet without affecting the parent VPC
- Resize: Change the prefix length of a subnet CIDR
"""

import boto3
import os
import sys
import time

# Initialize MGN client
region = os.environ.get('AWS_REGION', 'us-east-1')
endpoint = os.environ.get('ENDPOINT_URL')
kwargs = {'region_name': region}
if endpoint:
    kwargs['endpoint_url'] = endpoint
client = boto3.client('mgn', **kwargs)

def wait_for_mapping_update(client, definition_id, execution_id, job_id, max_attempts=60):
    """Wait for a mapping update job to complete."""
    print(f"Waiting for mapping update to complete...")
    for attempt in range(1, max_attempts + 1):
        updates = client.list_network_migration_mapping_updates(
            networkMigrationDefinitionID=definition_id,
            networkMigrationExecutionID=execution_id
        )
        for item in updates.get('items', []):
            if item.get('jobID') == job_id:
                status = item.get('status', 'UNKNOWN')
                print(f"  Attempt {attempt}/{max_attempts} — Job: {job_id} — Status: {status}")
                if status == 'SUCCEEDED':
                    print("✓ Mapping update completed successfully")
                    return True
                elif status == 'FAILED':
                    raise RuntimeError(f"Mapping update failed: {item.get('statusDetails', 'No details')}")
                break
        else:
            print(f"  Attempt {attempt}/{max_attempts} — Job not found yet")
        time.sleep(10)
    raise TimeoutError(f"Mapping update did not complete after {max_attempts} attempts")


def submit_mapping_update(client, definition_id, execution_id, constructs, description=""):
    """Submit a mapping update and wait for completion."""
    if not constructs:
        print(f"No constructs to {description}")
        return
    print(f"\n{description}: {len(constructs)} construct(s)")
    response = client.start_network_migration_mapping_update(
        networkMigrationDefinitionID=definition_id,
        networkMigrationExecutionID=execution_id,
        constructs=constructs
    )
    print(f"✓ Mapping update started. Job ID: {response['jobID']}")
    wait_for_mapping_update(client, definition_id, execution_id, response['jobID'])


# ============================================================
# VPC Operations
# ============================================================

def example_delete_vpc(definition_id, execution_id, segment_id, construct_id):
    """
    Delete a VPC from the configuration.
    Use for obsolete network segments that should not migrate to AWS.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {'delete': {}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Deleting VPC")


def example_exclude_vpc(definition_id, execution_id, segment_id, construct_id):
    """
    Exclude a VPC from the migration.
    Excluded VPCs are not deployed but can be re-included later.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {'update': {'excluded': True}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Excluding VPC")


def example_include_vpc(definition_id, execution_id, segment_id, construct_id):
    """
    Re-include a previously excluded VPC in the migration.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {'update': {'excluded': False}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Including VPC")


def example_merge_vpcs(definition_id, execution_id,
                       target_segment_id, target_construct_id,
                       source_segment_id, source_construct_id):
    """
    Merge two VPCs into one. The target VPC keeps its identity and absorbs
    all subnets from the source VPC. The target VPC's CIDR expands to the
    smallest range containing both original CIDRs.

    Requirements:
    - Subnet CIDRs must not overlap between the two VPCs.
    - The merged CIDR must not exceed /16.
    - For multi-account deployments, both VPCs must be in the same account.
    """
    constructs = [{
        'segmentID': target_segment_id,
        'constructID': target_construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {
            'merge': {
                'mergeConstructs': [{
                    'segmentID': source_segment_id,
                    'constructID': source_construct_id
                }]
            }
        }
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Merging VPCs")


def example_change_vpc_ip(definition_id, execution_id, segment_id, construct_id, new_cidr):
    """
    Change the base IP address of a VPC CIDR while keeping the same prefix length.
    All subnet CIDRs are automatically translated by the same offset.
    Security group rules that exactly match the old VPC CIDR are updated automatically.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {'update': {'properties': {'CidrBlock': new_cidr}}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Changing VPC IP address")


def example_rename_vpc(definition_id, execution_id, segment_id, construct_id, new_name):
    """
    Rename a VPC to align with your organization's naming conventions.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {'update': {'name': new_name}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Renaming VPC")


def example_resize_vpc(definition_id, execution_id, segment_id, construct_id, new_cidr):
    """
    Resize a VPC CIDR by changing the prefix length (e.g., /20 to /16 or /16 to /20).

    Prefix length decrease (more IPs): Subnets still fit, no changes needed.
    Prefix length increase (fewer IPs): Subnets outside the new range must be resized first.

    Requirements:
    - New CIDR must be between /16 and /28.
    - Must not overlap with other VPCs (Hub and Spoke topology).
    - When reducing, all existing subnets must fit within the new CIDR.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {'update': {'properties': {'CidrBlock': new_cidr}}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Resizing VPC")


def example_split_vpc(definition_id, execution_id, segment_id, construct_id,
                      cidr_block_1, cidr_block_2):
    """
    Split a VPC into two VPCs based on CIDR boundaries.
    Subnets are assigned to the new VPC whose CIDR contains them.
    Security groups are cloned to both new VPCs.

    Requirements:
    - Exactly two non-overlapping CIDR ranges.
    - Each CIDR must be between /16 and /28.
    - Every subnet must fit in exactly one of the two CIDRs.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::VPC',
        'operation': {
            'split': {
                'splitConstructs': [
                    {'cidrBlock': cidr_block_1},
                    {'cidrBlock': cidr_block_2}
                ]
            }
        }
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Splitting VPC")


# ============================================================
# Subnet Operations
# ============================================================

def example_delete_subnet(definition_id, execution_id, segment_id, construct_id):
    """
    Delete a subnet from the configuration without affecting the parent VPC.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::Subnet',
        'operation': {'delete': {}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Deleting subnet")


def example_change_subnet_ip(definition_id, execution_id, segment_id, construct_id, new_cidr):
    """
    Change the base IP address of a subnet CIDR while keeping the same prefix length.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::Subnet',
        'operation': {'update': {'properties': {'CidrBlock': new_cidr}}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Changing subnet IP address")


def example_resize_subnet(definition_id, execution_id, segment_id, construct_id, new_cidr):
    """
    Resize a subnet CIDR to expand or reduce the IP address range.

    Requirements:
    - New CIDR must be between /16 and /28.
    - Must not overlap with other subnets in the same VPC.
    - Must be within the parent VPC CIDR.
    """
    constructs = [{
        'segmentID': segment_id,
        'constructID': construct_id,
        'constructType': 'AWS::EC2::Subnet',
        'operation': {'update': {'properties': {'CidrBlock': new_cidr}}}
    }]
    submit_mapping_update(client, definition_id, execution_id, constructs,
                          description="Resizing subnet")


def edit_segments(definition_id, execution_id):
    """
    Edit network migration segments.
    
    Demonstrates:
    - Updating segment tags
    - Changing VPC CIDR blocks using example_change_vpc_ip
    
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
            'segment-name-1': '10.10.0.0/24',    # (Optional) Update with the segment name and desired CIDR
            'segment-name-2': '10.20.0.0/24',    # (Optional) Update with the segment name and desired CIDR
        }
        
        # Update network segment tags
        for segment in segments:
            segment_id = segment['segmentID']
            print(f"\nUpdating segment {segment_id} tags")
            
            client.update_network_migration_mapper_segment(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id,
                segmentID=segment_id,
                scopeTags={'AWSTransform': 'Network-API-blog', 'ManagedBy': 'AWS-Transform-API'}
            )
            print("✓ Segment tags updated")
        
        # Change VPC IP addresses for segments in cidr_mapping
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
                    print(f"Changing {segment_name} VPC IP -> {cidr_mapping[segment_name]}")
                    example_change_vpc_ip(
                        definition_id, execution_id,
                        segment_id, construct['constructID'],
                        cidr_mapping[segment_name]
                    )

        # --- VPC Operations ---

        # Delete a VPC:
        # example_delete_vpc(definition_id, execution_id, '<segment-id>', '<vpc-construct-id>')

        # Exclude a VPC from migration:
        # example_exclude_vpc(definition_id, execution_id, '<segment-id>', '<vpc-construct-id>')

        # Re-include a previously excluded VPC:
        # example_include_vpc(definition_id, execution_id, '<segment-id>', '<vpc-construct-id>')

        # Merge two VPCs (target absorbs source):
        # example_merge_vpcs(definition_id, execution_id,
        #     target_segment_id='<target-segment-id>', target_construct_id='<target-vpc-id>',
        #     source_segment_id='<source-segment-id>', source_construct_id='<source-vpc-id>')

        # Rename a VPC:
        # example_rename_vpc(definition_id, execution_id, '<segment-id>', '<vpc-construct-id>', 'new-vpc-name')

        # Resize a VPC (change prefix length):
        # example_resize_vpc(definition_id, execution_id, '<segment-id>', '<vpc-construct-id>', '10.0.0.0/16')

        # Split a VPC into two:
        # example_split_vpc(definition_id, execution_id, '<segment-id>', '<vpc-construct-id>',
        #     cidr_block_1='10.0.0.0/17', cidr_block_2='10.0.128.0/17')

        # --- Subnet Operations ---

        # Delete a subnet:
        # example_delete_subnet(definition_id, execution_id, '<segment-id>', '<subnet-construct-id>')

        # Change subnet IP address:
        # example_change_subnet_ip(definition_id, execution_id, '<segment-id>', '<subnet-construct-id>', '10.0.2.0/24')

        # Resize a subnet:
        # example_resize_subnet(definition_id, execution_id, '<segment-id>', '<subnet-construct-id>', '10.0.1.0/23')

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
