#include "scheduler/fcfs.h"

cFCFS::cFCFS(): blockedID(0) {
	runningProc = NULL;

	pthread_mutex_init(&blockedLock, NULL);
	pthread_cond_init(&allBlocked, NULL);

	logStream = NULL;
	procLogger = NULL;

	blockedVector.resize(DEF_BLOCK_VEC_SIZE);
	totalBlocked = 0;

	return;
}

cFCFS::~cFCFS() {
	blockedVector.clear();

	/* Shouldn't be anything here */
	while ( !readyQueue.empty() )
		readyQueue.pop();

	while ( !traceUnblocked.empty() )
		traceUnblocked.pop();

	return;
}

void cFCFS::initProcScheduleInfo(ProcessInfo* proc) {
	assert( proc != NULL );

	fcfsInfo* newInfoStruct = (fcfsInfo*) malloc(sizeof(fcfsInfo));
	proc->scheduleData = newInfoStruct;

	return;
}

void cFCFS::addProcess(ProcessInfo* proc) {
	assert( proc != NULL );
	assert( proc->state == ready );
	readyQueue.push(proc);

	return;
}

void cFCFS::setBlocked(ProcessInfo* proc) {
	assert( proc != NULL );
	assert( proc->state == running );

	pthread_mutex_lock(&blockedLock);
	proc->state = blocked;

	unsigned int newID = blockedID.getID();
	if ( newID >= blockedVector.size() ) {
		/* Resize the vector */
		blockedVector.resize(blockedVector.size() * 2);
	}

	/* Carry the index with the process */
	fcfsInfo* info = (fcfsInfo*) proc->scheduleData;
	info->blockedIndex = newID;

	blockedVector[newID] = proc;

	++totalBlocked;
	runningProc = NULL;
	fprintf(logStream, "Process %d has been blocked\n", proc->pid);
	pthread_mutex_unlock(&blockedLock);

	/* Update Process info for Top */
	procLogger->writeProcessInfo(proc);

	return;
}

void cFCFS::unblockProcess(ProcessInfo* proc) {
	assert( proc != NULL );
	assert( proc->state == blocked );
	assert( totalBlocked > 0 );

	pthread_mutex_lock(&blockedLock);

	proc->state = ready;

	fcfsInfo* info = (fcfsInfo*) proc->scheduleData;
	assert(info->blockedIndex < blockedVector.size());

	readyQueue.push(blockedVector[info->blockedIndex]);
	blockedID.returnID(info->blockedIndex);

	--totalBlocked;
	traceUnblocked.push(proc->pid);

	pthread_mutex_unlock(&blockedLock);
	pthread_cond_signal(&allBlocked);

	procLogger->writeProcessInfo(proc);

	return;
}

void cFCFS::removeProcess(ProcessInfo* proc) {
	assert( proc != NULL );
	assert( proc->state == running );

	proc->state = terminated;
	free( proc->scheduleData );
	procLogger->writeProcessInfo(proc);

	runningProc = NULL;

	return;
}

void cFCFS::printUnblocked() {
	pidType tempID = 0;

	while ( traceUnblocked.size() > 0 ) {
		tempID = traceUnblocked.front();
		traceUnblocked.pop();
		fprintf(logStream, "Process %d unblocked\n", tempID);
	}

	//For the output to look nicer
	if ( tempID != 0 )
		fprintf(logStream, "\n");

	return;
}

ProcessInfo* cFCFS::getNextToRun() {
	/* Find ready process which came first */
	printUnblocked();

	//This makes it non-preemptive
	if ( runningProc != NULL) {
		procLogger->writeProcessInfo(runningProc);
		return runningProc;
	}

	pthread_mutex_lock(&blockedLock);

	if ( readyQueue.size() == 0 ) {
		if ( totalBlocked > 0) {
			fprintf(logStream, "Scheduler waiting for a process to unblock\n");
			while ( readyQueue.size() == 0)
				pthread_cond_wait(&allBlocked, &blockedLock);

			printUnblocked();

		} else {
			/* Nothing is left to run */
			pthread_mutex_unlock(&blockedLock);
			return NULL;
		}
	}

	ProcessInfo* toRun = readyQueue.front();
	readyQueue.pop();

	assert(toRun != NULL);

	runningProc = toRun;
	runningProc->state = running;


	procLogger->writeProcessInfo(runningProc);

	pthread_mutex_unlock(&blockedLock);

	return toRun;
}

pidType cFCFS::numProcesses() {
	pidType total = 0;
	total += readyQueue.size();
	total += totalBlocked;

	total += (runningProc == NULL) ? 0 : 1;

	return total;
}

void cFCFS::addLogger(FILE* _logStream) {
	assert(logStream == NULL);
	assert(_logStream != NULL);

	logStream = _logStream;
	return;
}

void cFCFS::addProcLogger(cProcessLogger* _procLogger) {
	assert(procLogger == NULL);
	assert(_procLogger != NULL);

	procLogger = _procLogger;
	return;
}
