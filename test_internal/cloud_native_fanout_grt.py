"""Unchanged-policy native routing of the authenticated D094 repaired layout."""
import cloud_native_fanout  # binds the measured producer count and source
import cloud_prects_fanout_grt as route

route.INPUT=route.ROOT/'build/native_fanout_grt_input'
route.OUT=route.ROOT/'build/native_fanout_grt'
route.SOURCE_RUN=38452773248
route.RESULT_SHA='b804c57b3de1a1096535686d2adcdfcbb8904766218891fdfa32d826c278b946'
route.CANDIDATE={'odb':'71cb27c8286ce75f9d3f9410313b7750806807ac0d44982ff55e7fb6631db2ca',
 'nl':'68b84c6685afe023e850582c0362d9047888f0991d2620003b5698cf3a98ed22',
 'sdc':route.adapter.SDC_SHA}

if __name__=='__main__':route.main()
