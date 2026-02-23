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
Wait for Network Migration Mapping to complete.

Polls list-network-migration-mappings until status is SUCCEEDED.
"""

import boto3
import os
import sys
import time

region = os.environ.get('AWS_REGION', 'us-east-1')
endpoint = os.environ.get('ENDPOINT_URL')
kwargs = {'region_name': region}
if endpoint:
    kwargs['endpoint_url'] = endpoint
client = boto3.client('mgn', **kwargs)


def wait_for_mapping(definition_id, execution_id, poll_interval=10, max_attempts=60):
    """
    Poll mapping status until SUCCEEDED or failure.

    Args:
        definition_id (str): Network migration definition ID
        execution_id (str): Network migration execution ID
        poll_interval (int): Seconds between polls (default 10)
        max_attempts (int): Max polling attempts (default 60)

    Returns:
        list: The mapping items once SUCCEEDED
    """
    print(f"Waiting for mapping to complete (polling every {poll_interval}s)...")

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.list_network_migration_mappings(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id
            )

            items = response.get('items', [])

            if not items:
                print(f"  Attempt {attempt}/{max_attempts} — No mapping jobs found yet")
                time.sleep(poll_interval)
                continue

            # Check the latest job status
            latest = items[0]
            status = latest.get('status', 'UNKNOWN')
            job_id = latest.get('jobID', 'N/A')
            print(f"  Attempt {attempt}/{max_attempts} — Job: {job_id} — Status: {status}")

            if status == 'SUCCEEDED':
                print("✓ Mapping completed successfully")
                return items
            elif status == 'FAILED':
                details = latest.get('statusDetails', 'No details')
                raise RuntimeError(f"Mapping failed: {details}")

            time.sleep(poll_interval)

        except RuntimeError:
            raise
        except Exception as error:
            print(f"  Attempt {attempt}/{max_attempts} — Error: {str(error)}")
            time.sleep(poll_interval)

    raise TimeoutError(f"Mapping did not complete after {max_attempts} attempts")


if __name__ == '__main__':
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 02a_wait_mapping.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]
    
    try:
        wait_for_mapping(definition_id, execution_id)
    except Exception as error:
        print(f"Failed to wait for mapping: {str(error)}", file=sys.stderr)
        sys.exit(1)