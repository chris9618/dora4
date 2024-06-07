import requests

# Define constants
GITLAB_URL = 'https://gitlab.example.com'  # Replace with your GitLab instance URL
PRIVATE_TOKEN = 'YOUR_PRIVATE_ACCESS_TOKEN'  # Replace with your GitLab private access token

# Function to make a request to the GitLab API
def make_request(url):
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Function to get CI/CD analytics
def get_ci_cd_analytics(group_id):
    url = f"{GITLAB_URL}/api/v4/groups/{group_id}/ci_cd_analytics"  # Adjust endpoint as needed
    return make_request(url)

# Function to get contribution analytics
def get_contribution_analytics(group_id):
    url = f"{GITLAB_URL}/api/v4/groups/{group_id}/contribution_analytics"  # Adjust endpoint as needed
    return make_request(url)

# Function to get devops adoption
def get_devops_adoption(group_id):
    url = f"{GITLAB_URL}/api/v4/groups/{group_id}/devops_adoption"  # Adjust endpoint as needed
    return make_request(url)

# Function to get insights
def get_insights(group_id):
    url = f"{GITLAB_URL}/api/v4/groups/{group_id}/insights"  # Adjust endpoint as needed
    return make_request(url)

# Function to get productivity analytics
def get_productivity_analytics(group_id):
    url = f"{GITLAB_URL}/api/v4/groups/{group_id}/productivity_analytics"  # Adjust endpoint as needed
    return make_request(url)

# Function to get repository analytics
def get_repository_analytics(group_id):
    url = f"{GITLAB_URL}/api/v4/groups/{group_id}/repository_analytics"  # Adjust endpoint as needed
    return make_request(url)

# Main function to get all analytics for a group
def get_all_analytics(group_id):
    analytics = {
        "ci_cd_analytics": get_ci_cd_analytics(group_id),
        "contribution_analytics": get_contribution_analytics(group_id),
        "devops_adoption": get_devops_adoption(group_id),
        "insights": get_insights(group_id),
        "productivity_analytics": get_productivity_analytics(group_id),
        "repository_analytics": get_repository_analytics(group_id),
    }
    return analytics

# Example usage
if __name__ == "__main__":
    group_id = 12345  # Replace with your group ID
    try:
        analytics = get_all_analytics(group_id)
        print(analytics)
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")
