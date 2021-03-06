import re

configMap = {'x-axis':0,'order':1,'y-axis':2,'output':3,'type':4}

class graphOutputs:
	def __init__(self):
		#There are simpler ways this could have been done but when
		#I originally made this I hadn't intended for there o be this
		#many opitons. If given more time I would rework this.
		self.xy_re = re.compile("^(sps|sfc|sprt)(i|d)?:(lpf|lcs|let|ltlbh|ltlbm|lpfp|lcsp|letp|ltlbhp|ltlbmp|ltime|ltimep|gpf|gcs|get|gpgo|gpgi|gtlbh|gtlbm|gtime|gtimep|gutil):(.+?):?(?:(?<=:)(png|jpg|bmp)$|(?<!:)$)")

		self.yaxis_lops = ['lpf','lcs','let','ltlbm','ltlbh','ltime'] ##lops - local options
		self.yaxis_gops = ['gpf','gcs','get','gpgo','gpgi','gtlbh','gtlbm','gtime','gutil'] ##gops - global options
		
		self.comment = re.compile("^##.*$")
		
		self.outputs = []
		
	def loadOutputs(self, filename):
		try:
			f = open(filename,"r")
		except IOError,e:
			print("Failed to open configuration file: " + filename)
			print("\tError: " + str(e))
			exit(-1)
		
		match = None
		
		for line in f:
			#Skip Comments
			if ( self.comment.match(line) ):
				continue;
			
			match = self.xy_re.match(line)
			
			if ( match ):
				self.outputs.append(match.groups())
				print(match.groups())
		
		f.close()
		
		if ( len(self.outputs) == 0 ):
			print("No output graphs specified in out_graphs.conf")
			exit(-1)
	
	class outputIter:
		def __init__(self, cls):
			self.index = -1
			self.parent = cls
			
		def next(self):
			self.index += 1
			
			if ( self.index >= len(self.parent.outputs) ):
				raise StopIteration
			else:
				return self.parent.outputs[self.index]
				
	def __iter__(self):
		return self.outputIter(self)
	
	def __getitem__(self, key):
		return self.outputs[key]

	def __len__(self):
		return len(self.outputs)
			
			
