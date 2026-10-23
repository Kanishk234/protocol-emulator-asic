"""Registered LibreLane entry point for the reviewed TRIPWIRE physical chain.

The TT action still calls tt_tool --harden and LibreLane in the normal way.
This plugin exposes fresh final views and the stage reports those tools consume.
Container/native execution and main promotion require separate reviewed approval.
"""
import json
import os
from pathlib import Path

from librelane.common import Path as LLPath
from librelane.config import Variable
from librelane.flows import Flow
from librelane.flows.classic import Classic
from librelane.state import State

from physical_runtime import native
from sram_bank_clean_route import unique
from wire600_integrated_proof import main as reproduce
from prepare_official_flow import validate_source

OFFICIAL_WORKFLOW = '.github/workflows/gds.yaml'


def stage_links(root, run_dir):
    """Expose real stage directories needed by TT stats, logs and submission.

    These are links to freshly executed stages, not synthetic success receipts.
    """
    stages = [
        unique(root/'runs/native-stock-screen/flow', '*-verilator-lint'),
        unique(root/'runs/native-stock-screen/flow', '*-yosys-synthesis'),
        unique(root/'runs/native-stock-screen/flow', '*-openroad-globalplacement'),
        unique(root/'runs/extracted-timing', '*-openroad-stapostpnr'),
    ]
    for stage in stages:
        target = run_dir/stage.name
        if target.exists() or target.is_symlink():
            raise ValueError('Existing official stage alias')
        target.symlink_to(stage.resolve(), target_is_directory=True)


def chain_links(root, run_dir):
    for name in ('native-stock-screen', 'wire600-mux-margin-clean',
                 'wire600-mux-margin-route', 'extracted-timing', 'wire600-integrated-proof'):
        target = run_dir/('tripwire-'+name)
        if target.exists() or target.is_symlink():
            raise ValueError('Existing physical chain alias')
        target.symlink_to(root/'runs'/name, target_is_directory=True)


@Flow.factory.register()
class TripwireReproduced(Classic):
    name = 'TRIPWIRE reviewed source-to-GDS chain'
    config_vars = Classic.config_vars + [Variable(
        'TRIPWIRE_RUN_CONTEXT', LLPath,
        'GitHub run API receipt prepared in the current workspace before hardening.')]

    def run(self, initial_state, **kwargs):
        if not native():
            raise ValueError('TRIPWIRE flow requires its reviewed native-runtime image')
        if any(v is not None for v in initial_state.values()) or initial_state.metrics:
            raise ValueError('Official TRIPWIRE flow forbids initial physical checkpoints')
        if any(kwargs.get(k) for k in ('frm', 'to', 'skip')):
            raise ValueError('Official TRIPWIRE flow requires the complete build')
        root = Path.cwd()
        validate_source(root)
        run_dir = Path(self.run_dir)
        if run_dir.resolve() != (root/'runs/wokwi').resolve():
            raise ValueError('Official TRIPWIRE flow requires the normal TT run directory')
        context = json.loads(Path(self.config['TRIPWIRE_RUN_CONTEXT']).read_text())
        if (context.get('path') != OFFICIAL_WORKFLOW or context.get('head_branch') != 'main'
                or context.get('status') != 'in_progress' or context.get('conclusion') is not None):
            raise ValueError('Wrong live official build context')
        helpers = root/'workflow-src'
        if helpers.exists() or helpers.is_symlink():
            raise ValueError('Unexpected helper checkout in official build')
        merged = root/'src/config_merged.json'
        original = merged.read_bytes()
        # Preserve the verified recipe's staged configuration derivation: its
        # initial defaults are transformed before any tool runs. Refeeding the
        # final policy into that derivation would violate its preflight checks.
        # Main declares the final policy; these immutable inputs reconstruct it.
        config = json.loads((Path(__file__).parent.parent/
            'fixtures/wire600_selective/entry_config.json').read_text())
        config = {k: v for k, v in config.items() if not k.startswith('//')}
        config.update(json.loads((root/'src/user_config.json').read_text()))
        chain_links(root, run_dir)
        helpers.symlink_to(root, target_is_directory=True)
        environment_keys = ('GITHUB_RUN_ID', 'GITHUB_SHA', 'VARIANT', 'NATIVE_MAPPING_STRATEGY',
            'NATIVE_HOLD_TARGET', 'NATIVE_CLOCK_CLUSTER_SIZE', 'LIBRELANE_IMAGE_OVERRIDE',
            'TRIPWIRE_SELECTIVE_TARGETS')
        environment_before = {key: os.environ.get(key) for key in environment_keys}
        try:
            os.environ.update(
                GITHUB_RUN_ID=str(context['id']), GITHUB_SHA=context['head_sha'],
                VARIANT='bs-resync-cfg-tx-cached-lane-mask-drop-parallel-delta8',
                NATIVE_MAPPING_STRATEGY='AREA 1', NATIVE_HOLD_TARGET='0.10',
                NATIVE_CLOCK_CLUSTER_SIZE='8')
            Path('/tmp/wire600-clean-source-run.json').write_text(json.dumps(context)+'\n')
            merged.write_text(json.dumps(config, indent=2)+'\n')
            reproduce(workflow=OFFICIAL_WORKFLOW)
            export = root/'runs/wire600-integrated-proof/export'
            final = State.loads(unique(export, '*-checker-lvs/state_out.json').read_text())
            final.save_snapshot(run_dir/'final')
            stage_links(root, run_dir)
            (run_dir/'tripwire-reproduction.json').write_bytes(
                (root/'runs/wire600-integrated-proof/gates.json').read_bytes())
            (run_dir/'effective-native-config.json').write_bytes(
                (root/'src/config_electrical_incremental_route.json').read_bytes())
            (run_dir/'runtime-image.json').write_bytes((root/'runs/tripwire-image.json').read_bytes())
        finally:
            merged.write_bytes(original)
            helpers.unlink()
            for key, value in environment_before.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        # Child tool invocations persist all real states/reports in their run
        # directories. The outer flow exports their final State without fake steps.
        return final, []
