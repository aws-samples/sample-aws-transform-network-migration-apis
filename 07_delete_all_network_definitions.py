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
Delete All Network Migration Definitions

This script lists all network migration definitions and optionally deletes them.
Use with caution - this will delete ALL definitions in the account/region.

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


def list_all_definitions():
    """
    List all network migration definitions with pagination support.
    
    Returns:
        list: List of all network migration definition summaries
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
        
        return all_definitions
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


def delete_all_definitions(confirm_delete=False):
    """
    List and optionally delete all network migration definitions.
    
    Args:
        confirm_delete (bool): If True, actually delete definitions. If False, dry run only.
    """
    print("Fetching all network migration definitions...")
    definitions = list_all_definitions()
    
    if not definitions:
        print("No network migration definitions found.")
        return
    
    print(f"\nFound {len(definitions)} definition(s):\n")
    
    # Display all definitions
    for index, definition in enumerate(definitions, 1):
        def_id = definition.get('networkMigrationDefinitionID', 'N/A')
        name = definition.get('name', 'N/A')
        source_env = definition.get('sourceEnvironment', 'N/A')
        print(f"{index}. {name}")
        print(f"   ID: {def_id}")
        print(f"   Source Environment: {source_env}")
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
    print("WARNING: You are about to delete ALL definitions listed above!")
    print("=" * 60)
    
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
        delete_all_definitions(confirm_delete=confirm_delete)
    except Exception as error:
        print(f"Failed to complete operation: {str(error)}", file=sys.stderr)
        sys.exit(1)
