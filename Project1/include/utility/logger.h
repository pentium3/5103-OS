#ifndef LOGGER_H_INCLUDED
#define LOGGER_H_INCLUDED

/* This logger does not cut trees but it
 * does consume bits */

#include <assert.h>
#include <iostream>
#include <fstream>

using namespace std;

static FILE* logStream;

static bool logInitialized;

int initLog(const char* filename);
void closeLog();

FILE* getStream();


#endif // LOGGER_H_INCLUDED