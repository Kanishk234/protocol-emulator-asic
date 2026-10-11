"""Test interaction of two individually measured reset placement policies.

Original146 source; never assume145 and136 reductions add. Exact26-instance
plan, native legality/power/connectivity and six electrical guards precede GRT.
"""
import cloud_reset643_whitespace as trial

trial.INPUT = trial.ROOT/'build/reset_combined_input'
trial.OUT = trial.ROOT/'build/reset_combined'
trial.PLAN = dict(trial.PLAN, **{'u_shell.u_spi._251__684': {
    'before':[89280,510300,91200,514080],
    'after':[91680,502740,93600,506520]}})

def main():
    import json
    try:
        trial.main()
    finally:
        path=trial.OUT/'result.json'
        if path.exists():
            result=json.loads(path.read_text())
            result['scope']='Combined net683 and receiver-local net643 placement interaction'
            result['independent_route_controls']={'original':146,'net683':136,'net643_row':145}
            path.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__': main()
