import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import re
from statistics import median
# Load environment variables from .env file
load_dotenv()

access_token = os.getenv("G3")

# Define the desired fields and subfields
desired_fields = [
    'id',
    'title',
    'state',
    'created_at',
    'updated_at',
    'closed_at',
    'comments',
    'assignees',
    'labels',
    'pr_associated',  # New column for PR association
    'comment_priority',  # New column for comment priority
    'top_labels',  # New column for top 3 labels
    'Top_label_1',  # New column for label 1 encoding
    'Top_label_2',  # New column for label 2 encoding
    'Top_label_3',  # New column for label 3 encoding
    'priority'  # New column for consolidated priority levels (1 for high, 2 for normal, 3 for low)
]

def clean_data(data):
    illegal_char_pattern = re.compile(r'\W')
    for key in data:
        if isinstance(data[key], str):
            data[key] = illegal_char_pattern.sub(' ', data[key])

def extract_subfields(issue):
    return {
        'assignee_names': [assignee['login'] for assignee in issue['assignees']],
        'assignee_count': len(issue['assignees']),
        'label_names': [label['name'] for label in issue['labels']],
        'label_count': len(issue['labels'])
    }

def has_associated_pull_request(issue):
    return 1 if 'pull_request' in issue else 0

def calculate_comment_priority(issues):
    comment_counts = [issue['comments'] for issue in issues]
    median_comments = median(comment_counts)

    for issue in issues:
        if issue['comments'] > median_comments:
            issue['comment_priority'] = 'high'
        elif issue['comments'] == median_comments:
            issue['comment_priority'] = 'medium'
        else:
            issue['comment_priority'] = 'low'

def calculate_top_labels(issues):
    label_counts = {}
    for issue in issues:
        for label in issue['label_names']:
            if label in label_counts:
                label_counts[label] += 1
            else:
                label_counts[label] = 1

    top_labels = sorted(label_counts, key=label_counts.get, reverse=True)[:3]

    for issue in issues:
        issue['top_labels'] = top_labels
        for i, label in enumerate(top_labels):
            issue[f'Top_label_{i+1}'] = 1 if label in issue['label_names'] else 0

def consolidate_priority(issues):
    for issue in issues:
        labels = [label.lower() for label in issue['label_names']]

        high_priority_labels = ['priority: high', 'urgent', 'critical']
        medium_priority_labels = ['priority: normal', 'medium', 'normal']
        low_priority_labels = ['priority: low', 'minor', 'low']

        if any(label in labels for label in high_priority_labels):
            issue['priority'] = 1
        elif any(label in labels for label in medium_priority_labels):
            issue['priority'] = 2
        elif any(label in labels for label in low_priority_labels):
            issue['priority'] = 3
        else:
            issue['priority'] = 3

def fetch_issues(repo_owner, repo_name, state='closed', per_page=100, max_issues=5000):
    base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
    params = {
        'state': state,
        'per_page': per_page,
        'page': 1
    }
    headers = {
        'Authorization': f'token {access_token}'
    }
    issues = []
    issues_saved = 0

    while issues_saved < max_issues:
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code == 200:
            new_issues = response.json()
            for issue in new_issues:
                created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                if issues_saved < max_issues:
                    data = {
                        'id': issue['id'],
                        'title': issue['title'],
                        'state': issue['state'],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at'],
                        'closed_at': issue['closed_at'],
                        'comments': issue['comments']
                    }
                    data.update(extract_subfields(issue))
                    data['pr_associated'] = has_associated_pull_request(issue)
                    issues.append(data)
                    issues_saved += 1

                if issues_saved % 1000 == 0:
                    print(f"Saved {issues_saved} issues so far.")

                if 'rel="next"' not in response.headers.get('Link', '') or issues_saved == max_issues:
                    break
            params['page'] += 1
        else:
            print(f"Failed to retrieve issues. Status code: {response.status_code}")
            break

    calculate_comment_priority(issues)
    calculate_top_labels(issues)
    consolidate_priority(issues)

    for issue in issues:
        clean_data(issue)

    return issues

if __name__ == "__main__":
    repo_owner = 'opencv'
    repo_name = 'opencv'
    max_issues = 5000
    closed_issues = fetch_issues(repo_owner, repo_name, max_issues=max_issues)

    df = pd.DataFrame(closed_issues)

    excel_file = '1opencv_closed_issues_modified.xlsx'
    df.to_excel(excel_file, index=False)

    print(f"Total closed issues: {len(closed_issues)}")
    print(f"Data exported to {excel_file}")
