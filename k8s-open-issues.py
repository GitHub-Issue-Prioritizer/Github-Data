import requests
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub API endpoint for issues in the repository of your choice
repo_owner = 'kubernetes'  # Replace with the repository owner's username or organization name
repo_name = 'kubernetes'    # Replace with the name of the repository
api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'

# Replace with your GitHub personal access token
token = os.getenv("GITHUB_ACCESS_TOKEN")

headers = {
   'Authorization': f'token {token}'
}

# Initialize a list to store all issues
all_issues = []

# Initialize page counter
page = 1

while True:
    # Fetch issues data from the GitHub repository, 5000 per page (the maximum allowed by GitHub)
    response = requests.get(api_url, headers=headers, params={'page': page, 'state': 'open'})

    if response.status_code == 200:
        issues_data = response.json()
        
        # If there are no more issues, break the loop
        if not issues_data:
            break

        # Append the issues from this page to the list
        all_issues.extend(issues_data)

        # Increment the page counter
        page += 1
    else:
        print(f'Failed to fetch data. Status code: {response.status_code}')
        break

# Extract only the desired fields from the issues data
desired_fields = [
    'id',
    'title',
    'state',
    'label_names',
    'label_count',
    'created_at',
    'updated_at',
    'closed_at',
    'comments',
    'assignee_names',
    'assignee_count',
    'milestone',
    'locked'
]

# Extract the label names and label counts from the labels list
def extract_label_info(label_list):
    label_names = [label['name'] for label in label_list]
    label_count = len(label_names)
    return {'label_names': label_names, 'label_count': label_count}

# Modify the issues data to include only label names and label count
for issue in all_issues:
   label_info = extract_label_info(issue['labels'])
   issue['label_names'] = label_info['label_names']
   issue['label_count'] = label_info['label_count']

# Modify the issues data to include assignee names and assignee count
def extract_assignee_info(assignees_list):
    assignee_names = [assignee['login'] for assignee in assignees_list]
    assignee_count = len(assignee_names)
    return {'assignee_names': assignee_names, 'assignee_count': assignee_count}

for issue in all_issues:
    assignee_info = extract_assignee_info(issue['assignees'])
    issue['assignee_names'] = assignee_info['assignee_names']
    issue['assignee_count'] = assignee_info['assignee_count']

issues_data_filtered = [{field: issue[field] for field in desired_fields} for issue in all_issues]

# Convert the filtered issue data to a DataFrame
df = pd.DataFrame(issues_data_filtered)

# Save the DataFrame to an Excel file (XLSX)
df.to_excel('k8s_open_issues.xlsx', index=False)


# Save the DataFrame to an Excel file (XLSX) and append to the existing file
# with pd.ExcelWriter('k8s_github_issues.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
#     df.to_excel(writer, index=False, sheet_name='Sheet1', header=True)  # Append data to the existing sheet

print(f'Data saved to k8s_open_issues.xlsx')