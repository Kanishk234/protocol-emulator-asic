"""Run inside the pinned image to verify the diagnostic native step interface."""
import hashlib
import inspect
import json
from pathlib import Path
import librelane
from librelane.steps import Step

cls = Step.factory.get('Odb.InsertECODiodes')
if cls is None:
    raise RuntimeError('Pinned engine has no native endpoint diode insertion step')
script = Path(librelane.__file__).parent / 'scripts/odbpy/eco_diode.py'
text = script.read_text()
if 'reader.config["DIODE_CELL"].split("/")' in text:
    fields = {'DIODE_CELL': 'sg13cmos5l_antennanp/A'}
elif 'reader.config["DIODE_PORT"]' in text:
    fields = {'DIODE_CELL': 'sg13cmos5l_antennanp', 'DIODE_PORT': 'A'}
else:
    raise RuntimeError('Unreviewed native diode interface; do not guess a repair recipe')
result = dict(step='Odb.InsertECODiodes', diode_config=fields,
              native_script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
              native_class_sha256=hashlib.sha256(inspect.getsource(cls).encode()).hexdigest(),
              full_design_qualification=False)
Path('runs/native-endpoint-interface.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
