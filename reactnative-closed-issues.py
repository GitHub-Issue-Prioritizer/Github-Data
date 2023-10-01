import requests
import pandas as pd

# Replace 'YOUR_ACCESS_TOKEN' with your actual GitHub personal access token
access_token = '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'

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
    'labels'
]

def extract_subfields(issue):
    return {
        'assignee_names': [assignee['login'] for assignee in issue['assignees']],
        'assignee_count': len(issue['assignees']),
        'label_names': [label['name'] for label in issue['labels']],
        'label_count': len(issue['labels'])
    }

def fetch_issues(repo_owner, repo_name, state='closed', per_page=100):
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
    issues_saved = 0

    while True:
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code == 200:
            new_issues = response.json()
            for issue in new_issues:
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
                issues.append(data)
                issues_saved += 1  # Increment the count for each issue saved

                if issues_saved == 5000:
                    break  # Stop fetching after 5000 issues

            if 'rel="next"' not in response.headers.get('Link', '') or issues_saved == 5000:
                break  # No more pages to fetch or reached 5000 issues
            params['page'] += 1

            # Check if the number of issues saved is a multiple of 1000
            if issues_saved % 1000 == 0:
                print(f"Saved {issues_saved} issues so far.")
        else:
            print(f"Failed to retrieve issues. Status code: {response.status_code}")
            break

    return issues

if __name__ == "__main__":
    repo_owner = 'facebook'
    repo_name = 'react-native'
    closed_issues = fetch_issues(repo_owner, repo_name)

    # Create a DataFrame from the retrieved closed issues
    df = pd.DataFrame(closed_issues)

    # Export the DataFrame to an Excel file
    excel_file = 'closed_issues.xlsx'
    df.to_excel(excel_file, index=False)

    print(f"Total closed issues: {len(closed_issues)}")
    print(f"Data exported to {excel_file}")
