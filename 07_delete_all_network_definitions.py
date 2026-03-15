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
Delete Network Migration Definitions by Tags

This script lists network migration definitions filtered by specific tags and optionally deletes them.
Only definitions with matching tags will be deleted.

Usage:
    python 07_delete_all_network_definitions.py              # List only (dry run)
    python 07_delete_all_network_definitions.py --confirm    # List and delete
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

# Tags to filter by - only definitions with ALL these tags will be deleted
TAG_FILTER = {
    'AWSTransform': 'Network-API-blog',
    'ManagedBy': 'AWS-Transform-API'
}


def list_definitions_by_tags(tag_filter):
    """
    List network migration definitions filtered by tags (client-side filtering).
    
    Args:
        tag_filter (dict): Dictionary of tags to filter by
    
    Returns:
        list: List of definitions matching all specified tags
    """
    params = {
        'maxResults': 50
        }
    
    try:
        all_definitions = []
        next_token = None
        
        # Handle pagination
        while True:
            if next_token:
                params['nextToken'] = next_token
            
            response = client.list_network_migration_definitions(**params)
            
            items = response.get('items', [])
            all_definitions.extend(items)
            
            next_token = response.get('nextToken')
            if not next_token:
                break
        
        # Client-side tag filtering - match ALL specified tags
        filtered_definitions = [
            d for d in all_definitions
            if all(d.get('tags', {}).get(k) == v for k, v in tag_filter.items())
        ]
        
        return filtered_definitions
    except Exception as error:
        print(f"Error listing definitions: {str(error)}", file=sys.stderr)
        raise


def delete_definition(definition_id):
    """
    Delete a single network migration definition.
    
    Args:
        definition_id (str): Network migration definition ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client.delete_network_migration_definition(
            networkMigrationDefinitionID=definition_id
        )
        return True
    except Exception as error:
        print(f"  Error deleting {definition_id}: {str(error)}", file=sys.stderr)
        return False


def delete_definitions_by_tags(tag_filter, confirm_delete=False):
    """
    List and optionally delete network migration definitions matching specified tags.
    
    Args:
        tag_filter (dict): Dictionary of tags to filter by
        confirm_delete (bool): If True, actually delete definitions. If False, dry run only.
    """
    print("Fetching network migration definitions...")
    print(f"Filtering by tags: {tag_filter}\n")
    
    definitions = list_definitions_by_tags(tag_filter)
    
    if not definitions:
        print("No network migration definitions found matching the specified tags.")
        return
    
    print(f"Found {len(definitions)} definition(s) matching tags:\n")
    
    # Display all matching definitions
    for index, definition in enumerate(definitions, 1):
        def_id = definition.get('networkMigrationDefinitionID', 'N/A')
        name = definition.get('name', 'N/A')
        source_env = definition.get('sourceEnvironment', 'N/A')
        tags = definition.get('tags', {})
        print(f"{index}. {name}")
        print(f"   ID: {def_id}")
        print(f"   Source Environment: {source_env}")
        print(f"   Tags: {tags}")
        print()
    
    if not confirm_delete:
        print("=" * 60)
        print("DRY RUN MODE - No definitions were deleted.")
        print("To actually delete these definitions, run:")
        print(f"  python {os.path.basename(__file__)} --confirm")
        print("=" * 60)
        return
    
    # Confirm deletion
    print("=" * 60)
    print("⚠️  WARNING: You are about to delete ALL definitions listed above!")
    print("=" * 60)
    confirm = input("Do you want to proceed with deletion? (yes/no): ").strip().lower()
    if confirm not in ('yes', 'y'):
        print("Deletion cancelled by user.")
        return
    
    # Perform deletions
    print("\nDeleting definitions...")
    success_count = 0
    fail_count = 0
    
    for definition in definitions:
        def_id = definition.get('networkMigrationDefinitionID')
        name = definition.get('name', 'N/A')
        
        print(f"Deleting: {name} ({def_id})...", end=" ")
        
        if delete_definition(def_id):
            print("✓ Deleted")
            success_count += 1
        else:
            print("✗ Failed")
            fail_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"Deletion complete:")
    print(f"  ✓ Successfully deleted: {success_count}")
    if fail_count > 0:
        print(f"  ✗ Failed to delete: {fail_count}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    # Check for --confirm flag
    confirm_delete = '--confirm' in sys.argv or '-c' in sys.argv
    
    try:
        delete_definitions_by_tags(TAG_FILTER, confirm_delete=confirm_delete)
    except Exception as error:
        print(f"Failed to complete operation: {str(error)}", file=sys.stderr)
        sys.exit(1)
