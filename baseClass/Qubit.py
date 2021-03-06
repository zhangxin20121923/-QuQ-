#!/usr/bin/python3
from baseQubit import BaseQubit
import sys
sys.path.append('../tools/')
import interactCfg
import math
#from Circuit import Circuit
from Error import *
from Bit import Bit
import random
import copy

#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]

#the init state of the qubit must be |0>
class Qubit(BaseQubit):
	#mode is an argument of the class, so that all the qubit can have the same execution mode
	mode = interactCfg.readCfgEM()
	#use the list to store the ids, so that ID won't repeat
	idList = []
	#figure out the number of the Qubit in <QuQ>, and the value of the parameter can only increase
	totalNum = 0
	#the physical process of "preparation" is described as this function
	#mode='theory' or 'simulator', the user manual introduce details of the arguments

	#if the parameter "tag" is set to True, it means that the qubit is an auxiliary qubit 

	def __init__(self,tag = False,ids=None):
		#BaseQubit.__init__(self)
		self.matrix = [[],[]]
		self.amplitude = [0,0]
		self.assignmentError = 0.0
		self.singleGateError = 0.0
		#show whether the qubit was in entanglement
		self.entanglement = None
		if ids == None:
			ids = Qubit.totalNum + 1
		#the index of the current qubit, the range is from 0 to n
		if ids in Qubit.idList:
			try:
				raise IDRepeatError()
			except IDRepeatError as ir:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(ir,funName,line)
		self.ids = ids
		Qubit.totalNum += 1
		Qubit.idList.append(ids)
		#set the initial value of the qubit according to the mode 
		if self.mode == 'simulator':
			#has assignment error and gate error
			error = interactCfg.readCfgER(ids)
			#according to the error to product the amplitude
			self.matrix[1].append(math.sqrt(error))
			self.matrix[0].append(math.sqrt(1-error))
		elif self.mode == 'theory':
			#no assignment error or gate error
			self.matrix[0].append(1)
			self.matrix[1].append(0)
		else:
			try:
				raise ExecuteModeError()
			except ExecuteModeError as em:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(em,funName,line)
		self.setAmp()
		#set the type of the qubit 
		if tag:
			#it means that the qubit is an auxiliary Qubit
			self.tag = "AX"
		else:
			#the qubit is an actual qubit
			self.tag = "AC"
		self.recordQubit()

	#overwrite the function
	def getAmp(self):
		if self.entanglement == None:
			return self.amplitude
		else:
			prob = self.decideProb([self])[0]
			amp = []
			for p in prob:
				amp.append(math.sqrt(p))
			return amp
	def getMatrix(self):
		if self.entanglement == None:
			return self.matrix
		else:
			prob = self.decideProb([self])[0]
			matrix = []
			for p in prob:
				matrix.append([math.sqrt(p)])
			return matrix

	#store the current qubit in the circuit instance
	def recordQubit(self):
		circuitInstance = checkEnvironment()
		if circuitInstance == None:
			#there is zero or more than one circuit instance
			try:
				raise EnvironmentError()
			except EnvironmentError as ee:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(ee,funName,line)

		if circuitInstance.withOD:
			if self in circuitInstance.qubitExecuteList:
				del circuitInstance.qubitExecuteListOD[self]
				circuitInstance.qubitNumOD -= 1
			circuitInstance.qubitExecuteListOD[self] = []
			circuitInstance.qubitNumOD += 1		

		if self.tag == "AC":
			if self in circuitInstance.qubitExecuteList:
				del circuitInstance.qubitExecuteList[self]
				circuitInstance.qubitNum -= 1
			circuitInstance.qubitExecuteList[self] = []
			circuitInstance.qubitNum += 1

	def decideProb(self, qubitList:list = None):
		#the first dimen is probability, the second dimen is state
		result = [[],[]]
		qs = self.entanglement
		#once the qubit is in entanglement, the amplitude maybe different
		if qs == None:
			#print(self.getAmp())
			self.normalize()
			#print(self.getAmp())
			amplitude = self.getAmp()
			result[0].append((amplitude[0] * amplitude[0].conjugate()).real)
			result[0].append((amplitude[1] * amplitude[1].conjugate()).real)
			result[1].append("0")
			result[1].append("1")
		else:
			if qubitList == None or len(qubitList) == 0:
				try:
					raise ValueError()
				except ValueError:
					info = get_curl_info()
					funName = info[0]
					line = info[1]
					interactCfg.writeErrorMsg("ValueError: The argument qubitList has no element, it must has at least one element",funName,line)
			#print(qs.getAmp())
			qs.normalize()
			amplitude = qs.getAmp()
			totalQubit = len(qs.qubitList)
			iTH = []
			#get the index of the argument qubitList
			for qubit in qubitList:
				index = qs.getIndex(qubit)
				if index == -1:
					try:
						raise ValueError("Q" + str(qubit.ids) + " is not belong to the qubits")
					except ValueError as ve:
						info = get_curl_info()
						funName = info[0]
						line = info[1]
						interactCfg.writeErrorMsg(ve,funName,line)
				iTH.append(index)	
			length = len(iTH)
			caseNum = 2 ** length
			iTH.sort()
			#get the corresponding state
			stateList = []
			probList = []
			for i in range(0,caseNum):
				state = bin(i).split('b')[1]
				#add zero to beginning of the binary 
				for m in range(len(state) , len(iTH)):
					state = '0' + state				
				stateList.append(state)
			for state in stateList:
				#len(state) = length
				indexList = []

				for j in range(0,length):
					indexList.append(2 ** (totalQubit - iTH[j] - 1))
				prob = 0
				for k in range(0,2**totalQubit):
					target = True
					for index in range(0,len(indexList)):
						if k & indexList[index] == int(state[index]) * indexList[index]:
							continue
						target = False
					if target:
						prob += (amplitude[k] * amplitude[k].conjugate()).real
				probList.append(prob)
			# print(stateList)
			# print(amplitudeList)
			result[0] = probList
			result[1] = stateList
		return result

	def degenerate(self):
		self.normalize()
		ampList = self.getAmp()
		probList = [(i*i.conjugate()).real for i in ampList]
		if len(probList) != 2:
			try:
				raise ValueError
			except ValueError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("ValueError: the sum of the probabilities of |0> and |1> is not 1!",funName,line)
		randomNumber = random.uniform(0,1)
		#the order of the state of the qubit must be 0 and 1
		if randomNumber - probList[0] > 0:
			value = 1
		else:
			value = 0
		bit = Bit(value,self.ids)	
		qs = self.entanglement
		if qs != None:
			qs.deleteItem([self])
		return bit

	#delete the qubit
	def delete(self):
		self.entanglement = None
		if self.ids in Qubit.idList:
			Qubit.idList.remove(self.ids)

	# def __del__(self):
	# 	try:
	# 		Qubit.idList.remove(self.ids)
	# 		#the qubit is degenerated to Bit
	# 	except KeyError as ke:
	# 		interactCfg.writeErrorMsg("KeyError: " + str(ve) + " is not in Qubit instance!")

