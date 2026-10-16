"""Read-only portable audit of hosted G0/G1 artifacts against exact Git objects.

Uses the existing compile evidence validator. Never launches EDA or workflows.
Run with PYTHONPATH=tools from the project venv; no network access is needed.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'test_internal'))
import cloud_arch_comparison as hosted

TILES_REV = '7999e5a91dab77357fe9d401b6dfb0758f438bf1'
TILES_PREFIX = 'build/third_party/fabulous-tiles/'
RUNNER_PREFIX = '/home/runner/work/protocol-emulator-asic/protocol-emulator-asic/'
SOURCE_PREFIXES = ('arch/warp_g0', 'arch/warp_g1', 'arch/prims', 'macro/warp_g0',
                   'macro/warp_g1', 'tools/compile', 'tools/host', 'scripts/fetch_tiles.sh',
                   'scripts/fetch_nextpnr.sh', 'requirements-dev.txt')
TOOL_HASHES = {
    'yosys': '7c3e3396b38c129dd7485be5a0a0f0da8e495a94c8fd486059e3bea043a588d6',
    'nextpnr-generic': 'a36179428d1afb5c9b88950097f03473f22949a39be1ac5cf6e5f3a95b526829',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or str(p) != name:
        raise ValueError('Unsafe or noncanonical evidence path')
    return name


class GitInputs:
    """Read blobs only at explicit revisions; never consult working tree data."""
    def __init__(self, revision, repository=ROOT, tile_repository=None):
        if not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise ValueError('Exact forty-digit project revision required')
        self.revision = revision
        self.repository = Path(repository)
        self.tile_repository = Path(tile_repository or ROOT/'build/third_party/fabulous-tiles')

    def git(self, repository, *args):
        try:
            return subprocess.check_output(['git', '-C', str(repository), *args], timeout=30,
                                           stderr=subprocess.PIPE)
        except subprocess.SubprocessError as exc:
            raise ValueError('Required pinned Git object unavailable') from exc

    def list_paths(self, repository, revision, paths=()):
        return self.git(repository, 'ls-tree', '-r', '--name-only', revision, '--', *paths).decode().splitlines()

    def expected_paths(self):
        names = set(self.list_paths(self.repository, self.revision, SOURCE_PREFIXES))
        for design in hosted.DESIGNS:
            prefix = 'protocols/'+design+'/'
            names.update(p for p in self.list_paths(self.repository, self.revision, [prefix])
                         if p == prefix+'pins.yaml' or (p.startswith(prefix) and '/' not in p[len(prefix):] and p.endswith('.v')))
        names.update(['test_internal/cloud_arch_comparison.py', '.github/workflows/arch_comparison_evidence.yaml'])
        names.update(TILES_PREFIX+p for p in self.list_paths(self.tile_repository, TILES_REV))
        return names

    def read(self, name):
        name = relative_name(name)
        if name.startswith(TILES_PREFIX):
            return self.git(self.tile_repository, 'show', TILES_REV+':'+name[len(TILES_PREFIX):])
        if (name.startswith('protocols/') and name.split('/')[1] not in hosted.DESIGNS):
            raise ValueError('Unapproved protocol input')
        return self.git(self.repository, 'show', self.revision+':'+name)


def audit(directory, *, revision, run_id, attempt, repository=ROOT, tile_repository=None):
    """Bind moved artifacts to caller-supplied GitHub identity and pinned inputs."""
    if not re.fullmatch(r'[1-9][0-9]*', str(run_id)) or not re.fullmatch(r'[1-9][0-9]*', str(attempt)):
        raise ValueError('Explicit positive run ID and attempt required')
    directory = Path(directory)
    if not directory.is_dir() or directory.is_symlink() or any(p.is_symlink() for p in directory.rglob('*')):
        raise ValueError('Missing or linked artifact bundle')
    result_path = directory/'result.json'
    result = json.loads(result_path.read_text())
    if (result['commit'] != revision or str(result['workflow_run']) != str(run_id) or
            str(result['workflow_attempt']) != str(attempt) or result['passed'] is not True or
            result['inputs_unchanged'] is not True or result['physical_acceptance'] is not False or
            result['timing_acceptance'] is not False or result['tiles_revision'] != TILES_REV):
        raise ValueError('Artifact identity/status differs from requested run')
    inputs = GitInputs(revision, repository, tile_repository)
    expected_inputs = inputs.expected_paths()
    if set(result['input_sha256']) != expected_inputs:
        raise ValueError('Missing or extra listed input fingerprints')
    for name, expected in result['input_sha256'].items():
        if digest(inputs.read(name)) != expected:
            raise ValueError('Input hash differs from exact Git object: '+name)
    tools = result['tools']
    if (result['tool_sha256'] != TOOL_HASHES or 'Yosys 0.66+179' not in tools['yosys'] or
            'e74db6dea' not in tools['yosys'] or 'nextpnr-0.11.1-34-gc4fbb55a' not in tools['nextpnr-generic'] or
            result['timing_corner'] != hosted.compiler.SLOW_CORNER or result['assessment_clock_mhz'] != 50):
        raise ValueError('Pinned tool identity or timing assessment differs')
    expected_cases = {arch+'__'+design for arch in hosted.ARCHES for design in hosted.DESIGNS}
    if set(result['cases']) != expected_cases:
        raise ValueError('Incomplete or unapproved eight-case matrix')
    allowed_root = expected_cases | {case+'.log' for case in expected_cases} | {'result.json'}
    if not {p.name for p in directory.iterdir()} <= allowed_root:
        raise ValueError('Unapproved top-level artifact contents')

    def input_name(path):
        if not path.startswith(RUNNER_PREFIX):
            raise ValueError('Unknown original runner input path')
        name = relative_name(path[len(RUNNER_PREFIX):])
        if name not in expected_inputs:
            raise ValueError('Unlisted compile input')
        return name

    verified, image_count = {}, 0
    for case in sorted(expected_cases):
        arch, design = case.split('__')
        location = directory/case
        stated = result['cases'][case]
        if type(stated['fits']) is not bool or stated['tools'] != tools:
            raise ValueError('Invalid case outcome or tool identity')
        for name in stated['artifact_sha256']:
            relative_name(name)
        if {str(p.relative_to(location)) for p in location.rglob('*') if p.is_file()} != set(stated['artifact_sha256']):
            raise ValueError('Actual files differ from recorded case inventory')
        spec = yaml.safe_load(inputs.read('protocols/'+design+'/pins.yaml'))
        meta = yaml.safe_load(inputs.read('arch/'+arch+'/arch.yaml'))
        if stated['fits']:
            report = json.loads((location/'report.json').read_text())
            actual_names = [input_name(row['path']) for row in report['provenance']['inputs']]
            fab = meta['macro']+'/fabulous/'
            expected_names = {name for name in expected_inputs if name.startswith('protocols/'+design+'/')}
            expected_names.update({'arch/'+arch+'/arch.yaml', 'arch/'+arch+'/pins.csv', fab+'bitStreamSpec.bin',
                                   'tools/compile/compile.py', 'tools/compile/bitgen.py', 'tools/compile/bitfile.py'})
            expected_names.update(name for name in expected_inputs
                                  if name.startswith(fab+'.FABulous/') and name.endswith('.txt') and
                                  '/' not in name[len(fab+'.FABulous/'):])
            if meta.get('primitives'):
                expected_names.add('tools/compile/prims/warp_prims.v')
            if set(actual_names) != expected_names or len(actual_names) != len(set(actual_names)):
                raise ValueError('Missing/duplicate compile provenance inputs')
            image_count += 1
        computed = hosted.validate_case(location, design, arch, source_spec=spec, source_arch=meta,
                                        read_input=lambda path: inputs.read(input_name(path)))
        if computed != stated:
            raise ValueError('Native evidence differs from recorded case: '+case)
        verified[case] = {'fits': computed['fits'], 'params': computed['params'],
                          'placed_utilisation': computed['placed_utilisation'],
                          'failure_category': computed.get('failure_category'),
                          'image_sha256': computed.get('image_sha256')}
    return {'verified': True, 'revision': revision, 'workflow_run': str(run_id), 'workflow_attempt': str(attempt),
            'result_sha256': digest(result_path.read_bytes()), 'listed_inputs': len(expected_inputs),
            'cases': verified, 'verified_images': image_count, 'physical_acceptance': False,
            'timing_acceptance': False, 'scope': 'Portable compile artifact audit; tool hashes are retained identities, no binary or EDA execution'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--tile-repository', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory, revision=args.revision, run_id=args.run_id,
                           attempt=args.attempt, tile_repository=args.tile_repository), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
