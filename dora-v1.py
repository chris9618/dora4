import requests
import pandas as pd
from datetime import datetime, timedelta

# Define your GitLab personal access token
access_token = 'YOUR_ACCESS_TOKEN_HERE'

# Define the GitLab API endpoint
base_url = 'https://gitlab.com/api/v4'

# Function to fetch data from GitLab API
def fetch_gitlab_data(endpoint, params=None):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f'{base_url}{endpoint}', headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data from GitLab API. Status code: {response.status_code}")

# Fetch all projects in a group
def fetch_group_projects(group_id):
    projects = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100}
        data = fetch_gitlab_data(f'/groups/{group_id}/projects', params)
        if not data:
            break
        projects.extend(data)
        page += 1
    return projects

# Fetch deployment data
def fetch_deployments(project_id):
    deployments = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100}
        data = fetch_gitlab_data(f'/projects/{project_id}/deployments', params)
        if not data:
            break
        deployments.extend(data)
        page += 1
    return deployments

# Fetch project pipelines
def fetch_pipelines(project_id):
    pipelines = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100}
        data = fetch_gitlab_data(f'/projects/{project_id}/pipelines', params)
        if not data:
            break
        pipelines.extend(data)
        page += 1
    return pipelines

# Fetch pipeline jobs
def fetch_pipeline_jobs(project_id, pipeline_id):
    jobs = fetch_gitlab_data(f'/projects/{project_id}/pipelines/{pipeline_id}/jobs')
    return jobs

# Analyze DORA metrics for a single project
def analyze_dora_metrics(project_id):
    deployments = fetch_deployments(project_id)
    pipelines = fetch_pipelines(project_id)

    deployment_times = [datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ') for d in deployments]

    lead_times = []
    change_failures = 0
    restoration_times = []

    for pipeline in pipelines:
        if pipeline['status'] == 'success':
            jobs = fetch_pipeline_jobs(project_id, pipeline['id'])
            created_at = datetime.strptime(pipeline['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            updated_at = datetime.strptime(pipeline['updated_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            lead_times.append((updated_at - created_at).total_seconds() / 3600)  # Lead time in hours

            for job in jobs:
                if job['status'] == 'failed':
                    change_failures += 1
                if job['name'] == 'restore' and job['status'] == 'success':
                    restoration_time = datetime.strptime(job['finished_at'], '%Y-%m-%dT%H:%M:%S.%fZ') - datetime.strptime(job['started_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    restoration_times.append(restoration_time.total_seconds() / 3600)  # Restoration time in hours

    deployment_frequency = len(deployment_times) / len(pipelines) if pipelines else 0
    lead_time_for_changes = sum(lead_times) / len(lead_times) if lead_times else 0
    change_failure_rate = change_failures / len(pipelines) if pipelines else 0
    mttr = sum(restoration_times) / len(restoration_times) if restoration_times else 0

    return {
        'deployment_frequency': deployment_frequency,
        'lead_time_for_changes': lead_time_for_changes,
        'change_failure_rate': change_failure_rate,
        'mean_time_to_restore': mttr
    }

# Function to analyze multiple projects and aggregate metrics
def analyze_multiple_projects(project_ids):
    metrics = {
        'project_id': [],
        'deployment_frequency': [],
        'lead_time_for_changes': [],
        'change_failure_rate': [],
        'mean_time_to_restore': []
    }

    for project_id in project_ids:
        dora_metrics = analyze_dora_metrics(project_id)
        metrics['project_id'].append(project_id)
        metrics['deployment_frequency'].append(dora_metrics['deployment_frequency'])
        metrics['lead_time_for_changes'].append(dora_metrics['lead_time_for_changes'])
        metrics['change_failure_rate'].append(dora_metrics['change_failure_rate'])
        metrics['mean_time_to_restore'].append(dora_metrics['mean_time_to_restore'])

    metrics_df = pd.DataFrame(metrics)
    return metrics_df

# Example usage
group_id = 'YOUR_GROUP_ID_HERE'  # Replace with your GitLab group ID
projects = fetch_group_projects(group_id)
project_ids = [project['id'] for project in projects]

metrics_df = analyze_multiple_projects(project_ids)

# Display the aggregated metrics
print(metrics_df)

# Optionally, save the metrics to a CSV file for further analysis
metrics_df.to_csv('dora_metrics.csv', index=False)
