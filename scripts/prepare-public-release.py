#!/usr/bin/env python3
"""Build/check a clean committed public candidate. Does not publish or accept it."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import admission

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'codepetca/zero-community'
MAVEN_BASE = 'https://zero.codepet.ca/community/maven'
COORD = 'school/zero/community/zero-community'
NS = {'m': 'http://maven.apache.org/POM/4.0.0'}


def command(arguments, root, timeout=180):
    env = os.environ.copy()
    for name in ('MAVEN_ARGS', 'MAVEN_OPTS', 'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS'):
        env.pop(name, None)
    result = subprocess.run(arguments, cwd=root, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError('Check failed: ' + ' '.join(map(str, arguments)) + '\n' + result.stdout[-5000:] + result.stderr[-3000:])
    return result.stdout


def committed_source(root):
    root = Path(root).resolve()
    if command(['git', 'status', '--porcelain', '--untracked-files=normal'], root).strip():
        raise ValueError('Release requires clean committed source; commit edits first')
    revision = command(['git', 'rev-parse', 'HEAD'], root).strip()
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Expected exact source commit SHA')
    source = admission.inspect(root)
    tracked = set(command(['git', 'ls-files', '-z'], root).split('\0')) - {''}
    if not {f['path'] for f in source['files']} <= tracked:
        raise ValueError('Owned release source must be committed')
    library = source['metadata']['library']
    if library != {'groupId': 'school.zero.community', 'artifactId': 'zero-community', 'version': library.get('version'), 'javaRelease': 17, 'javafxVersion': '21.0.12'} or not re.fullmatch(r'0\.1\.[2-9][0-9]*|0\.1\.1[0-9]+', str(library.get('version', ''))):
        raise ValueError('Expected fixed public library coordinates and version >= 0.1.2')
    if any(c.get('license') != 'MIT' for c in source['metadata']['components']):
        raise ValueError('Public components require MIT')
    pom = ET.fromstring((root / 'pom.xml').read_bytes())
    if pom.findtext('m:licenses/m:license/m:name', namespaces=NS) != 'MIT License':
        raise ValueError('POM needs MIT license metadata')
    return revision, source, tracked


def new_output(root, output):
    root, output = Path(root).resolve(), Path(os.path.abspath(output))
    if output.exists() or output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise ValueError('New output without symlink parents required; overwrite refused')
    if not output.is_relative_to(root / '.proof'):
        raise ValueError('Output must stay under this source checkout\'s ignored .proof directory')
    return output


def verify_artifacts(root, files, source):
    notice = (root / 'LICENSE').read_bytes()
    for kind in ('jar', 'sources', 'javadoc'):
        with zipfile.ZipFile(files[kind]) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate artifact entries')
            license_path = 'resources/LICENSE' if kind == 'javadoc' else 'META-INF/LICENSE'
            if archive.read(license_path) != notice:
                raise ValueError('Canonical MIT notice missing or changed in ' + kind)
            if kind == 'jar' and sorted(n for n in names if n.endswith('.class')) != ['zero/community/HealthBar.class']:
                raise ValueError('Unexpected classes; library must not bundle Zero')
            if kind == 'sources' and archive.read('zero/community/HealthBar.java') != (root / 'src/main/java/zero/community/HealthBar.java').read_bytes():
                raise ValueError('Source JAR differs from source')
            if kind == 'javadoc' and 'zero/community/HealthBar.html' not in names:
                raise ValueError('HealthBar API JAR missing')
    if files['pom'].read_bytes() != (root / 'pom.xml').read_bytes():
        raise ValueError('Released POM differs from committed POM')
    version = source['metadata']['library']['version']
    names = {'jar': f'zero-community-{version}.jar', 'pom': f'zero-community-{version}.pom',
             'sources': f'zero-community-{version}-sources.jar', 'javadoc': f'zero-community-{version}-javadoc.jar'}
    return {kind: {'path': f'{COORD}/{version}/{names[kind]}',
                   'size': path.stat().st_size, 'sha256': admission.digest(path.read_bytes()), 'url': None}
            for kind, path in files.items()}


def consumer_checks(root, zero_root, work, files, version):
    spec = importlib.util.spec_from_file_location('cycle', root / 'scripts/verify-release-cycle.py')
    cycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cycle)
    cycle.ROOT, cycle.PROOF = root, work
    repo = work / 'repository' / COORD / version
    repo.mkdir(parents=True)
    for path in files.values():
        shutil.copyfile(path, repo / path.name)
        for algorithm in ('sha1', 'sha256'):
            import hashlib
            (repo / (path.name + '.' + algorithm)).write_text(hashlib.new(algorithm, path.read_bytes()).hexdigest() + '\n')
    result = []
    for kind in ('adventure', 'study'):
        dest = cycle.prepare_consumer(kind, zero_root)
        pom = dest / 'pom.xml'
        pom.write_text(pom.read_text().replace('<zero.community.version>0.1.0</zero.community.version>', f'<zero.community.version>{version}</zero.community.version>'))
        check = cycle.HARNESS.replace('VERSION', version).replace('CHECKS', cycle.CHECKS[kind]).replace('KIND', kind).replace('PHASE', 'public-candidate').replace('boolean fixed = version.equals("0.1.1");', 'boolean fixed = true;')
        (dest / 'src/main/java/CycleCheck.java').write_text(check)
        marker = f'CYCLE_OK {kind} public-candidate {version}'
        cycle.maven(dest, '-Dapp.mainClass=CycleCheck', 'clean', 'compile', 'javafx:run', marker=marker)
        cached = work / 'cache' / COORD / version / files['jar'].name
        if cached.read_bytes() != files['jar'].read_bytes():
            raise ValueError('Consumer did not resolve checked artifact')
        result.append({'app': kind, 'version': version, 'jarSha256': admission.digest(cached.read_bytes()), 'status': 'passed'})
    return result


def prepare(root, zero_root, output=None):
    root, zero_root = Path(root).resolve(), Path(zero_root).resolve()
    revision, source, tracked = committed_source(root)
    version = source['metadata']['library']['version']
    output = new_output(root, output or root / '.proof/public' / version)
    if not any((zero_root / path).is_file() for path in ('student-template/src/main/java/zero/SimpleApp.java', 'framework/src/main/java/zero/SimpleApp.java')):
        raise ValueError('Supply the sibling Zero source checkout for two-app verification')
    proof = root / '.proof'
    marker = proof / '.generated-by-zero-community'
    if proof.exists() and not marker.is_file():
        raise ValueError('Unrecognized .proof directory; use a fresh disposable checkout')
    proof.mkdir(exist_ok=True)
    marker.write_text('Generated local community verification only.\n')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Temporary generation is removed on failure; final directory is exclusively new.
    with tempfile.TemporaryDirectory(prefix='release-', dir=output.parent) as temporary:
        work = Path(temporary)
        build = work / 'build'
        build.mkdir()
        for name in sorted(tracked):
            path = root / name
            if path.is_symlink():
                raise ValueError('Tracked symlink is not a release build input: ' + name)
            destination = build / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        (work / 'settings.xml').write_text('<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"/>\n')
        wrapper = 'mvnw.cmd' if os.name == 'nt' else './mvnw'
        arguments = [wrapper, '-B', '-s', str(work / 'settings.xml'), '-gs', str(work / 'settings.xml'), f'-Dmaven.repo.local={work / "cache"}', 'clean', 'package']
        command(arguments, build)
        released_pom = work / f'zero-community-{version}.pom'
        shutil.copyfile(build / 'pom.xml', released_pom)
        files = {'jar': build / 'target' / f'zero-community-{version}.jar',
                 'pom': released_pom, 'sources': build / 'target' / f'zero-community-{version}-sources.jar',
                 'javadoc': build / 'target' / f'zero-community-{version}-javadoc.jar'}
        first = verify_artifacts(root, files, source)
        tests = ET.parse(build / 'target/surefire-reports/TEST-zero.community.HealthBarTest.xml').getroot()
        if tests.attrib.get('tests') != '3' or any(tests.attrib.get(key) != '0' for key in ('errors', 'failures', 'skipped')):
            raise ValueError('All three HealthBar behavior checks must pass')
        command(arguments, build)
        artifacts = verify_artifacts(root, files, source)
        if first != artifacts:
            raise ValueError('Repeated artifact bytes differ; candidate is not reproducible')
        consumers = consumer_checks(root, zero_root, work, files, version)
        end_revision, end_source, end_tracked = committed_source(root)
        if (end_revision, end_source['sourceDigest'], end_tracked) != (revision, source['sourceDigest'], tracked):
            raise ValueError('Source changed during release preparation')
        manifest = {'schemaVersion': 1, 'origin': 'public-release',
                    'publication': {'status': 'local', 'repository': REPOSITORY},
                    'repositoryUrl': MAVEN_BASE, 'library': source['metadata']['library'],
                    'latest': version, 'components': source['metadata']['components'],
                    'releases': [{'version': version, 'sourceRevision': revision, 'sourceDigest': source['sourceDigest'],
                                  'notes': 'First public MIT candidate; experimental HealthBar, unchanged explicit API.', 'artifacts': artifacts}]}
        receipt = {'schema': 1, 'sourceDigest': source['sourceDigest'],
                   'checks': [{'id': name, 'status': 'passed', 'evidence': detail} for name, detail in (
                       ('build-behavior', 'Two clean builds; three meaningful HealthBar JavaFX checks passed.'),
                       ('artifact-provenance', 'Reproducible four artifacts; exact source/POM/MIT notice/API and no bundled Zero.'),
                       ('reuse-compatibility', 'Adventure and study consume the exact Maven JAR and exercise explicit updates and fractional fill.'))],
                   'provenance': {'sourceRevision': revision, 'generator': 'prepare-public-release.py',
                                  'testedArtifact': {'kind': 'candidate-jar', 'version': version, 'sha256': artifacts['jar']['sha256'],
                                                     'sourceBinding': 'built-local-candidate', 'sourceDigest': source['sourceDigest']}},
                   'consumers': consumers, 'communityReviewed': False, 'publishAllowed': False,
                   'scope': 'Local finite synthetic JavaFX checks; no physical input, maintainer acceptance or publication.'}
        admission.validate_receipt(receipt, source['sourceDigest'])
        output.mkdir()
        for path in files.values():
            shutil.copyfile(path, output / path.name)
        (output / 'LICENSE').write_bytes((root / 'LICENSE').read_bytes())
        (output / 'catalog.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (output / 'checks.json').write_text(json.dumps(receipt, indent=2) + '\n')
        (output / 'SOURCE.json').write_text(json.dumps({'repository': REPOSITORY, 'sourceRevision': revision,
                                                      'sourceDigest': source['sourceDigest'], 'files': source['files']}, indent=2) + '\n')
        (output / 'SHA256SUMS').write_text(''.join(f'{admission.digest(p.read_bytes())}  {p.name}\n' for p in sorted(output.iterdir()) if p.is_file()))
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--zero-root', type=Path)
    parser.add_argument('--verify-built', type=Path, help='Read-only inspection of already-built artifact contents (CI)')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.verify_built:
            root = args.verify_built.resolve()
            source = admission.inspect(root)
            version = source['metadata']['library']['version']
            files = {'jar': root / 'target' / f'zero-community-{version}.jar',
                     'pom': root / 'pom.xml', 'sources': root / 'target' / f'zero-community-{version}-sources.jar',
                     'javadoc': root / 'target' / f'zero-community-{version}-javadoc.jar'}
            print(json.dumps(verify_artifacts(root, files, source), indent=2))
        else:
            if not args.zero_root:
                parser.error('--zero-root required for actual release preparation')
            print(json.dumps(prepare(args.root, args.zero_root, args.output), indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        print('Public candidate refused: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
