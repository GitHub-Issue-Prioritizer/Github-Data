# import requests
# import pandas as pd
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# # Load environment variables from .env file
# load_dotenv()

# access_token = os.getenv("G3")

# # Define the desired fields and subfields
# desired_fields = [
#     'id',
#     'title',
#     'state',
#     'created_at',
#     'updated_at',
#     'closed_at',
#     'comments',
#     'assignees',
#     'labels',
#     'pr_associated'  # New column for PR association
# ]

# def extract_subfields(issue):
#     return {
#         'assignee_names': [assignee['login'] for assignee in issue['assignees']],
#         'assignee_count': len(issue['assignees']),
#         'label_names': [label['name'] for label in issue['labels']],
#         'label_count': len(issue['labels'])
#     }

# def has_associated_pull_request(issue):
#     return 1 if 'pull_request' in issue else 0

# def fetch_issues(repo_owner, repo_name, state='closed', per_page=100, start_date='2020-10-03', max_issues=5000):
#     base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
#     start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
#     params = {
#         'state': state,
#         'per_page': per_page,
#         'page': 1
#     }
#     headers = {
#         'Authorization': f'token {access_token}'  # Include your access token
#     }
#     issues = []
#     issues_saved = 0

#     while issues_saved < max_issues:
#         response = requests.get(base_url, params=params, headers=headers)

#         if response.status_code == 200:
#             new_issues = response.json()
#             for issue in new_issues:
#                 created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
#                 if created_at >= start_datetime and issues_saved < max_issues:
#                     data = {
#                         'id': issue['id'],
#                         'title': issue['title'],
#                         'state': issue['state'],
#                         'created_at': issue['created_at'],
#                         'updated_at': issue['updated_at'],
#                         'closed_at': issue['closed_at'],
#                         'comments': issue['comments']
#                     }
#                     data.update(extract_subfields(issue))
#                     data['pr_associated'] = has_associated_pull_request(issue)
#                     issues.append(data)
#                     issues_saved += 1

#                 if issues_saved % 1000 == 0:
#                     print(f"Saved {issues_saved} issues so far.")

#                 if 'rel="next"' not in response.headers.get('Link', '') or issues_saved == max_issues:
#                     break  # No more pages to fetch or reached the desired number of issues
#             params['page'] += 1
#         else:
#             print(f"Failed to retrieve issues. Status code: {response.status_code}")
#             break

#     # Filter issues with assignee_count > 0, label_count > 0, and closed issues with PR association.
#     issues = [issue for issue in issues if issue['label_count'] > 0 and issue['pr_associated'] in [0, 1]]

#     return issues

# if __name__ == "__main__":
#     repo_owner = 'facebook'
#     repo_name = 'react-native'
#     max_issues = 5000
#     closed_issues = fetch_issues(repo_owner, repo_name, max_issues=max_issues)

#     # Create a DataFrame from the retrieved closed issues
#     df = pd.DataFrame(closed_issues)

#     # Export the DataFrame to an Excel file
#     excel_file = 'closed3_issues.xlsx'
#     df.to_excel(excel_file, index=False)

#     print(f"Total closed issues: {len(closed_issues)}")
#     print(f"Data exported to {excel_file}")


# import requests
# import pandas as pd
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# # Load environment variables from .env file
# load_dotenv()

# access_token = os.getenv("G3")

# # Define the desired fields and subfields
# desired_fields = [
#     'id',
#     'title',
#     'state',
#     'created_at',
#     'updated_at',
#     'closed_at',
#     'comments',
#     'assignees',
#     'labels',
#     'pr_associated',
#     'comment_priority',  # New column for comment priority
#     'high_priority_label',  # New columns for label encoding of priority labels
#     'medium_priority_label',
#     'low_priority_label'
# ]

# def extract_subfields(issue,df):
#     assignee_names = [assignee['login'] for assignee in issue['assignees']]
#     assignee_count = len(assignee_names)
#     label_names = [label['name'] for label in issue['labels']]
#     label_count = len(label_names)
#     labels_dict = {}
    
#     # Calculate comment priority
#     num_comments = issue['comments']
#     comments_median = df['comments'].median()  # Modify 'df' to your DataFrame name
#     comment_priority = 'low'
#     if num_comments > comments_median:
#         comment_priority = 'high'
#     elif num_comments == comments_median:
#         comment_priority = 'medium'

