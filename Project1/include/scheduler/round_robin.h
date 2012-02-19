#ifndef ROUND_ROBIN_H_INCLUDED
#define ROUND_ROBIN_H_INCLUDED

#include <assert.h>

#include "scheduler/scheduler.h"

#define DEF_BLOCK_VEC_SIZE 4
#define QUANTUM 2 // in clock ticks

using namespace std;

/** Round Robin Scheduler */
class cRoundRobin: public cScheduler {
	private:
        queue<ProcessInfo*> readyQueue;
        vector<ProcessInfo*> blockedVector;

        int totalBlocked;

        int clockTicksUsed;

        ProcessInfo* runningProc;

        pthread_mutex_t 	blockedLock;
		pthread_cond_t 		allBlocked;

        cIDManager blockedID;

        /* Logging */
		FILE* logStream;
		cProcessLogger* procLogger;

	public:
		cRoundRobin();
		~cRoundRobin();

		void initProcScheduleInfo(ProcessInfo*);
		void addProcess(ProcessInfo*);
		void setBlocked(ProcessInfo*);
		void unblockProcess(ProcessInfo*);
		void removeProcess(ProcessInfo*);

		ProcessInfo* getNextToRun();
		pidType numProcesses();

		void addLogger(FILE* _logStream);
		void addProcLogger(cProcessLogger* _procLogger);

};

/** Struct containing process info specific for Round-Robin scheduling */
struct roundRobinInfo {
	unsigned int blockedIndex;
};


#endif // ROUND_ROBIN_H_INCLUDED
