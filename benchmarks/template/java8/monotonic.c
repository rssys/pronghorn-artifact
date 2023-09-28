#include <time.h>
#include <stdio.h>

int main() {
	struct timespec tms;
    if(clock_gettime(CLOCK_MONOTONIC, &tms)) {
        return -1;
    }
    long long int nanosecs = tms.tv_sec * 1000000000;
    nanosecs += tms.tv_nsec;
    printf("%lld\n", nanosecs);
	return 0;
}