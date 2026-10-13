"""Fixed-instance fanout repair of authenticated D094 native placement."""
import cloud_prects_fanout as repair

repair.SOURCE=repair.ROOT/'build/prects_native_estimator'
repair.OUT=repair.ROOT/'build/native_fanout'
repair.INSTANCE_COUNT=3670
repair.SOURCE_RUN=38339209412
repair.RESULT_SHA='c22a7e67b1e41e900a388e37c18cfb4ab664f05bac5b860e8f56b7fea03d3b96'
repair.EXPECTED={'odb':'7ac798a50557b00b27d453c1d998622fac953298915322bbef7612123454da96',
 'nl':'eb7d5e8763e0e0795eaf91e6008025b340f3b3e0db0075df285690e38e16f7e2',
 'sdc':'2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e'}

if __name__=='__main__':repair.main()