#     # Define label categories
#     high_priority_labels = ['p0', 'priority: p0', 'p1', 'priority 1', 'priority: p1', 'critical', 'criticalpriority',
#                             'priority-critical', 'critical priority', 'priority:critical', 'priority critical', 'priority: crit-ical',
#                             'priority - critical', 'critical-priority', 'priority/critical', 'urgent', 'priority/urgent', 'priority/blocker',
#                             'priority: blocker', 'important', 'priority/important', 'priority: ma-jor', 'highpriority', 'priority-high',
#                             'high priority', 'priority:high', 'priority high', 'priority: high', 'priority - high', 'high-priority', 'priority/high',
#                             'is:priority']
    
#     medium_priority_labels = ['priority: p2', 'p2']
    
#     low_priority_labels = ['priority: p3', 'p3', 'priority 3', 'priority: p4', 'p4', 'priority 4', 'priority: minor', 'lowpriority',
#                            'priority-low', 'low priority', 'priority:low', 'priority low', 'priority: low', 'priority - low', 'low-priority', 
#                            'priority/low', 'is:no-priority']
    
#     # Check label categories and assign label encodings
#     high_priority_label = 0
#     medium_priority_label = 0
#     low_priority_label = 0

#     for label in label_names:
#         if label in high_priority_labels:
#             high_priority_label = 1
#         elif label in medium_priority_labels:
#             medium_priority_label = 1
#         elif label in low_priority_labels:
#             low_priority_label = 1

#     return {
#         'assignee_names': assignee_names,
#         'assignee_count': assignee_count,
#         'label_names': label_names,
#         'label_count': label_count,
#         'comment_priority': comment_priority,
#         'high_priority_label': high_priority_label,
#         'medium_priority_label': medium_priority_label,
#         'low_priority_label': low_priority_label,
#         **labels_dict,
#     }

# def has_associated_pull_request(issue):
#     return 1 if 'pull_request' in issue else 0

# def fetch_issues(repo_owner, repo_name, state='closed', per_page=100, max_issues=5000):
#     base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
#     params = {
#         'state': state,
#         'per_page': per_page,
#         'page': 1
#     }
#     headers = {
#         'Authorization': f'token {access_token}'  # Include your access token
#     }
#     issues = []
#     issues_saved = 0

#     while issues_saved < max_issues:
#         response = requests.get(base_url, params=params, headers=headers)

#         if response.status_code == 200:
#             new_issues = response.json()
#             for issue in new_issues:
#                 created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
#                 data = {
#                     'id': issue['id'],
#                     'title': issue['title'],
#                     'state': issue['state'],
#                     'created_at': issue['created_at'],
#                     'updated_at': issue['updated_at'],
#                     'closed_at': issue['closed_at'],
#                     'comments': issue['comments']
#                 }
#                 data.update(extract_subfields(issue,df))
#                 data['pr_associated'] = has_associated_pull_request(issue)
#                 issues.append(data)
#                 issues_saved += 1

#                 if issues_saved % 1000 == 0:
#                     print(f"Saved {issues_saved} issues so far.")

#                 if 'rel="next"' not in response.headers.get('Link', '') or issues_saved == max_issues:
#                     break  # No more pages to fetch or reached the desired number of issues
#             params['page'] += 1
#         else:
#             print(f"Failed to retrieve issues. Status code: {response.status_code}")
#             break

#     # Filter issues with label_count > 0 and PR association.
#     issues = [issue for issue in issues if issue['label_count'] > 0 and issue['pr_associated'] in [0, 1]]

#     return issues

# if __name__ == "__main__":
#     repo_owner = 'facebook'
#     repo_name = 'react-native'
#     max_issues = 5000
#     closed_issues = fetch_issues(repo_owner, repo_name, max_issues=max_issues)

#     # Create a DataFrame from the retrieved closed issues
#     df = pd.DataFrame(closed_issues)

#     # Export the DataFrame to an Excel file
#     excel_file = 'updated_closed_issues.xlsx'
#     df.to_excel(excel_file, index=False)

#     print(f"Total closed issues: {len(closed_issues)}")
#     print(f"Data exported to {excel_file}")





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
    'pr_associated',
    'comment_priority',  # New column for comment priority
    'high_priority_label',  # New columns for label encoding of priority labels
    'medium_priority_label',
    'low_priority_label'
]

