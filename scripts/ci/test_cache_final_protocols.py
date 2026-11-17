import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from cache_final_protocols import SHARDS, ALL_TESTS, check_xml, aggregate, FINAL_NL_SHA, ROUTE_RUN


def xml(path, shard):
    root=ET.Element('testsuite')
    for name in SHARDS[shard]:
        ET.SubElement(root,'testcase',name=name,classname='test_l3',sim_time_ns='100')
    ET.ElementTree(root).write(path)


def test_complete_suite_and_missing_case(tmp_path):
    identity=dict(netlist_sha256=FINAL_NL_SHA,route_run=ROUTE_RUN,sigrok_required=True,
                  simulator='Icarus Verilog 13',model_pdk_revision='89d42ee6d2fd9b50b86a1aada6fee6673c3e6008',
                  model_hashes={str(i):str(i) for i in range(4)},replay={'expected_tests':22})
    for shard in SHARDS:
        p=tmp_path/f'results_{shard}.xml';xml(p,shard)
        (tmp_path/f'receipt_{shard}.json').write_text(json.dumps({'results':check_xml(p,shard),'identity':identity}))
    aggregate(tmp_path,tmp_path/'out')
    assert json.loads((tmp_path/'out/summary.json').read_text())['passed']==22
    p.unlink()
    with pytest.raises(ValueError,match='Missing/duplicate'):aggregate(tmp_path,tmp_path/'out2')


@pytest.mark.parametrize('damage',['skip','fail','duplicate','missing'])
def test_reject_incomplete_execution(tmp_path,damage):
    p=tmp_path/'cases.xml';xml(p,'serial');tree=ET.parse(p);root=tree.getroot();case=root[0]
    if damage=='skip':ET.SubElement(case,'skipped')
    elif damage=='fail':ET.SubElement(case,'failure')
    elif damage=='duplicate':root.append(case)
    else:root.remove(case)
    tree.write(p)
    with pytest.raises(ValueError):check_xml(p,'serial')
