#import the ibm code
from IBMQuantumExperience import *
from interactCfg import *
from Error import *
import os
import sys
#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]

#the max execute times is made by IBM stuff
MAXTIMES = 8192

class IBMQX:
	def __init__(self):
		print("Connecting to the Server...")
		#change the config message in config/IBMToken.cfg
		tokenDic = readCfgPM()
		self.__config = {
   			"url": tokenDic['url']
		}	
		#init the api
		self.api = IBMQuantumExperience(tokenDic['token'], self.__config)
		deviceList = self.__getAvailalbeBak()
		self.device = tokenDic['device']
		self.shot = int(tokenDic['shot'])
		if self.device not in deviceList:
			try:
				raise IBMError("the seleted device isn't available")
			except IBMError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie.value,funName,line)	
		if self.shot < 1 or self.shot > MAXTIMES:
			try:
				raise IBMError("the execute times must be from 1 to 8192, but the input is " + str(self.shot))
			except IBMError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie.value,funName,line)
		#get the connectivity map of the device according to the name of the device
		try:
			self.connectivity = tokenDic['connectivity'][self.device]
		except KeyError as ke:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("the IBMToken.cfg doesn't have the connectivity of the current device: " + self.device,funName,line)
		#create a new folder to save the data of IBMQX
		circuit = checkEnvironment()
		if os.path.exists(circuit.urls + "/IBMQX") == False:
			try:
				os.makedirs(circuit.urls + "/IBMQX") 
			except OSError:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("Can't create the new folder 'IBMQX'!",funName,line)	

	#get the availalbe backend, return the backend list
	def __getAvailalbeBak(self):
		result = []
		lists = self.api.available_backends()
		for item in lists:
			backend = item['name']
			result.append(backend)
		return result

	#adjust the QASM code, which is producted by circuit.QASM(), so that the qubits can satisfy the constraint
	#of the CNOT connectivity
	def __canExecute(self):
		print("Optimizing the QASM-code, please wait for a while...")
		#the code has been store in circuit.url/QASM.txt
		circuit = checkEnvironment()
		if circuit == None:
			return None
		codeLocation = circuit.urls + "/QASM.txt"
		#this function must be called after circuit.execute()
		if os.path.exists(codeLocation) == False:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The QASM code hasn't been generated, please check your code!",funName,line)	
		file = open(codeLocation)
		QASM = file.readlines()	
		file.close()
		CNOTList = []
		code = ""
		#store the qubit has been measured
		measured_q = []
		for line in QASM:
			q = line.split(" ")[1]
			if q in measured_q:
				#the qubit has been measured
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("QuanSim can't act any gate on a measured qubit!",funName,line)
			
			#the measure must be the last gate on qubits
			if "measure" in line:
				if "," in q:
					info = get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("QuanSim can't measure more than one qubit at the same time!",funName,line)
				measured_q.append(q)
			if "cx" in line:
				strs = q.split(',')
				#get the id of control-qubit and target-qubit
				tQ = strs[1][2]
				cQ = strs[0][2]
				#the reverse cnot won't be appended to the list
				if [cQ,tQ] in CNOTList or [tQ,cQ] in CNOTList:
					continue
				CNOTList.append([cQ,tQ])

		#check the CNOT list whether satisfies the constraint of the connectivity
		CNOTError = []
		print(CNOTList)
		print(self.connectivity)

		#从宏观的角度分析，总共的连接关系，节点的入度和出度
		#convert the cnotList to dic
		CNOTDic = {}
		for cnot in CNOTList:
			cQ = cnot[0]
			tQ = cnot[1]
			if cQ in CNOTDic:
				CNOTDic[cQ].append(tQ)
			else:
				CNOTDic[cQ] = [tQ]
		

		for index in range(0,len(CNOTList)):
			if CNOTList[index] in CNOTError:
				continue
			cQ = CNOTList[index][0]
			tQ = CNOTList[index][1]
			if self.__checkConstraint([cQ,tQ]):
				continue
			else:
				#先从宏观的角度来分析：总共有多少种连接关系，对应的入度和出度
				#宏观的角度发现可以执行，那么就是可以执行的
				if cQ in self.connectivity:
					for t in self.connectivity[cQ]:
						CNOTList[index][1] = t
						tBool = True
						for i in range(0,index):
							if CNOTList[i][0] == tQ:
								CNOTList[i][0] = t
							if CNOTList[i][1] == tQ:
								CNOTList[i][1] = t
							if self.__checkConstraint([CNOTList[i][0],CNOTList[i][1]]):
								continue
							else:
								tBool = False
								break
						if tBool:
							break
						else:
							continue
				else:
					#改变cQ，tQ是否改变需要再讨论
			CNOTError.append(tmp)

		if len(CNOTError) == 0:
			self.__reverseCNOT(QASM)

		reasonList = []
		canExecute = True
		if len(CNOTError) != 0:
			for item in CNOTError:
				cq = str(item[0])#the controlQubit
				tq = str(item[1])#the targetQubit			
				#record the reason for why can,'t execute the code
				canExecute = False
				reason = "Can't utilize Q" + cq + " as the control Qubit and Q" + tq + " as the target Qubit!"
				reasonList.append(reason)

		if canExecute:
			for line in QASM:
				code += line
			try:
				file = open(circuit.urls + "/IBMQX/QASM-modified.txt","w")
				file.write(code)	
				file.close()	
			except IOError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("Can't write QASM code to QASM-modified.txt!",funName,line)		
			return code
		file = open(circuit.urls + "/IBMQX/codeWarning.txt",'a')
		file.write("WARNING:\n")
		#write the reason in codeWarning.txt
		for i in range(0,len(reasonList)):
			strs = str(i+1) + "." + reasonList[i] + "\n"
			file.write(strs)
		return None

	#check cnot whether satisfies the constraint
	#the format of cnot should be [1,3]
	def __checkConstraint(self,cnot:list):
		if len(cnot) != 2:
			try:
				raise ValueError
			except ValueError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("The cnot should be two-dimension!",funName,line)
		cQ = cnot[0]
		tQ = cnot[1]
		if cQ in self.connectivity and tQ in self.connectivity[cQ]:
			#directly satisfy the constraint
			return True
		#reverse CNOT; will introduce addtional H and bring noise
		elif tQ in self.connectivity and cQ in self.connectivity[tQ]:
			return True
		else:
			return False

	#get the legal cnot gate in current device
	def __getLegalCNOT(self):
		legalCList = []
		for cQ in self.connectivity:
			for tQ in self.connectivity[cQ]:
				if [cQ,tQ] not in legalCList:
					legalCList.append([cQ,tQ])
				if [tQ,cQ] not in legalCList:
					legalCList.append([tQ,cQ])
		return legalCList

	#modify the qasm code by adding H to reverse the current CNOT
	def __reverseCNOT(self,QASM):
		lineN = 0
		while lineN < len(QASM):
			if 'cx' in QASM[lineN]:
				q = QASM[lineN].split(" ")[1]
				strs = q.split(',')
				#get the id of control-qubit and target-qubit
				tQ = strs[1][2]
				cQ = strs[0][2]
				if cQ in self.connectivity and tQ in self.connectivity[cQ]:
					pass
				elif tQ in self.connectivity and cQ in self.connectivity[tQ]:				
					#add H gate to satisfy the constraint
					hExternal = "h q[" + str(cQ) + "];\r\nh q[" + str(tQ) + "];\r\n"					
					gateStr = "cx q[" + str(cQ) + "],q[" + str(tQ) + "];"
					if gateStr in QASM[lineN]:
						QASM.insert(lineN,hExternal)
						QASM[lineN+1] = "cx q[" + str(tQ) + "],q[" + str(cQ) + "];\r\n"
						QASM.insert(lineN+2,hExternal)
				else:
					pass
			lineN += 1 


	#execute the code
	def executeQASM(self,experimentName = None):
		code = self.__canExecute()
		circuit = checkEnvironment()
		if code == None:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The QASM code generated by QuanSim doesn't satisfy the requirement of IBMQX!",funName,line)
			return False
		try:
			data = self.api.run_experiment(code,self.device,self.shot,experimentName)
		except ConnectionError as ce:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Can't connect to the server, Please try again later!",funName,line)
		#analyse the message
		try:
			file = open(circuit.urls + "/IBMQX/rawData_IBMQX.txt","w",encoding='utf-8')
			file.write(str(data))
			file.close()
		except IOError:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Can't write the raw data of IBMQX to rawData_IBMQX.txt!",funName,line)
		try:
			status = data['status']
			result = data['result']
			measure = result['measure']
			qubits = measure['qubits']
			labels = measure['labels']
			values = measure['values']
			rList = []
			for i in range(0,len(labels)):
				states = ""
				for q in qubits:
					state = labels[i][len(labels[i])-q-1]
					states += state
				rList.append([states,values[i]])
			dataMsg = "-" * 30
			dataMsg += " the data of IBMQX "
			dataMsg += "-" * 31
			dataMsg += "\r\n"
			dataMsg += "Result:\r\n"
			for r in rList:
				prob = float(r[1]) * 100
				dataMsg += " "*8+"|" + r[0] + ">----%.2f%%"%(prob)
				dataMsg += "\r\n"
			dataMsg += "-" * 80
			print(dataMsg)
		except KeyError:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("There are some keys aren't in the result returned by IBMQX!",funName,line)
		try:
			file = open(circuit.urls + "/IBMQX/Data_IBMQX.txt","w",encoding='utf-8')
			file.write(dataMsg)
			file.close()
		except IOError:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Can't write the raw data of IBMQX to Data_IBMQX.txt!",funName,line)