def extract_subfields(issue, df):
    assignee_names = [assignee['login'] for assignee in issue['assignees']]
    assignee_count = len(assignee_names)
    label_names = [label['name'] for label in issue['labels']]
    label_count = len(label_names)
    labels_dict = {}
    
    # Calculate comment priority
    num_comments = issue['comments']
    comments_median = df['comments'].median()
    comment_priority = 'low'
    if num_comments > comments_median:
        comment_priority = 'high'
    elif num_comments == comments_median:
        comment_priority = 'medium'

    # Define label categories
    high_priority_labels = ['p0', 'priority: p0', 'p1', 'priority 1', 'priority: p1', 'critical', 'criticalpriority',
                            'priority-critical', 'critical priority', 'priority:critical', 'priority critical', 'priority: crit-ical',
                            'priority - critical', 'critical-priority', 'priority/critical', 'urgent', 'priority/urgent', 'priority/blocker',
                            'priority: blocker', 'important', 'priority/important', 'priority: ma-jor', 'highpriority', 'priority-high',
                            'high priority', 'priority:high', 'priority high', 'priority: high', 'priority - high', 'high-priority', 'priority/high',
                            'is:priority']
    
    medium_priority_labels = ['priority: p2', 'p2']
    
    low_priority_labels = ['priority: p3', 'p3', 'priority 3', 'priority: p4', 'p4', 'priority 4', 'priority: minor', 'lowpriority',
                           'priority-low', 'low priority', 'priority:low', 'priority low', 'priority: low', 'priority - low', 'low-priority', 
                           'priority/low', 'is:no-priority']
    
    # Check label categories and assign label encodings
    high_priority_label = 0
    medium_priority_label = 0
    low_priority_label = 0

    for label in label_names:
        if label in high_priority_labels:
            high_priority_label = 1
        elif label in medium_priority_labels:
            medium_priority_label = 1
        elif label in low_priority_labels:
            low_priority_label = 1

    return {
        'assignee_names': assignee_names,
        'assignee_count': assignee_count,
        'label_names': label_names,
        'label_count': label_count,
        'comment_priority': comment_priority,
        'high_priority_label': high_priority_label,
        'medium_priority_label': medium_priority_label,
        'low_priority_label': low_priority_label,
        **labels_dict,
    }

def has_associated_pull_request(issue):
    return 1 if 'pull_request' in issue else 0

def fetch_issues(repo_owner, repo_name, state='closed', per_page=100, max_issues=5000):
    base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
    params = {
        'state': state,
        'per_page': per_page,
        'page': 1
    }
    headers = {
        'Authorization': f'token {access_token}'  # Include your access token
    }
    issues = []

    while True:  # Keep fetching until there are no more issues or you reach the desired number
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code == 200:
            new_issues = response.json()
            if not new_issues:
                break  # No more issues to fetch
            issues.extend(new_issues)
            if len(issues) >= max_issues:
                break  # Reached the desired number of issues
            params['page'] += 1
        else:
            print(f"Failed to retrieve issues. Status code: {response.status_code}")
            break

    # Filter issues with label_count > 0 and PR association.
    issues = [issue for issue in issues if issue['label_count'] > 0 and issue['pr_associated'] in [0, 1]]

    return issues

if __name__ == "__main__":
    repo_owner = 'facebook'
    repo_name = 'react-native'
    max_issues = 5000
    closed_issues = fetch_issues(repo_owner, repo_name, max_issues=max_issues)

    # Create a DataFrame from the retrieved closed issues
    df = pd.DataFrame(closed_issues)

    # Process the data as needed
    issues = []
    for issue in closed_issues:
        data = {
            'id': issue['id'],
            'title': issue['title'],
            'state': issue['state'],
            'created_at': issue['created_at'],
            'updated_at': issue['updated_at'],
            'closed_at': issue['closed_at'],
            'comments': issue['comments']
        }
        data.update(extract_subfields(issue, df))
        data['pr_associated'] = has_associated_pull_request(issue)
        issues.append(data)

    # Export the DataFrame to an Excel file
    excel_file = 'updated_closed_issues.xlsx'
    df.to_excel(excel_file, index=False)

    print(f"Total closed issues: {len(closed_issues)}")
    print(f"Data exported to {excel_file}")
