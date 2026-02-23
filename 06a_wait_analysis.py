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
Wait for Network Migration Analysis to complete.

Polls list-network-migration-analyses until status is SUCCEEDED.
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


def display_analysis_results(definition_id, execution_id):
    """
    Fetch and display network migration analysis results.
    
    Args:
        definition_id (str): Network migration definition ID
        execution_id (str): Network migration execution ID
    """
    try:
        print("\n=== Analysis Results ===")
        
        params = {
            'networkMigrationDefinitionID': definition_id,
            'networkMigrationExecutionID': execution_id,
            'maxResults': 50
        }
        
        all_results = []
        next_token = None
        
        # Handle pagination
        while True:
            if next_token:
                params['nextToken'] = next_token
            
            response = client.list_network_migration_analysis_results(**params)
            
            items = response.get('items', [])
            all_results.extend(items)
            
            next_token = response.get('nextToken')
            if not next_token:
                break
        
        if not all_results:
            print("No analysis results found.")
            return
        
        print(f"Total analysis results: {len(all_results)}\n")
        
        # Group results by status
        succeeded = [r for r in all_results if r.get('status') == 'SUCCEEDED']
        failed = [r for r in all_results if r.get('status') == 'FAILED']
        other = [r for r in all_results if r.get('status') not in ['SUCCEEDED', 'FAILED']]
        
        print(f"✓ Succeeded: {len(succeeded)}")
        print(f"✗ Failed: {len(failed)}")
        if other:
            print(f"○ Other: {len(other)}")
        
        # Display details for each result
        for index, result in enumerate(all_results, 1):
            print(f"\n--- Result {index} ---")
            print(f"  Analyzer Type: {result.get('analyzerType', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")
            
            source = result.get('source', {})
            if source:
                print(f"  Source:")
                if 'vpcID' in source:
                    print(f"    VPC ID: {source.get('vpcID')}")
                if 'subnetID' in source:
                    print(f"    Subnet ID: {source.get('subnetID')}")
            
            target = result.get('target', {})
            if target:
                print(f"  Target:")
                if 'vpcID' in target:
                    print(f"    VPC ID: {target.get('vpcID')}")
                if 'subnetID' in target:
                    print(f"    Subnet ID: {target.get('subnetID')}")
            
            analysis_result = result.get('analysisResult')
            if analysis_result:
                print(f"  Analysis Result: {analysis_result}")
        
    except Exception as error:
        print(f"\nWarning: Could not fetch analysis results: {str(error)}", file=sys.stderr)


def wait_for_analysis(definition_id, execution_id, poll_interval=10, max_attempts=60):
    """
    Poll analysis status until SUCCEEDED or failure.

    Args:
        definition_id (str): Network migration definition ID
        execution_id (str): Network migration execution ID
        poll_interval (int): Seconds between polls (default 10)
        max_attempts (int): Max polling attempts (default 60)

    Returns:
        list: The analysis items once SUCCEEDED
    """
    print(f"Waiting for analysis to complete (polling every {poll_interval}s)...")

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.list_network_migration_analyses(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id
            )

            items = response.get('items', [])

            if not items:
                print(f"  Attempt {attempt}/{max_attempts} — No analysis jobs found yet")
                time.sleep(poll_interval)
                continue

            latest = items[0]
            status = latest.get('status', 'UNKNOWN')
            job_id = latest.get('jobID', 'N/A')
            print(f"  Attempt {attempt}/{max_attempts} — Job: {job_id} — Status: {status}")

            if status == 'SUCCEEDED':
                print("✓ Analysis completed successfully")
                display_analysis_results(definition_id, execution_id)
                return items
            elif status == 'FAILED':
                details = latest.get('statusDetails', 'No details')
                raise RuntimeError(f"Analysis failed: {details}")

            time.sleep(poll_interval)

        except RuntimeError:
            raise
        except Exception as error:
            print(f"  Attempt {attempt}/{max_attempts} — Error: {str(error)}")
            time.sleep(poll_interval)

    raise TimeoutError(f"Analysis did not complete after {max_attempts} attempts")


if __name__ == '__main__':
    definition_id = os.environ.get('DEFINITION_ID')
    execution_id = os.environ.get('EXECUTION_ID')
    
    if not definition_id or not execution_id:
        if len(sys.argv) < 3:
            print("Usage: python 06a_wait_analysis.py <definitionID> <executionID>", file=sys.stderr)
            print("Or set DEFINITION_ID and EXECUTION_ID environment variables", file=sys.stderr)
            sys.exit(1)
        definition_id = definition_id or sys.argv[1]
        execution_id = execution_id or sys.argv[2]
    
    try:
        wait_for_analysis(definition_id, execution_id)
    except Exception as error:
        print(f"Failed to wait for analysis: {str(error)}", file=sys.stderr)
        sys.exit(1)