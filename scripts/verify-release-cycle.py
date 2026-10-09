#!/usr/bin/env python3
"""Build immutable local releases and verify real Maven install/update/revert.

Only .proof/ is generated. No remote publication, credentials or UI automation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PROOF = ROOT / '.proof'
VERSIONS = ('0.1.0', '0.1.1')
COORD_PATH = Path('school/zero/community/zero-community')
WRAPPER = 'mvnw.cmd' if os.name == 'nt' else './mvnw'


def digest(path, algorithm='sha256'):
    return hashlib.new(algorithm, path.read_bytes()).hexdigest()


def run(arguments, cwd, marker=None, timeout=180):
    result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if result.returncode or (marker and marker not in result.stdout):
        print(result.stdout[-9000:], result.stderr[-4000:], flush=True)
        raise RuntimeError(f'Check failed in {cwd}: {arguments}')
    return result.stdout


def maven(cwd, *goals, marker=None):
    return run([WRAPPER, '-B', '-s', str(PROOF / 'settings.xml'), '-gs', str(PROOF / 'settings.xml'),
                f'-Dmaven.repo.local={PROOF / "cache"}', *goals], cwd, marker)


def wrapper(dest):
    shutil.copy2(ROOT / 'mvnw', dest / 'mvnw')
    shutil.copy2(ROOT / 'mvnw.cmd', dest / 'mvnw.cmd')
    shutil.copytree(ROOT / '.mvn', dest / '.mvn', dirs_exist_ok=True)


def fresh_generated(dest):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)


def build_release(version):
    build = PROOF / 'builds' / version
    fresh_generated(build)
    wrapper(build)
    pom_source = ROOT / f'releases/{version}/pom.xml'
    pom = pom_source.read_text()
    (build / 'pom.xml').write_text(pom)
    source = ROOT / f'releases/{version}/src'
    shutil.copytree(source, build / 'src')
    goals = ['clean', 'package']
    # Baseline intentionally contains the bug that the current regression rejects.
    if version == '0.1.0':
        goals.insert(0, '-DskipTests')
    maven(build, *goals)
    if version == '0.1.1':
        tests = ET.parse(build / 'target/surefire-reports/TEST-zero.community.HealthBarTest.xml').getroot()
        assert tests.attrib['tests'] == '3' and all(tests.attrib[key] == '0' for key in ('failures', 'errors', 'skipped'))
        print('LIBRARY_TESTS_OK 3: fractions/captions, bounds/independence/reset, invalid inputs', flush=True)
    files = {
        'jar': build / 'target' / f'zero-community-{version}.jar',
        'pom': build / 'pom.xml',
        'sources': build / 'target' / f'zero-community-{version}-sources.jar',
        'javadoc': build / 'target' / f'zero-community-{version}-javadoc.jar',
    }
    with zipfile.ZipFile(files['jar']) as jar:
        classes = [name for name in jar.namelist() if name.endswith('.class')]
        assert classes == ['zero/community/HealthBar.class'], f'Unexpected bundled classes: {classes}'
    with zipfile.ZipFile(files['sources']) as sources:
        assert sources.read('zero/community/HealthBar.java') == (source / 'main/java/zero/community/HealthBar.java').read_bytes()
    with zipfile.ZipFile(files['javadoc']) as docs:
        assert 'zero/community/HealthBar.html' in docs.namelist()
    print(f'BUILD_OK {version}: library, sources, API docs; no Zero framework bundled', flush=True)
    return build, files


def install_release(version, build, files):
    directory = PROOF / 'repository' / COORD_PATH / version
    names = {'jar': f'zero-community-{version}.jar', 'pom': f'zero-community-{version}.pom',
             'sources': f'zero-community-{version}-sources.jar', 'javadoc': f'zero-community-{version}-javadoc.jar'}
    if directory.exists():
        for kind, name in names.items():
            destination = directory / name
            if not destination.exists() or digest(destination) != digest(files[kind]):
                raise RuntimeError(f'Immutable release replacement refused: {destination}')
        print(f'IMMUTABLE_REUSE {version}: all four artifact digests match', flush=True)
    else:
        maven(build, 'org.apache.maven.plugins:maven-install-plugin:3.1.4:install-file',
              f'-Dfile={files["jar"]}', f'-DpomFile={files["pom"]}',
              f'-Dsources={files["sources"]}', f'-Djavadoc={files["javadoc"]}',
              f'-DlocalRepositoryPath={PROOF / "repository"}')
        print(f'INSTALL_OK {version}: immutable local file Maven repository', flush=True)
    artifacts = {}
    for kind, name in names.items():
        path = directory / name
        assert digest(path) == digest(files[kind]), 'Installed bytes differ from build'
        for algorithm in ('sha256', 'sha1'):
            (directory / (name + '.' + algorithm)).write_text(digest(path, algorithm) + '\n')
        artifacts[kind] = {'path': (COORD_PATH / version / name).as_posix(), 'sha256': digest(path)}
    return {'version': version, 'artifacts': artifacts}


def verify_regression(fixed_build):
    mutant = PROOF / 'regression'
    fresh_generated(mutant)
    wrapper(mutant)
    shutil.copy2(fixed_build / 'pom.xml', mutant / 'pom.xml')
    shutil.copytree(fixed_build / 'src', mutant / 'src')
    shutil.copy2(ROOT / 'releases/0.1.0/src/main/java/zero/community/HealthBar.java',
                 mutant / 'src/main/java/zero/community/HealthBar.java')
    result = subprocess.run([WRAPPER, '-B', '-s', str(PROOF / 'settings.xml'), '-gs', str(PROOF / 'settings.xml'),
                             f'-Dmaven.repo.local={PROOF / "cache"}', 'clean', 'test'],
                            cwd=mutant, capture_output=True, text=True, timeout=60)
    report = mutant / 'target/surefire-reports/TEST-zero.community.HealthBarTest.xml'
    assert result.returncode != 0 and report.is_file(), 'Regression must reject the historical fraction bug'
    tests = ET.parse(report).getroot()
    rejected = {test.attrib['name'] for test in tests.findall('testcase') if test.find('error') is not None or test.find('failure') is not None}
    assert rejected == {'partialDamageShowsCorrectFractionAndCaption', 'boundsAndIndependentInstancesSurviveReset'}, rejected
    print('REGRESSION_OK: existing tests reject historical fraction bug in two independent scenarios', flush=True)
    return sorted(rejected)


def verify_immutable_refusal(build, files):
    attempt = PROOF / 'immutability-attempt'
    fresh_generated(attempt)
    changed = attempt / 'different.jar'
    changed.write_bytes(b'Different artifact bytes must never replace a release.\n')
    replaced = {**files, 'jar': changed}
    try:
        install_release('0.1.0', build, replaced)
    except RuntimeError as failure:
        assert str(failure).startswith('Immutable release replacement refused:')
    else:
        raise AssertionError('Immutable repository allowed replacement')
    installed = PROOF / 'repository' / COORD_PATH / '0.1.0/zero-community-0.1.0.jar'
    assert digest(installed) == digest(files['jar']), 'Refusal must preserve existing bytes'
    print('IMMUTABILITY_GUARD_OK: differing bytes refused; baseline JAR unchanged', flush=True)


CHECKS = {
    'adventure': '''Button hit = (Button) field(app, "hit");
        Button heal = (Button) field(app, "heal");
        Button reset = (Button) field(app, "reset");
        hit.fire();
        require((int) field(app, "health") == 75 && meter.getHealth() == 75, "Damage updates owned and displayed health");
        require(label.getText().equals("Health: 75 / 100"), "Damage updates numeric label");
        require(fill.getProgress() == (fixed ? .75 : 0.0), "Fraction distinguishes baseline from compatible fix");
        heal.fire(); require(meter.getHealth() == 85, "Healing explicitly updates component");
        for (int i = 0; i < 5; i++) hit.fire();
        require(meter.getHealth() == 0 && fill.getProgress() == 0, "Repeated damage clamps at zero");
        reset.fire(); require(meter.getHealth() == 100 && fill.getProgress() == 1, "Restart restores full health");
        for (int i = 0; i < 5; i++) heal.fire();
        require(meter.getHealth() == 100, "Healing clamps at maximum");''',
    'study': '''TextField answer = (TextField) field(app, "answer");
        Button check = (Button) field(app, "check");
        Button reset = (Button) field(app, "reset");
        Label feedback = (Label) field(app, "feedback");
        check.fire(); require(meter.getHealth() == 8, "Blank input preserves study budget");
        answer.setText(" 3 "); Event.fireEvent(answer, new javafx.event.ActionEvent());
        require((int) field(app, "energy") == 7 && meter.getHealth() == 7, "Enter spends one energy on trimmed correct answer");
        require(feedback.getText().equals("Correct!") && label.getText().equals("Study energy: 7 / 8"), "Correct result updates feedback and caption");
        require(fill.getProgress() == (fixed ? .875 : 0.0), "Fraction distinguishes baseline from compatible fix");
        answer.setText("wrong"); check.fire();
        require(meter.getHealth() == 5 && feedback.getText().equals("Try again."), "Retry spends two energy");
        for (int i = 0; i < 4; i++) check.fire();
        require(meter.getHealth() == 0 && check.isDisabled() && answer.isDisabled(), "Exhaustion clamps and locks session");
        check.fire(); require(meter.getHealth() == 0, "Exhausted session cannot spend more");
        reset.fire(); require(meter.getHealth() == 8 && fill.getProgress() == 1 && answer.getText().isEmpty()
            && !check.isDisabled() && !answer.isDisabled(), "Reset restores input and full budget");
        answer.setText("3"); check.fire(); require(meter.getHealth() == 7, "Second session spends energy again");'''
}

HARNESS = '''import javafx.application.Application;
import javafx.application.Platform;
import javafx.animation.PauseTransition;
import javafx.util.Duration;
import javafx.stage.Stage;
import javafx.event.Event;
import javafx.scene.control.*;
import javafx.scene.layout.VBox;
import zero.community.HealthBar;
public class CycleCheck extends Application {
    static Object field(Object object, String name) throws Exception {
        var field = object.getClass().getDeclaredField(name);
        field.setAccessible(true); return field.get(object);
    }
    static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public void start(Stage stage) {
        Thread watchdog = new Thread(() -> {
            try { Thread.sleep(15_000); } catch (InterruptedException ignored) { return; }
            System.err.println("CYCLE_TIMEOUT"); System.exit(1);
        });
        watchdog.setDaemon(true); watchdog.start();
        Main app = new Main(); app.start(stage);
        PauseTransition wait = new PauseTransition(Duration.millis(200));
        wait.setOnFinished(event -> {
            try {
                String version = "VERSION";
                boolean fixed = version.equals("0.1.1");
                String origin = HealthBar.class.getProtectionDomain().getCodeSource().getLocation().toString();
                require(origin.endsWith("zero-community-" + version + ".jar"), "Actual pinned dependency JAR: " + origin);
                HealthBar meter = (HealthBar) field(app, "meter");
                VBox view = (VBox) meter.view();
                Label label = (Label) view.getChildren().get(0);
                ProgressBar fill = (ProgressBar) view.getChildren().get(1);
                CHECKS
                System.out.println("CYCLE_OK KIND PHASE " + version + " origin=" + origin);
            } catch (Throwable failure) {
                failure.printStackTrace(); System.exit(1);
            } finally { app.stop(); stage.close(); Platform.exit(); }
        }); wait.play();
    }
    public static void main(String[] args) { launch(args); }
}
'''


def prepare_consumer(kind, zero_root):
    dest = PROOF / 'consumers' / kind
    fresh_generated(dest)
    wrapper(dest)
    src = dest / 'src/main/java'
    (src / 'zero').mkdir(parents=True)
    simple_app = zero_root / 'student-template/src/main/java/zero/SimpleApp.java'
    if not simple_app.is_file():
        simple_app = zero_root / 'framework/src/main/java/zero/SimpleApp.java'
    shutil.copy2(simple_app, src / 'zero/SimpleApp.java')
    shutil.copy2(ROOT / f'examples/{kind}/Main.java', src / 'Main.java')
    pom = (zero_root / 'student-template/pom.xml').read_text()
    pom = pom.replace('<app.mainClass>Main</app.mainClass>', '<app.mainClass>Main</app.mainClass>\n    <zero.community.version>0.1.0</zero.community.version>')
    pom = pom.replace('  </dependencies>', '''    <dependency><groupId>school.zero.community</groupId><artifactId>zero-community</artifactId>
      <version>${zero.community.version}</version></dependency>
  </dependencies>''')
    pom = pom.replace('  <build>', f'''  <repositories><repository><id>zero-local-proof</id><url>{(PROOF / 'repository').as_uri()}</url>
    <releases><enabled>true</enabled><checksumPolicy>fail</checksumPolicy><updatePolicy>never</updatePolicy></releases>
    <snapshots><enabled>false</enabled></snapshots></repository></repositories>
  <build>''', 1)
    (dest / 'pom.xml').write_text(pom)
    assert not any(path.name == 'HealthBar.java' for path in src.rglob('*.java'))
    return dest


def check_consumer(dest, kind, phase, version):
    pom = dest / 'pom.xml'
    text = pom.read_text()
    for old in VERSIONS:
        text = text.replace(f'<zero.community.version>{old}</zero.community.version>', f'<zero.community.version>{version}</zero.community.version>')
    pom.write_text(text)
    check = HARNESS.replace('VERSION', version).replace('CHECKS', CHECKS[kind]).replace('KIND', kind).replace('PHASE', phase)
    (dest / 'src/main/java/CycleCheck.java').write_text(check)
    marker = f'CYCLE_OK {kind} {phase} {version}'
    output = maven(dest, '-Dapp.mainClass=CycleCheck', 'clean', 'compile', 'javafx:run', marker=marker)
    print(next(line for line in output.splitlines() if line.startswith(marker)), flush=True)
    cached = PROOF / 'cache' / COORD_PATH / version / f'zero-community-{version}.jar'
    released = PROOF / 'repository' / COORD_PATH / version / cached.name
    assert digest(cached) == digest(released), 'Consumer did not resolve exact released bytes'
    fraction = (0.75 if kind == 'adventure' else 0.875) if version == '0.1.1' else 0.0
    return {'app': kind, 'phase': phase, 'version': version, 'jarSha256': digest(cached),
            'fractionAfterFirstAction': fraction}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zero-root', required=True, type=Path)
    args = parser.parse_args()
    zero_root = args.zero_root.resolve()
    assert any((zero_root / path).is_file() for path in ('student-template/src/main/java/zero/SimpleApp.java', 'framework/src/main/java/zero/SimpleApp.java')), 'Supply the local Zero checkout'
    started = time.monotonic()
    if PROOF.exists() and not (PROOF / '.generated-by-zero-community').exists():
        raise RuntimeError('Refusing to use an unrecognized .proof directory')
    PROOF.mkdir(exist_ok=True)
    (PROOF / '.generated-by-zero-community').write_text('Generated local release proof only.\n')
    (PROOF / 'settings.xml').write_text('<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"/>\n')
    metadata = json.loads((ROOT / 'catalog/components.json').read_text())
    metadata['library']['version'] = VERSIONS[-1]  # Historical fixture catalog, never public discovery.
    assert {item['id'] for item in metadata['components'][0]['examples']} == set(CHECKS)
    consumers = {kind: prepare_consumer(kind, zero_root) for kind in CHECKS}
    baseline_build, baseline_files = build_release('0.1.0')
    baseline = install_release('0.1.0', baseline_build, baseline_files)
    events = [check_consumer(dest, kind, 'install', '0.1.0') for kind, dest in consumers.items()]
    fixed_build, fixed_files = build_release('0.1.1')
    fixed = install_release('0.1.1', fixed_build, fixed_files)
    regression = verify_regression(fixed_build)
    verify_immutable_refusal(baseline_build, baseline_files)
    events.extend(check_consumer(dest, kind, 'update', '0.1.1') for kind, dest in consumers.items())
    events.extend(check_consumer(dest, kind, 'revert', '0.1.0') for kind, dest in consumers.items())
    for release in (baseline, fixed):
        for artifact in release['artifacts'].values():
            assert digest(PROOF / 'repository' / artifact['path']) == artifact['sha256'], 'Release changed during cycle'
    revision_result = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    revision = revision_result.stdout.strip() if revision_result.returncode == 0 else None
    catalog = {'schemaVersion': 1, 'library': metadata['library'], 'components': metadata['components'],
               'latest': '0.1.1', 'origin': 'local-proof', 'repositorySubdirectory': 'repository',
               'sourceRevision': revision, 'releases': [baseline, fixed]}
    (PROOF / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    receipt = {'schemaVersion': 1, 'checks': events, 'releasesRetained': True,
               'libraryTestsPassed': 3,
               'historicalBugRejectedBy': regression, 'immutableReplacementRefused': True,
               'frameworkBundled': False, 'componentSourceCopiedToConsumers': False,
               'elapsedSeconds': round(time.monotonic() - started, 2),
               'scope': 'finite JavaFX synthetic checks; no physical input or publication'}
    (PROOF / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'PROOF_OK {len(events)} consumer checks; both immutable releases retained ({receipt["elapsedSeconds"]}s)', flush=True)


if __name__ == '__main__':
    main()
