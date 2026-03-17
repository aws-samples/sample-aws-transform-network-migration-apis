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
Complete Network Migration Workflow

This script orchestrates all steps of the network migration process:
1. Create network migration definition
2. List executions and retrieve execution ID
3. Start network mapping
4. List and review segments
5. Edit segments (optional customization)
6. Generate infrastructure code
7. Deploy network infrastructure
8. Run connectivity analysis

Note: This is a demo script. In production, you should implement proper
job status polling instead of fixed delays.
"""

import time
import uuid
import sys
import os
import boto3

# Add current directory to path to import other modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize MGN client
region = os.environ.get('AWS_REGION', 'us-east-1')
endpoint = os.environ.get('ENDPOINT_URL')
mgn_kwargs = {'region_name': region}
if endpoint:
    mgn_kwargs['endpoint_url'] = endpoint
client = boto3.client('mgn', **mgn_kwargs)

# Import functions from other example scripts
import importlib

# Dynamically import modules to avoid issues with numeric prefixes
create_definition_module = importlib.import_module('01_create_definition')
list_executions_module = importlib.import_module('01a_list_execution')
start_mapping_module = importlib.import_module('02_start_mapping')
wait_mapping_module = importlib.import_module('02a_wait_mapping')
list_segments_module = importlib.import_module('02b_list_segments')
edit_segments_module = importlib.import_module('03_edit_segments')
generate_code_module = importlib.import_module('04_generate_code')
wait_code_gen_module = importlib.import_module('04a_wait_code_generation')
deploy_network_module = importlib.import_module('05_deploy_network')
wait_deploy_module = importlib.import_module('05a_wait_deployment')
run_analysis_module = importlib.import_module('06_run_analysis')
wait_analysis_module = importlib.import_module('06a_wait_analysis')

create_definition = create_definition_module.create_definition
list_executions = list_executions_module.list_executions
get_latest_execution_id = list_executions_module.get_latest_execution_id
start_mapping = start_mapping_module.start_mapping
wait_for_mapping = wait_mapping_module.wait_for_mapping
list_segments = list_segments_module.list_segments
edit_segments = edit_segments_module.edit_segments
generate_code = generate_code_module.generate_code
wait_for_code_generation = wait_code_gen_module.wait_for_code_generation
deploy_network = deploy_network_module.deploy_network
wait_for_deployment = wait_deploy_module.wait_for_deployment
run_analysis = run_analysis_module.run_analysis
wait_for_analysis = wait_analysis_module.wait_for_analysis


def sleep(seconds):
    """Sleep for specified seconds."""
    time.sleep(seconds)


def wait_for_mapping_update(definition_id, execution_id, poll_interval=10, max_attempts=60):
    """Wait for the latest mapping update job to complete."""
    print("Waiting for mapping update to complete (polling every 10s)...")
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.list_network_migration_mapping_updates(
                networkMigrationDefinitionID=definition_id,
                networkMigrationExecutionID=execution_id,
                maxResults=1
            )
            items = response.get('items', [])
            if items:
                status = items[0].get('status', 'UNKNOWN')
                print(f"  Attempt {attempt}/{max_attempts} — Status: {status}")
                if status in ('SUCCEEDED', 'COMPLETED'):
                    print("✓ Mapping update complete")
                    return
                if status in ('FAILED', 'ERROR'):
                    print(f"✗ Mapping update failed: {items[0].get('statusDetails', '')}")
                    return
            time.sleep(poll_interval)
        except Exception as error:
            print(f"  Attempt {attempt}/{max_attempts} — Error: {error}")
            time.sleep(poll_interval)
    print("⚠ Timed out waiting for mapping update")


def complete_workflow():
    """
    Execute the complete network migration workflow.
    """
    print("=== AWS Network Migration Complete Workflow ===\n")
    
    try:
        # Step 1: Create Definition
        print("Step 1: Creating Network Migration Definition...")
        definition_id = create_definition()
        sleep(2)
        
        # Step 1a: List Executions and get execution ID
        print("\nStep 1a: Retrieving Execution ID from definition...")
        execution_id = get_latest_execution_id(definition_id)
        sleep(2)

        # Step 2: Start Mapping
        print("\nStep 2: Starting Network Migration Mapping...")
        mapping_job_id = start_mapping(definition_id, execution_id)
        sleep(2)

        # Step 2b: Wait for mapping to complete
        print("\nStep 2a: Waiting for mapping to complete...")
        wait_for_mapping(definition_id, execution_id)
        sleep(2)
        
        # Step 2a: List and Review Segments
        print("\nStep 2b: Listing Network Migration Segments...")
        segments = list_segments(definition_id, execution_id)
        print(f"Found {len(segments)} segments to review")
        sleep(2)
        
        # Step 3: Edit Segments
        print("\nStep 3: Editing Migration Segments...")
        edit_segments(definition_id, execution_id)
        sleep(2)

        # Step 3a: Wait for mapping update to complete
        print("\nStep 3a: Waiting for mapping update to complete...")
        wait_for_mapping_update(definition_id, execution_id)
        sleep(2)
        
        # Step 4: Generate Code
        print("\nStep 4: Generating Infrastructure Code...")
        code_gen_job_id = generate_code(definition_id, execution_id)
        sleep(2)
        
        print("\nStep 4a: Waiting for code generation to complete...")
        wait_for_code_generation(definition_id, execution_id)
        sleep(2)

        # Step 5: Deploy Network
        print("\nStep 5: Deploying Network...")
        deploy_job_id = deploy_network(definition_id, execution_id)
        sleep(2)

        # Step 5a: Wait for deployment to complete
        print("\nStep 5a: Waiting for deployment to complete...")
        wait_for_deployment(definition_id, execution_id)
        sleep(2)
        
        # Step 6: Run Analysis
        print("\nStep 6: Running Migration Analysis...")
        analysis_job_id = run_analysis(definition_id, execution_id)
        
        # Step 6a: Wait for analysis to complete
        print("\nStep 6a: Waiting for analysis to complete...")
        wait_for_analysis(definition_id, execution_id)
        sleep(2)
        
        print("\n=== Workflow Complete ===")
        print("\nSummary:")
        print(f"- Definition ID: {definition_id}")
        print(f"- Execution ID: {execution_id}")
        print(f"- Segments Found: {len(segments)}")
        print(f"- Mapping Job: {mapping_job_id}")
        print(f"- Code Gen Job: {code_gen_job_id}")
        print(f"- Deploy Job: {deploy_job_id}")
        print(f"- Analysis Job: {analysis_job_id}")
        
    except Exception as error:
        print(f"\n❌ Workflow failed: {str(error)}")
        sys.exit(1)


if __name__ == '__main__':
    # Run workflow
    complete_workflow()
