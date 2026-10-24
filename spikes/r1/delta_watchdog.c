/* Diagnostic-only VPI observer: counts zero-time activity, never changes signals.
 * A watchdog stop is a failed experiment, never an acceptance result. */
#include <vpi_user.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef struct watch { vpiHandle h; char *name; uint64_t time; unsigned count; struct watch *next; } watch;
static watch *head;
static int done;
static PLI_INT32 changed(p_cb_data cb) {
    watch *w=(watch *)cb->user_data;
    s_vpi_time t={.type=vpiSimTime};vpi_get_time(NULL,&t);
    uint64_t now=((uint64_t)t.high<<32)|t.low;
    if(w->time!=now){w->time=now;w->count=0;}
    w->count++;
    if(!done && w->count>1000) {
        done=1;vpi_printf("DELTA_WATCHDOG stuck at tick %llu; signal %s changed %u times\n",(unsigned long long)now,w->name,w->count);
        for(int n=0;n<20;n++) {
            watch *best=NULL;
            for(watch *p=head;p;p=p->next)if(p->time==now && (!best || p->count>best->count))best=p;
            if(!best || !best->count)break;
            s_vpi_value value={.format=vpiBinStrVal};vpi_get_value(best->h,&value);
            vpi_printf("DELTA_SIGNAL %u %s = %s\n",best->count,best->name,value.value.str);
            best->count=0;
        }
        /* A deferred vpiFinish can wait forever for a nonconverging timestamp.
         * Abort this diagnostic process explicitly; missing XML is a failure. */
        fflush(stdout);fflush(stderr);_Exit(2);
    }
    return 0;
}
static void scan(vpiHandle scope) {
    for(int i=0;i<2;i++) {
        vpiHandle it=vpi_iterate(i?vpiReg:vpiNet,scope),h;
        if(it)while((h=vpi_scan(it))) {
            watch *w=calloc(1,sizeof(*w));w->h=h;w->name=strdup(vpi_get_str(vpiFullName,h));w->next=head;head=w;
            s_cb_data cb={.reason=cbValueChange,.cb_rtn=changed,.obj=h,.user_data=(PLI_BYTE8 *)w};
            s_vpi_time time={.type=vpiSuppressTime};s_vpi_value value={.format=vpiSuppressVal};cb.time=&time;cb.value=&value;
            vpi_register_cb(&cb);
        }
    }
    vpiHandle it=vpi_iterate(vpiModule,scope),h;
    if(it)while((h=vpi_scan(it)))scan(h);
}
static PLI_INT32 enable(p_cb_data unused) {
    scan(NULL);unsigned n=0;for(watch *p=head;p;p=p->next)n++;vpi_printf("DELTA_WATCHDOG armed %u signals\n",n);fflush(stdout);return 0;
}
static PLI_INT32 startup(p_cb_data unused) {
    const char *requested=getenv("WARP_DELTA_START_TICKS");
    uint64_t target=requested?strtoull(requested,NULL,10):0;vpi_printf("DELTA_WATCHDOG startup target %llu\n",(unsigned long long)target);fflush(stdout);
    s_vpi_time time={.type=vpiSimTime,.high=target>>32,.low=target&0xffffffff};
    s_cb_data cb={.reason=cbAfterDelay,.cb_rtn=enable,.time=&time};vpi_register_cb(&cb);return 0;
}
static void register_watchdog(void) {
    s_cb_data cb={.reason=cbStartOfSimulation,.cb_rtn=startup};vpi_register_cb(&cb);
}
void (*vlog_startup_routines[])(void)={register_watchdog,0};
