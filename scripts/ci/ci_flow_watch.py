"""Keep verbose flow output in an artifact; emit bounded progress heartbeats."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def stop(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def run(command, log, heartbeat=30, total_timeout=6900, synthesis_timeout=900,
        docker_stats=False):
    if not command or min(heartbeat, total_timeout, synthesis_timeout) <= 0:
        raise ValueError('Positive watchdog limits and a command are required')
    if log.exists():
        raise ValueError('Refusing to overwrite an existing flow log')
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    stage = 'starting'
    stage_started = started
    modified = started
    suffix = ''
    timeout_reason = None
    print(f'Flow watchdog started; full output: {log}', flush=True)
    with log.open('w') as output, log.open(errors='replace') as reader:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True,
                                   env=dict(os.environ, PYTHONUNBUFFERED='1'))
        try:
            while True:
                now = time.monotonic()
                fresh = reader.read()
                if fresh:
                    modified = now
                    text = suffix + fresh
                    markers = re.findall(r"Running '([A-Za-z0-9_.]+)'", text)
                    if markers and markers[-1] != stage:
                        stage = markers[-1]
                        stage_started = now
                    suffix = text[-1024:]
                code = process.poll()
                if code is not None:
                    break
                if now-started >= total_timeout:
                    timeout_reason = 'total flow deadline'
                elif stage == 'Yosys.Synthesis' and now-stage_started >= synthesis_timeout:
                    timeout_reason = 'synthesis deadline'
                print(f'Heartbeat: elapsed={now-started:.0f}s stage={stage} '
                      f'stage_elapsed={now-stage_started:.0f}s '
                      f'log_bytes={log.stat().st_size} quiet={now-modified:.0f}s', flush=True)
                if suffix:
                    print('Latest output: '+suffix.splitlines()[-1][-240:], flush=True)
                if timeout_reason:
                    print('ERROR: '+timeout_reason+'; stopping flow, retaining logs', flush=True)
                    stop(process)
                    code = 124
                    break
                if docker_stats:
                    try:
                        stats = subprocess.run(['docker', 'stats', '--no-stream', '--format',
                                                '{{.Name}} CPU={{.CPUPerc}} MEM={{.MemUsage}}'],
                                               capture_output=True, text=True, timeout=5)
                        if stats.stdout.strip():
                            print(stats.stdout.strip(), flush=True)
                    except (OSError, subprocess.TimeoutExpired):
                        print('Container statistics unavailable', flush=True)
                time.sleep(min(heartbeat, max(.01, total_timeout-(time.monotonic()-started))))
        finally:
            stop(process)
    receipt = dict(returncode=code, elapsed_seconds=time.monotonic()-started,
                   last_stage=stage, timeout_reason=timeout_reason,
                   synthesis_timeout_seconds=synthesis_timeout,
                   total_timeout_seconds=total_timeout)
    log.with_suffix('.watch.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--heartbeat', type=float, default=30)
    parser.add_argument('--total-timeout', type=float, default=6900)
    parser.add_argument('--synthesis-timeout', type=float, default=900)
    parser.add_argument('--docker-stats', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    raise SystemExit(run(command, args.log, args.heartbeat, args.total_timeout,
                         args.synthesis_timeout, args.docker_stats))
