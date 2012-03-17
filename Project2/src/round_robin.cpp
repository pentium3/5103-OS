#include "round_robin.h"

extern INIReader* settings;

cRoundRobin::cRoundRobin(): blockedID(0) {
	/* ---- Set Defaults ---- */
	settings->addDefault("R-R", "quanta", "5");

	quantum = EXTRACTP(int, R-R, quanta);

	runningProc = NULL;
	clockTicksUsed = 0;

	blockedVector.resize(4);
	totalBlocked = 0;

	return;

}

cRoundRobin::~cRoundRobin() {

	return;
}

void cRoundRobin::initProcScheduleInfo(sProc* proc) {
	assert( proc != NULL );

	roundRobinInfo* newInfoStruct = (roundRobinInfo*) malloc(sizeof(roundRobinInfo));
	proc->scheduleData = newInfoStruct;

	return;
}

void cRoundRobin::addProcesses(vector<sProc*>& procs) {
	vector<sProc*>::iterator it;

	for ( it = procs.begin(); it != procs.end(); ++it ) {
		initProcScheduleInfo(*it);

		readyQueue.push(*it);
	}

	return;
}

void cRoundRobin::setBlocked(sProc* proc) {
	assert( proc != NULL );
	assert( proc == runningProc );

	unsigned int newID = blockedID.getID();
	if ( newID >= blockedVector.size() ) {
		/* Resize the vector */
		blockedVector.resize(blockedVector.size() * 2);
	}

	/* Carry the index with the process */
	roundRobinInfo* info = (roundRobinInfo*) proc->scheduleData;
	info->blockedIndex = newID;

	blockedVector.at(newID) = proc;

	++totalBlocked;
	runningProc = NULL;

	// Reset the clock ticks since we will be picking a new process to run.
	clockTicksUsed = 0;

	return;
}

void cRoundRobin::unblockProcess(sProc* proc) {
	assert( proc != NULL );
	assert( totalBlocked > 0 );

	roundRobinInfo* info = (roundRobinInfo*) proc->scheduleData;
	assert(info->blockedIndex < blockedVector.size());

	readyQueue.push(blockedVector[info->blockedIndex]);
	blockedID.returnID(info->blockedIndex);

	--totalBlocked;

	//pthread_cond_signal(&allBlocked);

	return;
}

void cRoundRobin::removeProcess(sProc* proc) {
	assert( proc != NULL );
	assert( proc == runningProc );

	free( proc->scheduleData );

	runningProc = NULL;
	clockTicksUsed = 0;

	return;
}

sProc* cRoundRobin::getNextToRun() {

	if ( runningProc != NULL) {
	    if (clockTicksUsed >= quantum){ // Has the running process used up it's quantum?
	        readyQueue.push(runningProc);
	        // Reset the clock ticks since we will be picking a new process to run.
	        clockTicksUsed = 0;

	        runningProc = NULL;
	    } else{
	        clockTicksUsed++;

            return runningProc;
	    }
	}

	if ( readyQueue.size() == 0 ) {
		return NULL;

		//if ( totalBlocked > 0) {
		//	while ( readyQueue.size() == 0)
		//		pthread_cond_wait(&allBlocked, &blockedLock);

		//} else {
		//	/* Nothing is left to run */
		//	pthread_mutex_unlock(&blockedLock);
		//	return NULL;
		//}
	}

	sProc* toRun = readyQueue.front();
	readyQueue.pop();

	assert(toRun != NULL);

	runningProc = toRun;
	clockTicksUsed++;

	//pthread_mutex_unlock(&blockedLock);


	return toRun;
}

int cRoundRobin::numProcesses() {
	int total = 0;
	total += readyQueue.size();
	total += totalBlocked;

	total += (runningProc == NULL) ? 0 : 1;

	return total;
}