class Qubits(BaseQubit):
	#the init has two qubits as input, compute the tensor product of the two elements
	#########################################################################################################
	#if there are some other ways to preparation entanglement, we can write another init with different input
	#########################################################################################################
	def __init__(self,q1:Qubit,q2:Qubit):
		#the two qubits must be not in the entanglement
		if q1.entanglement != None or q2.entanglement != None:
			try:
				raise ValueError("The qubits must not be in the entanglement!")
			except ValueError as ve:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(ve,funName,line)
		#store the number of entanglement qubits
		self.number = 2
		self.matrix = []
		self.setMatrix(q1 * q2)
		self.amplitude = [0] * (len(q1.getAmp())*len(q2.getAmp()))
		self.qubitList = [q1,q2]
		#change the variable "entanglement" of qubit to this instance
		q1.entanglement = self
		q2.entanglement = self

	#qs[index]
	def __getitem__(self,index):
		item = None
		try:
			item = self.qubitList[index]
		except IndexError as ie:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg(ie,funName,line)
		return item

	#input two matrix, then compute the tensor product of the two matrix and return the new matrix
	def mulMatrix(self,matrix,newMatrix):
		result = []
		for i in range(0,len(matrix)):
			for j in range(0,len(newMatrix)):
				item = []
				item.append(matrix[i][0] * newMatrix[j][0])
				result.append(item)
		return result

	#return the index of the qubitList, if not in, return -1
	def getIndex(self,qubit:Qubit):
		for i in range(0,len(self.qubitList)):
			if qubit == self.qubitList[i]:
				return i
		return -1

	#data can be Qubit or Qubits
	def addNewItem(self,data):
		if len(self.qubitList) == 0:
			try:
				raise ValueError()
			except ValueError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("ValueError: There is no element in this Qubits!",funName,line)
		types = type(data)
		if types != Qubit and types != Qubits:
			try:
				raise TypeError()
			except TypeError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("TypeError: the type should be Qubit or Qubits",funName,line)
		#compute the matrix of the new qubits
		newMatrix = self.mulMatrix(self.getMatrix(),data.getMatrix())
		if types == Qubit:
			self.qubitList.append(data)
			self.number += 1
			data.entanglement = self
		else:
			#the types of data is qubits
			for item in data.qubitList:
				self.qubitList.append(item)
				self.number += 1
				item.entanglement = self
		self.setMatrix(newMatrix)
		return 0

	#delete the list of qubit from current instance
	def deleteItem(self,ql:list):
		for q in ql:
			if self.getIndex(q) == -1:
				#the qubit isn't in this instance
				try:
					raise ValueError()
				except ValueError:
					info = get_curl_info()
					funName = info[0]
					line = info[1]
					interactCfg.writeErrorMsg("ValueError: qubit(q" + str(q.ids) + ") is not in this Qubits!",funName,line)
		#qlIn store the qubit which are in this Qubits and haven't been measured
		qlIn = []
		for qubit in self.qubitList:
			if qubit not in ql:
				qlIn.append(qubit)
		#change the state of the current Qubits
		newMatrix = []
		if len(qlIn) == 0:
			pass
		else:
			result = q.decideProb(qlIn)
			state = result[1]
			prob = result[0]
			newMatrix = []
			for i in range(0,2**(len(qlIn))):
				newMatrix.append([0])
			for s in range(0,len(state)):
				l = len(state[s])
				sums = 0
				for index in range(0,l):
					number = int(state[s][index]) * (2**(l-index-1))
					sums += number
				newMatrix[sums][0] = math.sqrt(prob[s])
		#delete the measured qubit from qubits and convert the measured qubit to bit class
		for q in ql:
			q.delete()
		for i in range(0,len(ql)):
			self.number -= 1
			self.qubitList.remove(ql[i])
		self.setMatrix(newMatrix)


