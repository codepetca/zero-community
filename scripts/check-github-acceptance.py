#!/usr/bin/env python3
"""Owner-side read-only GitHub acceptance check. Never approve, merge or publish.

Run this helper from a clean checkout at authenticated canonical GitHub main,
never the helper from a contribution PR.
API responses are fetched directly with existing gh authentication. No JSON
packet, fixture, contributor flag or AI output can establish authority.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import admission

REPOSITORY = 'codepetca/zero-community'
BASE = 'repos/' + REPOSITORY
ROOT = Path(__file__).resolve().parents[1]


def gh_api(path):
    result = subprocess.run(['gh', 'api', '--hostname', 'github.com', '--method', 'GET', path],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('GitHub read unavailable; contribution waits')
    if len(result.stdout.encode()) > 4_000_000:
        raise ValueError('GitHub response exceeds read budget')
    return admission.parse_json(result.stdout)


def pages(api, path):
    values = []
    for page in range(1, 101):
        result = api(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
        if not isinstance(result, list):
            raise ValueError('Expected GitHub list response')
        values.extend(result)
        if len(result) < 100:
            return values
    raise ValueError('GitHub review pagination exceeds budget; contribution waits')


def git(root, *arguments, raw=False):
    result = subprocess.run(['git', *arguments], cwd=root, capture_output=True, text=not raw, timeout=10)
    if result.returncode:
        raise ValueError('Cannot verify exact checkout')
    return result.stdout if raw else result.stdout.strip()


def clean_revision(root, label):
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root or git(root, 'status', '--porcelain', '--untracked-files=normal'):
        raise ValueError(f'Acceptance requires a clean committed {label} checkout')
    revision = git(root, 'rev-parse', 'HEAD')
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError(f'Invalid {label} revision')
    return revision


def policy_tree(root):
    # Git modes, object types and blob IDs bind the complete protected path set,
    # including additions/deletions. Candidate scripts are never executed.
    entries = git(root, 'ls-tree', '-r', '-z', 'HEAD', '--',
                  'scripts', '.github/workflows', '.mvn', 'mvnw', 'mvnw.cmd', 'pom.xml', raw=True)
    return {path.decode('utf-8'): identity.decode('ascii') for entry in entries.split(b'\0') if entry
            for identity, path in [entry.split(b'\t', 1)]}


def main_revision(api):
    revision = api(f'{BASE}/branches/main').get('commit', {}).get('sha')
    if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Canonical main revision unavailable')
    return revision


def canonical_pr(pr, revision):
    return (pr.get('base', {}).get('repo', {}).get('full_name', '').lower() == REPOSITORY
            and pr.get('base', {}).get('ref') == 'main'
            and pr.get('head', {}).get('sha') == revision)


def check(root, pull_number, api=gh_api, trusted_root=ROOT):
    root = Path(root).resolve()
    trusted_root = Path(trusted_root).resolve()
    revision = clean_revision(root, 'candidate')
    trusted_revision = clean_revision(trusted_root, 'trusted main')
    if main_revision(api) != trusted_revision:
        raise ValueError('Trusted helper checkout must match authenticated canonical main SHA')
    trusted_policy = policy_tree(trusted_root)
    candidate_policy = policy_tree(root)
    source = admission.inspect(root)
    result = {'schema': 1, 'repository': REPOSITORY, 'pullRequest': pull_number,
              'sourceRevision': revision, 'sourceDigest': source['sourceDigest'],
              'trustedMainRevision': trusted_revision,
              'status': 'waiting', 'communityReviewed': False, 'publishAllowed': False,
              'scope': 'Authenticated GitHub human decision plus read-only CI; separate release checks and publication required.',
              'blockers': []}
    policy_changes = sorted(path for path in set(candidate_policy) | set(trusted_policy)
                            if candidate_policy.get(path) != trusted_policy.get(path))
    result['executionPolicyChanges'] = policy_changes
    if policy_changes:
        result['blockers'].append('Execution policy differs from trusted main; separate owner policy review required')
    if any(c.get('license') != 'MIT' for c in source['metadata']['components']):
        result['blockers'].append('MIT source licensing required')
    pr = api(f'{BASE}/pulls/{pull_number}')
    if not canonical_pr(pr, revision):
        raise ValueError('Candidate SHA or canonical main base repository mismatch')
    if pr.get('draft') or pr.get('state') != 'open':
        result['blockers'].append('Open ready-for-review PR required')
    author = pr.get('user', {}).get('login', '').lower()
    if not author:
        raise ValueError('PR author identity missing')
    reviews = pages(api, f'{BASE}/pulls/{pull_number}/reviews')
    effective = {}
    # GitHub returns reviews chronologically. COMMENTED/PENDING do not revoke an
    # approval; a later decision/dismissal does. Match IDs rather than trusting
    # claimed author_association or contributor metadata.
    for review in sorted(reviews, key=lambda r: r['id']):
        login = review.get('user', {}).get('login', '')
        if review.get('state') in ('APPROVED', 'CHANGES_REQUESTED', 'DISMISSED'):
            effective[login.lower()] = review
    approvals = []
    blocking_reviews = []
    for login, review in effective.items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,38}', login) or login == author or review.get('user', {}).get('type') != 'User':
            continue
        if review.get('state') not in ('APPROVED', 'CHANGES_REQUESTED') or review.get('commit_id') != revision or not review.get('submitted_at'):
            continue
        permission = api(f'{BASE}/collaborators/{login}/permission')
        if permission.get('role_name') in ('maintain', 'admin') and permission.get('user', {}).get('id') == review['user'].get('id') and permission.get('user', {}).get('login', '').lower() == login:
            decisions = approvals if review['state'] == 'APPROVED' else blocking_reviews
            decisions.append({'reviewId': review['id'], 'reviewer': login, 'reviewerId': review['user']['id'],
                              'role': permission['role_name'], 'sourceRevision': revision,
                              'url': f'https://github.com/{REPOSITORY}/pull/{pull_number}#pullrequestreview-{review["id"]}'})
    if blocking_reviews:
        result['blockers'].append('Current-head changes requested by an existing maintain/admin human must be resolved')
    if not approvals:
        result['blockers'].append('Independent current-head approval by an existing maintain/admin human required')
    workflow = api(f'{BASE}/actions/workflows/checks.yml')
    if workflow.get('path') != '.github/workflows/checks.yml' or type(workflow.get('id')) is not int:
        raise ValueError('Canonical component check workflow unavailable')
    runs = api(f'{BASE}/actions/workflows/{workflow["id"]}/runs?head_sha={revision}&event=pull_request&per_page=100')
    eligible = [run for run in runs.get('workflow_runs', []) if run.get('workflow_id') == workflow['id'] and run.get('head_sha') == revision and run.get('event') == 'pull_request' and any(p.get('number') == pull_number for p in run.get('pull_requests', []))]
    # A failed/incomplete rerun supersedes an older success.
    latest = max(eligible, key=lambda r: (r['id'], r.get('run_attempt', 1)), default=None)
    if not latest or latest.get('status') != 'completed' or latest.get('conclusion') != 'success':
        result['blockers'].append('Successful current-head canonical read-only Component checks required')
    # Reauthenticate main and both clean checkouts after authority/CI reads.
    if main_revision(api) != trusted_revision or clean_revision(trusted_root, 'trusted main') != trusted_revision or policy_tree(trusted_root) != trusted_policy:
        raise ValueError('Trusted main changed during acceptance check')
    if not canonical_pr(api(f'{BASE}/pulls/{pull_number}'), revision) or clean_revision(root, 'candidate') != revision or policy_tree(root) != candidate_policy:
        raise ValueError('Candidate changed during acceptance check')
    if admission.inspect(root)['sourceDigest'] != source['sourceDigest']:
        raise ValueError('Candidate source digest changed during acceptance check')
    result['approvals'] = approvals
    result['blockingReviews'] = blocking_reviews
    result['checkRun'] = {'id': latest['id'], 'url': f'https://github.com/{REPOSITORY}/actions/runs/{latest["id"]}'} if latest else None
    if not result['blockers']:
        result.update(status='accepted', communityReviewed=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Clean candidate checkout; run helper from clean authenticated canonical main')
    parser.add_argument('--pull-request', type=int, required=True)
    args = parser.parse_args()
    if args.pull_request < 1:
        parser.error('positive PR number required')
    try:
        result = check(args.root, args.pull_request)
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        result = {'schema': 1, 'repository': REPOSITORY, 'status': 'waiting', 'communityReviewed': False,
                  'publishAllowed': False, 'blockers': [str(error)]}
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'accepted' else 1


if __name__ == '__main__':
    sys.exit(main())
