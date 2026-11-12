"""Select bounded wire repair on the exact diode-only native-drive recipe."""
import hashlib
import json
from pathlib import Path

BASE_SHA = '9074bd3491a40f63b66ce8f09e33c22f8b3e21601a76ffd749fd6add6b3dc9ac'


def prepare(root=Path('.')):
    root=Path(root)
    path=root/'src/config.json'
    blob=path.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=BASE_SHA:
        raise ValueError('Wrong native-drive configuration')
    config=json.loads(blob)
    selected_path=root/'spikes/phase2_stock_flow/selected_profile.json'
    selected=json.loads(selected_path.read_text())
    if selected.get('profile')!='portable_cpad_drive2':
        raise ValueError('Wrong native-drive source profile')
    if config.get('GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH') != 200:
        raise ValueError('Unexpected source wire-repair policy')
    config['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']=175
    changed=(json.dumps(config,indent=2)+'\n').encode()
    digest=hashlib.sha256(changed).hexdigest()
    selected.update(profile='portable_cpad_drive2_wire175', config_sha256=digest,
        comparison_reference_run=43178099947, comparison_reference_artifact_id=13930453234,
        comparison_reference_config_sha256=BASE_SHA,
        additional_changes_from_reference={'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH':175})
    selected['changes']['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']=175
    path.write_bytes(changed)
    selected_path.write_text(json.dumps(selected,indent=2)+'\n')
    return dict(reference_config_sha256=BASE_SHA,candidate_config_sha256=digest,
        changed_fields=['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'],physical_qualified=False)


if __name__=='__main__':
    receipt=prepare()
    out=Path('runs/wire175')
    out.mkdir(parents=True,exist_ok=True)
    (out/'profile.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