class testRun:
	def __init__(self):
		#Regex for capturing the bitstring of options
		self.bits_re = re.compile("^[01]+$")
		
		#Options PS:FN
		self.test_params = re.compile("^(\d+):(\d+):([a-zA-Z0-9-_]+):([a-zA-z0-9_-]+)$")
		
		##Match a process
		self.proc_re	= re.compile("^Process (\d+):$")
		self.global_re	= re.compile("^Global VMM info:$")
		self.cs_re		= re.compile("^Context Switches: (\d+)$")
		self.pf_re		= re.compile("^Page Faults: (\d+)$")
		self.et_re		= re.compile("^Execution Time: (\d+)$")
		self.tlbh_re	= re.compile("^TLB Hits: (\d+)$")
		self.tlbm_re	= re.compile("^TLB Miss: (\d+)$")
		self.pgi_re		= re.compile("^Page In: (\d+)$")
		self.pgo_re		= re.compile("^Page Out: (\d+)$")
		self.time_re	= re.compile("^Total Time: (\d+)$")

		self.proc_data = []
		
		self.global_cs		= None
		self.global_pf		= None
		self.global_et		= None
		self.global_tlbh	= None
		self.global_tlbm	= None
		self.global_pgo		= None
		self.global_pgi		= None

		self.avgCS		= None
		self.avgPF		= None
		self.avgET		= None
		self.avgTLBH	= None
		self.avgTLBM	= None
		
		##Gets set after data is parsed
		self.dataMap = {}
		
		##sps		= setting:Page Size
		##sfc		= setting:Frame Count
		##sprt		= setting:Page Replacement Type
		##stitle	= setting:Test Title
		self.paramMap = {'sps':0,'sfc':1,'sprt':2,'stitle':3}
		
		
	def loadTest(self,fn):
		self.filename = fn
		
		f = open(fn,"r")
		
		match = None
		line = f.readline()
		match = self.test_params.match(line)
		if ( match == None ):
			print("Test result %s is missing test parameters" % (fn))
			return False
			
		self.params = match.groups()
		print(self.params)
		
		for line in f:
			match_proc = self.proc_re.match(line)
			match_global = self.global_re.match(line)
			if ( match_proc ):
				proc_num = int(match_proc.group(1)) # Save process number
				
				proc_cs		= None
				proc_pf		= None
				proc_et		= None
				proc_tlbh	= None
				proc_tlbm	= None
				proc_time	= None
				
				for proc_line in f:
					match_cs	= self.cs_re.match(proc_line)
					match_pf	= self.pf_re.match(proc_line)
					match_et	= self.et_re.match(proc_line)
					match_tlbh	= self.tlbh_re.match(proc_line)
					match_tlbm	= self.tlbm_re.match(proc_line)
					match_time	= self.time_re.match(proc_line)
					
					if ( match_cs ):
						proc_cs = match_cs.group(1)
						match_cs = None
					elif ( match_pf ):
						proc_pf = match_pf.group(1)
						match_pf = None
					elif ( match_et ):
						proc_et = match_et.group(1)
						match_et = None
					elif ( match_tlbh ):
						#print("Matched local tlb hit: " + match_tlbh.group(1))
						proc_tlbh = match_tlbh.group(1)
						match_tlbh = None
					elif ( match_tlbm ):
						#print("Matched local tlb miss: " + match_tlbm.group(1))
						proc_tlbm = match_tlbm.group(1)
						match_tlbm = None
					elif ( match_time ):
						proc_time = match_time.group(1)
						match_time = None
					else:	
						self.proc_data.append((proc_num,proc_cs,proc_pf,proc_et,proc_tlbh,proc_tlbm,proc_time))

						print("Finished parsing process data:")
						print("\t" + str(self.proc_data[-1])) ##Print out tuple
						
						break
					##End process data for loop
				##End process if statement

			elif ( match_global ):
				
				for line in f:
					match_cs	= self.cs_re.match(line)
					match_pf	= self.pf_re.match(line)
					match_et	= self.et_re.match(line)
					match_tlbh	= self.tlbh_re.match(line)
					match_tlbm	= self.tlbm_re.match(line)
					match_pgo	= self.pgo_re.match(line)
					match_pgi	= self.pgi_re.match(line)
				
					#print("Line: " + line)
					if ( match_cs):
						self.global_cs = match_cs.group(1)
						match_cs = None
					elif ( match_pf ):
						self.global_pf = match_pf.group(1)
						match_pf = None
					elif ( match_et ):
						self.global_et = match_et.group(1)
						match_et = None
					elif ( match_tlbh ):
						print("TLB Hit: " + match_tlbh.group(1))
						self.global_tlbh = match_tlbh.group(1)
						match_tlbh = None
					elif ( match_tlbm ):
						print("TLB Miss: " + match_tlbm.group(1))
						self.global_tlbm = match_tlbm.group(1)
						match_tlbm = None
					elif ( match_pgo ):
						self.global_pgo = match_pgo.group(1)
						match_pgo = None
					elif ( match_pgi ):
						self.global_pgi = match_pgi.group(1)
						match_pgi = None
					else:
						print("Invalid line in global data results: " + line)
						break
				##End global data for loop
			##End global data if statement
		##End main for loop
		
		print("Global Data: ")
		print(self.global_cs, self.global_pf, self.global_et, self.global_tlbh, self.global_tlbm, self.global_pgo, self.global_pgi)
		
		print("Finished parsing results file: " + fn)
		return True

	def __getitem__(self,key):
		try:
			retVal = self.dataMap[key]
			return retVal
		except:
			raise IndexError
		
	def __len__(self):
		return len(self.proc_data)
		
	def getParam(self, param):
		retVal = None
		
		try:
			retVal = self.params[self.paramMap[param]]
		except:
			return None
			
		return retVal
		
	def setupMaps(self):
		cs_count	= 0
		pf_count	= 0
		et_count	= 0
		tlbh_count	= 0
		tlbm_count	= 0
		time_count	= 0
		
		## Mapping of the values in the process tuple
		## Just in-case it changes later this will be
		## easy to modify
		tupMap = {'pn':0,'cs':1, 'pf':2, 'et':3, 'tlbh':4, 'tlbm':5, 'time':6}

		##Hold individual process data
		self.dataMap['lcsp']	= []
		self.dataMap['lpfp']	= []
		self.dataMap['letp']	= []
		self.dataMap['ltlbhp']	= []
		self.dataMap['ltlbmp']	= []
		self.dataMap['ltimep']	= []
		
		for proc in self.proc_data:
			cs_count	+= int(proc[tupMap['cs']])
			pf_count	+= int(proc[tupMap['pf']])
			et_count	+= int(proc[tupMap['et']])
			tlbh_count	+= int(proc[tupMap['tlbh']])
			tlbm_count	+= int(proc[tupMap['tlbm']])
			time_count	+= int(proc[tupMap['time']])
			
			
			self.dataMap['lcsp'].append(int(proc[tupMap['cs']]))
			self.dataMap['lpfp'].append(int(proc[tupMap['pf']]))
			self.dataMap['letp'].append(int(proc[tupMap['et']]))
			self.dataMap['ltlbhp'].append(int(proc[tupMap['tlbh']]))
			self.dataMap['ltlbmp'].append(int(proc[tupMap['tlbm']]))
			self.dataMap['ltimep'].append(int(proc[tupMap['time']]))

		self.dataMap['procNum'] = proc[tupMap['pn']]
		##Take averages
		self.dataMap['lcs']		= (float(cs_count) / len(self.proc_data),)
		self.dataMap['lpf']		= (float(pf_count) / len(self.proc_data),)
		self.dataMap['let']		= (float(et_count) / len(self.proc_data),)
		self.dataMap['ltlbh']	= (float(tlbh_count) / len(self.proc_data),)
		self.dataMap['ltlbm']	= (float(tlbm_count) / len(self.proc_data),)
		self.dataMap['ltime']	= (float(time_count) / len(self.proc_data),)
		
		## Could just assign the value cs_count. In the future
		## there may be data at the global level that does not
		## correspond 1-1 with a local value so I want to keep
		## them separate.
		self.dataMap['gcs']		= (int(self.global_cs),  )
		self.dataMap['gpf']		= (int(self.global_pf),  )
		self.dataMap['get']		= (int(self.global_et),  )
		self.dataMap['gpgo']	= (int(self.global_pgo), )
		self.dataMap['gpgi']	= (int(self.global_pgi), )
		self.dataMap['gtlbh']	= (int(self.global_tlbh),)
		self.dataMap['gtlbm']	= (int(self.global_tlbm),)
		self.dataMap['gtime']	= (max(map(lambda x: int(x), self.dataMap['ltimep'])),)
		self.dataMap['gutil']	= (float(self.dataMap['get'][0]) / self.dataMap['gtime'][0],)
