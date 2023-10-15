import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import re
import statistics

# Load environment variables from .env file
load_dotenv()

access_token = os.getenv("GITHUB_ACCESS_TOKEN2")

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
    median_comments = statistics.median(comment_counts)
    for issue in issues:
        if issue['comments'] > median_comments:
            issue['comment_priority'] = 1
        elif issue['comments'] == median_comments:
            issue['comment_priority'] = 2
        else:
            issue['comment_priority'] = 3

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

def consolidate_priority(issues, label_mapping, include_priority_labels):
    filtered_issues = []
    for issue in issues:
        labels = [label for label in issue['label_names']]
        has_priority_label = any(label in labels for label in include_priority_labels)
        if has_priority_label:
            for priority, label_categories in label_mapping.items():
                if any(label in labels for label in label_categories):
                    issue['priority'] = priority
                    filtered_issues.append(issue)
                    break
    return filtered_issues

def fetch_issues(repo_owner, repo_name, state='open', per_page=100, max_issues=5000):
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
    return issues

if __name__ == "__main__":
    include_priority_labels = [
    'low impact', 'medium difficulty', 'medium effort', 'must have eventually', 'must have', 'nice to have', 'should have',
    'high priority', 'medium priority', 'low priority',
    'priority-0-high', 'priority-1-normal', 'priority-2-low',
    'High Priority', 'Low Priority', 'Moderate',
    'Priority: Critical', 'Priority: High','Priority:High','Priority: Medium','Priority:Medium', 'Priority: Low',
    'P0', 'P1', 'P2', 'P3', 'P4', 'P5',
    'priorirty: low', 'priority: important',
    'priority::critical', 'priority::high', 'priority::medium', 'priority::low',
    '🧹 p1-chore','🍰 p2-nice-to-have', '🔨 p3-minor-bug', '❗ p4-important', '🔥 p5-urgent',
    '- P1: chore', '- P2: has workaround', '- P2: nice to have', '- P3: minor bug', '- P4: important', '- P5: urgent',
    ]   
    repos = [
        # ('ETHEREUM', 'SOLIDITY', ['low impact', 'medium difficulty', 'medium effort', 'must have eventually', 'must have', 'nice to have', 'should have']),
        # ('ETHEREUM', 'ethereum-org-website', ['high priority', 'medium priority', 'low priority']),
        # ('python', 'mypy', ['priority-0-high', 'priority-1-normal', 'priority-2-low']),
        # ('scikit-learn', 'scikit-learn', ['High Priority', 'Low Priority', 'Moderate']),
        ('MystenLabs', 'sui', ['Priority: Critical', 'Priority: High','Priority:High','Priority: Medium','Priority:Medium', 'Priority: Low']),
        ('angular', 'angular', ['P0', 'P1', 'P2', 'P3', 'P4', 'P5']),
        ('mui', 'material-ui', ['priorirty: low', 'priority: important']),
        # ('axios', 'axios', ['priority::critical', 'priority::high', 'priority::medium', 'priority::low']),
        ('opencv', 'opencv', ['priority: high', 'priority: normal', 'priority: low']),
        ('nuxt', 'nuxt', ['🧹 p1-chore','🍰 p2-nice-to-have', '🔨 p3-minor-bug', '❗ p4-important', '🔥 p5-urgent']),
        # ('withastro', 'Astro', ['- P1: chore', '- P2: has workaround', '- P2: nice to have', '- P3: minor bug', '- P4: important', '- P5: urgent'])
    ]

    max_issues_per_repo = 1000
    combined_issues = []

    label_mapping = {
          1: [
            'must have eventually', 'must have', 'should have', #1
            'high priority', #2
            'priority-0-high', #3
            'High Priority', #4
            'Priority: Critical','Priority: High','Priority:High' #5
            'P0','P1', #6
            'priority: important' #7
            # 'priority::critical','priority::high' #8
            'priority: high' #8
            '❗ p4-important', '🔥 p5-urgent', #9
            '- P4: important', '- P5: urgent', #10
            #extra
            'priority: high', 'urgent', 'critical',
            
        ],
        2: [
            'medium difficulty','medium effort','nice to have',#1
            'medium priority', #2
            'priority-1-normal', #3
            'Moderate', #4
            'Priority: Medium','Priority:Medium', #5
            'P2','P3', #6
            # 'priority::medium' #8
            'priority: normal' #8
            '🍰 p2-nice-to-have', #9
            '- P2: nice to have', '- P3: minor bug', #10
        ],
        3: [
            'low impact', #1
            'low priority',#2
            'priority-2-low', #3
            'Low Priority' #4
            'Priority: Low', #5
            'P4','P5', #6
            'priorirty: low' #7
            # 'priority::low' #8
            'priority: normal' #8
            '🧹 p1-chore', '🔨 p3-minor-bug', #9
            '- P1: chore', '- P2: has workaround', #10
        ]
    }

    for repo_owner, repo_name, labels in repos:
        print(f"Fetching issues from {repo_owner}/{repo_name}")
        fetched_issues = fetch_issues(repo_owner, repo_name, max_issues=max_issues_per_repo)
        filtered_issues = consolidate_priority(fetched_issues, label_mapping, include_priority_labels)
        combined_issues.extend(filtered_issues)
        print(f"Fetched {len(filtered_issues)} issues from {repo_owner}/{repo_name}")

    df = pd.DataFrame(combined_issues)

    excel_file = 'combined_open2_issues.xlsx'
    df.to_excel(excel_file, index=False)

    print(f"Total issues collected: {len(combined_issues)}")
    print(f"Data exported to {excel_file}")
