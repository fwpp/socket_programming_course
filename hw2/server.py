import socket
import json
import threading
import time
import sys

class handleClient(threading.Thread):
	def __init__(self, sock, user):
		threading.Thread.__init__(self)
		self.sock = sock
		self.user = user
		self.username = ''
		
	def run(self):
		while True:
			print('wait for client')
			request = self.parsePacket(self.sock.recv(1000))
			print(request)
			if( request['action'] == 1 ):
				#login
				if request['username'] in self.user:
					if request['password'] == self.user[request['username']]['password']:
						response = self.createPacket({'code':200})
						self.sock.send(response)
						self.username = request['username']
						self.user[request['username']]['online'] = True
						self.user[request['username']]['socket'] = self.sock
			elif request['action'] == 2:
				#logout
				print('client: ',self.username,' logout')
				self.user[self.username]['socket'].close()
				self.user[self.username]['socket']=''
				self.user[self.username]['online']=False
				#finish thread
				return
			elif request['action'] == 3:
				#listuser
				msg = '';
				for username in self.user.keys():
					if self.user[username]['online'] and username != self.username:
						msg += username + '\n'
				response = self.createPacket({'action':3,'content':msg})
				self.sock.send(response)
			elif request['action'] == 4:
				#send
				to = request['to']
				content = request['content']
				if to in self.user:
					if self.user[to]['online']:
						response = {}
						sockTo = self.user[to]['socket']
						response = {'action':4,'from':self.username,'content':content}
						sockTo.send(self.createPacket(response))
					else:
						self.user[to]['mailbox'] += 'Message from '+self.username+':'+content
			elif request['action'] == 5:
				#talk
				to = request['to']
				sockTo = self.user[to]['socket']
				if 'content' not in request:
					#initialize chat
					contetn = self.username + ' want to chat with you'
					status = 1 #initialize
				else:
					status = 2 #chatting
					content = request['content']
					if content == 'exit()':
						status = 3 #finish chatting
				response = {'action':5,'from':self.username,'content':content,'status':status}
				sockTo.send(self.createPacket(response))
			elif request['action'] == 6:
				#broadcast
				content = request['content']
				for username in self.user.keys():
					if self.user[username]['online'] and username != self.username:
						response = {'action':6,'from':self.username,'content':content}
						sockTo = self.user[username]['socket']
						sockTo.send(self.createPacket(response))
			elif request['action'] == 7:
				#fetchMsg
				content = self.user[self.username]['mailbox']
				if content == '':
					content = 'no left message'
				response = {'action':7,'content':content}
				self.sock.send(self.createPacket(response))
				self.user[self.username]['mailbox'] = ''

	def createPacket(self,data):
		return json.dumps(data).encode('utf-8')
		
	def parsePacket(self,data):
		return json.loads(data.decode('utf-8'))
	
if __name__ == '__main__':
	#userlist
	user = {'hi':{'online':False,'password':'hi','socket':'','mailbox':''}, 'hello':{'online':False,'password':'hello','socket':'','mailbox':''}, 'oo':{'online':False,'password':'oo','socket':'','mailbox':''}}
	

	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.bind( ('localhost',10000) )
	sock.listen(100)

	print("server start")
	
	while True:
		print("wait for client")
		connection, client_address = sock.accept()
		print("recevier: ", client_address)
		handleClientObj = handleClient(connection, user)
		handleClientObj.start()
		
		
	
		
