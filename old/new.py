from statistics import median
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

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
    'high_priority_label',  # New column for high priority label
    'medium_priority_label',  # New column for medium priority label
    'low_priority_label'  # New column for low priority label
]

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

def label_encode_priority(issues):
    for issue in issues:
        title = issue['title'].lower()

        high_priority_keywords = [
            'priority: p0', 'priority 0', 'priority: p1', 'priority 1',
            'critical', 'criticalpriority', 'priority-critical',
            'critical priority', 'priority:critical', 'priority critical',
            'priority: critical', 'priority - critical', 'critical-priority',
            'priority/critical', 'urgent', 'priority/urgent',
            'priority/blocker', 'priority: blocker', 'highpriority',
            'priority-high', 'high priority', 'priority:high',
            'priority high', 'priority: high', 'priority - high',
            'high-priority', 'priority/high', 'is:priority'
        ]

        medium_priority_keywords = ['priority: p2', 'p2']

        low_priority_keywords = [
            'priority: p3', 'priority 3', 'priority: p4', 'p4',
            'priority 4', 'priority: minor', 'lowpriority',
            'priority-low', 'low priority', 'priority:low',
            'priority low', 'priority: low', 'priority - low',
            'low-priority', 'priority/low', 'is:no-priority'
        ]

        issue['high_priority_label'] = any(keyword in title for keyword in high_priority_keywords)
        issue['medium_priority_label'] = any(keyword in title for keyword in medium_priority_keywords)
        issue['low_priority_label'] = any(keyword in title for keyword in low_priority_keywords)

def fetch_issues(repo_owner, repo_name, state='closed', per_page=100, max_issues=5000):
    base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
    # start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    params = {
        'state': state,
        'per_page': per_page,
        'page': 1
    }
    headers = {
        'Authorization': f'token {access_token}'  # Include your access token
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
                    break  # No more pages to fetch or reached the desired number of issues
            params['page'] += 1
        else:
            print(f"Failed to retrieve issues. Status code: {response.status_code}")
            break

    calculate_comment_priority(issues)
    calculate_top_labels(issues)
    label_encode_priority(issues)

    # Filter issues with assignee_count > 0, label_count > 0, and closed issues with PR association.
    issues = [issue for issue in issues if issue['label_count'] > 0 and issue['pr_associated'] in [0, 1]]

    return issues

if __name__ == "__main__":
    repo_owner = 'facebook'
    repo_name = 'react-native'
    max_issues = 5000
    closed_issues = fetch_issues(repo_owner, repo_name, max_issues=max_issues)

    # Create a DataFrame from the retrieved closed issues
    df = pd.DataFrame(closed_issues)

    # Export the DataFrame to an Excel file
    excel_file = 'closed_issues_modified.xlsx'
    df.to_excel(excel_file, index=False)

    print(f"Total closed issues: {len(closed_issues)}")
    print(f"Data exported to {excel_file}")
