import socket
import json
import threading
import time
import sys
from getpass import getpass

class receiver(threading.Thread):
	def __init__(self, sock,clientStatus):
		threading.Thread.__init__(self)
		
		self.sock = sock
		self.clientStatus = clientStatus
		
	def run(self):
		while True:
			response = self.parsePacket(self.sock.recv(1000))

			print(response)
			if response['action'] == 3:
				print(response['content'])
			elif response['action'] == 4:
				print(response['from'],' says: ',response['content'])
			elif response['action'] == 5:
				status = response['status']
				content = response['content']
				if status == 1:
					print("press 'Enter' go to chatting mode")
					self.clientStatus['chatTo'] = response['from']
					self.clientStatus['mode'] = 1
				elif status == 2:
					print(response['from'],' says ',content)
				elif status == 3:
					print("press 'Enter' back to command mode")
					self.clientStatus['mode'] = 0
					self.clientStatus['chatTo'] = ''
			elif response['action'] == 6:
				print(response['from'],' says: ',response['content'])
			elif response['action'] == 7:
				print(response['content'])
		
	def createPacket(self,data):
		return json.dumps(data).encode('utf-8')
		
	def parsePacket(self,data):
		return json.loads(data.decode('utf-8'))

		
def createPacket(data):
	return json.dumps(data).encode('utf-8')
		
def parsePacket(data):
	if data == None:
		data = {'action':''}
	return json.loads(data.decode('utf-8'))	
	
if __name__ == "__main__":
	#determine which mode is on
	# 0 : command
	# 1 : chatting
	clientStatus = {'mode':0,'chatTo':''}

	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.connect( ('localhost',10000) )
	
	print("connect to server")
	
	request_map = {'login':1,'logout':2,'listuser':3,'send':4,'talk':5,'broadcast':6,'fetchMsg':7}
	"""
	request:
		action
		1 : login
		2 : logout
		3 : listuser
		4 : send
		5 : talk
		6 : broadcast
		7 : fetchMsg
		
	response:
		code:
		200: OK
		403: forbidden
	"""
	
	#login
	while True:
		username = input("enter username :")
		password  = getpass();
		request = { 'action' :request_map['login'], 'username':username, 'password':password }
		sock.send( createPacket(request) )
		response = parsePacket(sock.recv(100))
		print('response: ',response)
		if( response['code'] == 403 ):
			print("login fail")
		else:
			break
	print("login successfully")
	
	#construct a thread to receive packet
	receiverObj = receiver(sock,clientStatus)
	receiverObj.start()
	
	#At the beginning, user fetchMsg to see whether anyone left message for him/her
	print('fetch left message...')
	request = {'action':request_map['fetchMsg']}
	sock.send( createPacket(request) )
	
	#handle command
	while True:
		command = input(">")
		
		#chatting mode
		while clientStatus['mode'] == 1:
			content = input()
			if clientStatus['mode'] == 0:
				print('exit chatting mode')
				clientStatus['chatTo'] = ''
				break
			if content == '':
				continue
			to = clientStatus['chatTo']
			request = {'action':5,'to':to,'content':content}
			print(request)
			sock.send(createPacket(request))
			if content == 'exit()':
				clientStatus['mode'] = 0
				clientStatus['chatTo'] = ''
				break
		
		request = {}
		command = command.split(' ')
		action = command[0]
		if action not in request_map:
			continue
		request['action'] = request_map[action]
		print('action:',request['action'])
		
		if request['action'] == 2:
			sock.send(createPacket(request))
			break;
		elif request['action'] == 3:
			sock.send(createPacket(request))
		elif request['action'] == 4:
			#send to content
			to = command[1]
			content = command[2]
			request['to'] = to
			request['content'] = content
			print(request)
			sock.send(createPacket(request))
		elif request['action'] == 5:
			#talk person
			to = command[1]
			request['to'] = to
			print(request)
			sock.send(createPacket(request))
			clientStatus['mode'] = 1
			while True:
				content = input() #enter exit() to exit chatting mode
				if clientStatus['mode'] == 0:
					print('exit chatting mode')
					clientStatus['chatTo'] = ''
					break
				if content == '':
					continue
				request = {'action':5,'to':to,'content':content}
				sock.send(createPacket(request))
				if content == 'exit()':
					clientStatus['mode'] = 0
					clientStatus['chatTo'] = ''
					break
		elif request['action'] == 6:
			content = command[1]
			request['content'] = content
			print(request)
			sock.send(createPacket(request))
		

	