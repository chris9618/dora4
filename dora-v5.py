import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

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

# Fetch all projects in a group recursively
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

    subgroups = fetch_gitlab_data(f'/groups/{group_id}/subgroups')
    for subgroup in subgroups:
        projects.extend(fetch_group_projects(subgroup['id']))

    return projects

# Fetch deployment data
def fetch_deployments(project_id, start_date, end_date):
    deployments = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100, 'created_after': start_date, 'created_before': end_date}
        data = fetch_gitlab_data(f'/projects/{project_id}/deployments', params)
        if not data:
            break
        deployments.extend(data)
        page += 1
    return deployments

# Fetch project pipelines
def fetch_pipelines(project_id, start_date, end_date):
    pipelines = []
    page = 1
    while True:
        params = {'page': page, 'per_page': 100, 'updated_after': start_date, 'updated_before': end_date}
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

# Parse datetime with flexible handling of formats
def parse_datetime(date_str):
    for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_str}' is not supported")

# Analyze DORA metrics for a single project
def analyze_dora_metrics(project_id, start_date, end_date):
    deployments = fetch_deployments(project_id, start_date, end_date)
    pipelines = fetch_pipelines(project_id, start_date, end_date)

    deployment_times = [parse_datetime(d['created_at']) for d in deployments]

    lead_times = []
    change_failures = 0
    restoration_times = []

    for pipeline in pipelines:
        if pipeline['status'] == 'success':
            jobs = fetch_pipeline_jobs(project_id, pipeline['id'])
            created_at = parse_datetime(pipeline['created_at'])
            updated_at = parse_datetime(pipeline['updated_at'])
            lead_times.append((updated_at - created_at).total_seconds() / 3600)  # Lead time in hours

            for job in jobs:
                if job['status'] == 'failed':
                    change_failures += 1
                if job['name'] == 'restore' and job['status'] == 'success':
                    restoration_time = parse_datetime(job['finished_at']) - parse_datetime(job['started_at'])
                    restoration_times.append(restoration_time.total_seconds() / 3600)  # Restoration time in hours

    # Deployment frequency as deployments per day
    total_days = (parse_datetime(end_date) - parse_datetime(start_date)).days + 1
    deployment_frequency = len(deployment_times) / total_days if total_days > 0 else 0
    
    # Average lead time for changes in hours
    lead_time_for_changes = sum(lead_times) / len(lead_times) if lead_times else 0
    
    # Change failure rate as percentage
    change_failure_rate = (change_failures / len(pipelines)) * 100 if pipelines else 0
    
    # Mean time to restore in hours
    mttr = sum(restoration_times) / len(restoration_times) if restoration_times else 0

    return {
        'deployment_frequency': deployment_frequency,
        'lead_time_for_changes': lead_time_for_changes,
        'change_failure_rate': change_failure_rate,
        'mean_time_to_restore': mttr
    }

# Function to analyze multiple projects and aggregate metrics
def analyze_multiple_projects(project_ids, start_date, end_date):
    metrics = {
        'project_id': [],
        'date': [],
        'deployment_frequency': [],
        'lead_time_for_changes': [],
        'change_failure_rate': [],
        'mean_time_to_restore': []
    }

    for project_id in project_ids:
        dora_metrics = analyze_dora_metrics(project_id, start_date, end_date)
        metrics['project_id'].append(project_id)
        metrics['date'].append(end_date)  # Assuming end_date as the date for reporting purposes
        metrics['deployment_frequency'].append(dora_metrics['deployment_frequency'])
        metrics['lead_time_for_changes'].append(dora_metrics['lead_time_for_changes'])
        metrics['change_failure_rate'].append(dora_metrics['change_failure_rate'])
        metrics['mean_time_to_restore'].append(dora_metrics['mean_time_to_restore'])

    metrics_df = pd.DataFrame(metrics)
    return metrics_df

# Function to generate monthly and daily reports
def generate_reports(group_id, start_date, end_date):
    projects = fetch_group_projects(group_id)
    project_ids = [project['id'] for project in projects]

    # Daily report
    daily_metrics_df = analyze_multiple_projects(project_ids, start_date, end_date)
    daily_metrics_df['date'] = pd.to_datetime(daily_metrics_df['date'])

    # Monthly report
    monthly_metrics_df = daily_metrics_df.copy()
    monthly_metrics_df['date'] = monthly_metrics_df['date'].dt.to_period('M')
    monthly_metrics_df = monthly_metrics_df.groupby(['project_id', 'date']).mean().reset_index()

    return daily_metrics_df, monthly_metrics_df

# Example usage
group_id = 'YOUR_GROUP_ID_HERE'  # Replace with your GitLab group ID
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')  # Adjust date range as needed
end_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

daily_metrics_df, monthly_metrics_df = generate_reports(group_id, start_date, end_date)

# Display the aggregated metrics
print("Daily Metrics:")
print(daily_metrics_df)
print("\nMonthly Metrics:")
print(monthly_metrics_df)

# Optionally, save the metrics to CSV files for further analysis
daily_metrics_df.to_csv('daily_dora_metrics.csv', index=False)
monthly_metrics_df.to_csv('monthly_dora_metrics.csv', index=False)
