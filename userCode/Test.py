from header import *

def u():
	c = Circuit(True)
	q = Qubit()
	qList = []
	for i in range(0,3):
		qList.append(Qubit())
	#Rx(PI,qList[0])
	#Rx(PI,qList[0])
	#X(q)
	#QSprint(qList[0])
	#X(q)
	#Toffoli(q,qList[0],qList[1])
	#CNOT(qList[0],qList[1])
	# with Mif([qList[0]],[0]) as mo:
	# 	mo.X(q)
	# 	mo.H(qList[1])
		# mo.CNOT(qList[2],qList[1])

	#print(c.qubitExecuteListOD)
	#Rx(PI/2,q)
	with DMif([qList[0]],[0]) as dmo:
		dmo.X(q)
		dmo.H(qList[1])
		#q = dmo.Ry(PI,q)[-1]
		#q = dmo.Rz(-PI/2,q)[-1]
	# with DMif([qList[0],qList[1]],[1,0]) as dmo:
	# 	dmo.H(q)
	#M(qList[1])
	#QSprint(q)
	#QSprint(q.entanglement)
	#M(q)
	#QSprint(q)
	M(q)
	M(qList[1])
	#print(c.qubitExecuteList)
	#M(qList[0])
	c.execute(1024)