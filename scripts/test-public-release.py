#!/usr/bin/env python3
"""Release/acceptance boundary checks. GitHub responses are mocked, never live."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
import admission

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load('public_release', 'prepare-public-release.py')
acceptance = load('github_acceptance', 'check-github-acceptance.py')


class PublicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve() / 'source'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', '.proof', 'target', '__pycache__'))
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.base = acceptance.BASE
        self.review = {'id': 20, 'user': {'login': 'maintainer', 'id': 7, 'type': 'User'}, 'state': 'APPROVED', 'commit_id': self.sha, 'submitted_at': '2026-10-09T00:00:00Z'}
        self.pr = {'base': {'repo': {'full_name': acceptance.REPOSITORY}}, 'head': {'sha': self.sha}, 'user': {'login': 'contributor'}, 'state': 'open', 'draft': False}
        self.run = {'id': 30, 'workflow_id': 10, 'head_sha': self.sha, 'event': 'pull_request', 'pull_requests': [{'number': 2}], 'status': 'completed', 'conclusion': 'success'}
        self.reviews = [self.review]
        self.role = {'role_name': 'maintain', 'permission': 'write', 'user': {'login': 'maintainer', 'id': 7}}
        self.runs = [self.run]
        self.calls = []

    def git(self, *arguments):
        return subprocess.check_output(['git', *arguments], cwd=self.root, text=True)

    def tearDown(self):
        self.temp.cleanup()

    def api(self, path):
        self.calls.append(path)
        if path == self.base + '/pulls/2':
            return self.pr
        if '/reviews?' in path:
            return self.reviews if 'page=1' in path else []
        if '/collaborators/' in path:
            return self.role
        if path == self.base + '/actions/workflows/checks.yml':
            return {'id': 10, 'path': '.github/workflows/checks.yml'}
        if '/runs?' in path:
            return {'workflow_runs': self.runs}
        raise AssertionError('Unexpected API request: ' + path)

    def checked(self):
        return acceptance.check(self.root, 2, self.api)

    def test_current_human_maintain_approval(self):
        result = self.checked()
        self.assertEqual(result['status'], 'accepted')
        self.assertTrue(result['communityReviewed'])
        self.assertFalse(result['publishAllowed'])
        self.assertEqual(result['sourceDigest'], admission.inspect(self.root)['sourceDigest'])
        self.assertTrue(all(path.startswith(self.base + '/') for path in self.calls))

    def test_admin_accepted_but_write_unknown_and_self_not_accepted(self):
        self.role['role_name'] = 'admin'
        self.assertEqual(self.checked()['status'], 'accepted')
        for role in ('write', 'triage', 'read', None):
            self.role['role_name'] = role
            self.assertEqual(self.checked()['status'], 'waiting')
        self.role['role_name'] = 'admin'
        self.pr['user']['login'] = 'Maintainer'
        self.assertEqual(self.checked()['status'], 'waiting')

    def test_stale_dismissed_pending_and_bot_wait(self):
        for state in ('DISMISSED', 'CHANGES_REQUESTED', 'PENDING', 'COMMENTED'):
            self.review['state'] = state
            self.assertEqual(self.checked()['status'], 'waiting')
        self.review['state'] = 'APPROVED'
        self.review['commit_id'] = 'a' * 40
        self.assertEqual(self.checked()['status'], 'waiting')
        self.review['commit_id'] = self.sha
        self.review['user']['type'] = 'Bot'
        self.assertEqual(self.checked()['status'], 'waiting')

    def test_superseded_approval_waits_but_comment_does_not_revoke(self):
        later = dict(self.review, id=21, state='CHANGES_REQUESTED')
        self.reviews.append(later)
        self.assertEqual(self.checked()['status'], 'waiting')
        later['state'] = 'COMMENTED'
        self.assertEqual(self.checked()['status'], 'accepted')

    def test_role_identity_mismatch_and_ci_failures_wait(self):
        self.role['user']['id'] = 8
        self.assertEqual(self.checked()['status'], 'waiting')
        self.role['user']['id'] = 7
        for key, value in [('conclusion', 'failure'), ('status', 'in_progress'), ('head_sha', 'b' * 40), ('workflow_id', 99), ('event', 'push'), ('pull_requests', [])]:
            old = self.run[key]
            self.run[key] = value
            self.assertEqual(self.checked()['status'], 'waiting')
            self.run[key] = old
        self.runs.append(dict(self.run, id=31, conclusion='failure'))
        self.assertEqual(self.checked()['status'], 'waiting')

    def test_other_current_qualified_change_request_blocks_approval(self):
        request = dict(self.review, id=21, state='CHANGES_REQUESTED', user={'login': 'reviewer', 'id': 8, 'type': 'User'})
        self.reviews.append(request)
        role = 'admin'
        def qualified(path):
            if '/collaborators/reviewer/permission' in path:
                return {'role_name': role, 'user': {'login': 'reviewer', 'id': 8}}
            return self.api(path)
        result = acceptance.check(self.root, 2, qualified)
        self.assertEqual(result['status'], 'waiting')
        self.assertEqual(len(result['approvals']), 1)
        self.assertEqual(len(result['blockingReviews']), 1)
        request['commit_id'] = 'f' * 40
        self.assertEqual(acceptance.check(self.root, 2, qualified)['status'], 'accepted')
        request['commit_id'] = self.sha
        role = 'write'
        self.assertEqual(acceptance.check(self.root, 2, qualified)['status'], 'accepted')
        role = 'maintain'
        request['state'] = 'DISMISSED'
        self.assertEqual(acceptance.check(self.root, 2, qualified)['status'], 'accepted')

    def test_review_pagination(self):
        self.reviews = [dict(self.review, id=i, state='COMMENTED') for i in range(100)]
        def paginated(path):
            if '/reviews?' in path and 'page=2' in path:
                return [self.review]
            return self.api(path)
        self.assertEqual(acceptance.check(self.root, 2, paginated)['status'], 'accepted')

    def test_head_race_and_wrong_repository_refused(self):
        reads = 0
        def racing(path):
            nonlocal reads
            if path == self.base + '/pulls/2':
                reads += 1
                if reads > 1:
                    return dict(self.pr, head={'sha': 'c' * 40})
            return self.api(path)
        with self.assertRaisesRegex(ValueError, 'changed'):
            acceptance.check(self.root, 2, racing)
        self.pr['base']['repo']['full_name'] = 'contributor/zero-community'
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            self.checked()

    def test_dirty_source_refused_before_api_and_release(self):
        (self.root / 'LICENSE').write_text('Changed')
        with self.assertRaisesRegex(ValueError, 'clean'):
            self.checked()
        self.assertEqual(self.calls, [])
        with self.assertRaisesRegex(ValueError, 'clean'):
            release.committed_source(self.root)

    def test_source_committed_fixed_coordinates_and_output_boundaries(self):
        revision, source, _ = release.committed_source(self.root)
        self.assertEqual(revision, self.sha)
        self.assertEqual(source['metadata']['library']['version'], '0.1.2')
        with self.assertRaisesRegex(ValueError, 'ignored'):
            release.new_output(self.root, self.root / 'dist')
        output = self.root / '.proof/public/0.1.2'
        output.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            release.new_output(self.root, output)

    def test_artifact_license_source_and_class_guards(self):
        work = self.root / '.proof/artifacts'
        work.mkdir(parents=True)
        files = {'pom': work / 'zero-community-0.1.2.pom'}
        files['pom'].write_bytes((self.root / 'pom.xml').read_bytes())
        contents = {'jar': {'zero/community/HealthBar.class': b'class', 'META-INF/LICENSE': (self.root / 'LICENSE').read_bytes()},
                    'sources': {'zero/community/HealthBar.java': (self.root / 'src/main/java/zero/community/HealthBar.java').read_bytes(), 'META-INF/LICENSE': (self.root / 'LICENSE').read_bytes()},
                    'javadoc': {'zero/community/HealthBar.html': b'api', 'resources/LICENSE': (self.root / 'LICENSE').read_bytes()}}
        def write():
            for kind, entries in contents.items():
                files[kind] = work / (kind + '.jar')
                with zipfile.ZipFile(files[kind], 'w') as archive:
                    for name, data in entries.items():
                        archive.writestr(name, data)
        write()
        source = admission.inspect(self.root)
        artifacts = release.verify_artifacts(self.root, files, source)
        self.assertIsNone(artifacts['jar']['url'])
        contents['jar']['zero/SimpleApp.class'] = b'framework'
        write()
        with self.assertRaisesRegex(ValueError, 'Unexpected classes'):
            release.verify_artifacts(self.root, files, source)
        del contents['jar']['zero/SimpleApp.class']
        contents['sources']['META-INF/LICENSE'] = b'wrong notice'
        write()
        with self.assertRaisesRegex(ValueError, 'MIT'):
            release.verify_artifacts(self.root, files, source)

    def test_historical_source_and_pom_preserved(self):
        for version in ('0.1.0', '0.1.1'):
            pom = (ROOT / f'releases/{version}/pom.xml').read_text()
            self.assertIn(f'<version>{version}</version>', pom)
            self.assertNotIn('<licenses>', pom)
            self.assertTrue((ROOT / f'releases/{version}/src/main/java/zero/community/HealthBar.java').is_file())


if __name__ == '__main__':
    unittest.main()
