import socket
import json
import threading
import time
import sys
import hashlib

class handleClient(threading.Thread):
	def __init__(self, sock, user, userlistFilename):
		threading.Thread.__init__(self)
		self.sock = sock
		self.user = user
		self.username = ''
		self.userlistFilename = userlistFilename
		self.key = 'messenger'
		
	def run(self):
		while True:
			print('wait for client')
			request = self.parsePacket(self.sock.recv(1000))
			print(request)
			if( request['action'] == 1 ):
				#login
				if request['username'] in self.user:
					#hash password
					md5Hash = hashlib.md5()
					md5Hash.update( (request['password']+self.key).encode('utf-8') )
					password = md5Hash.hexdigest()
					if password == self.user[request['username']]['password']:
						response = self.createPacket({'code':200})
						self.sock.send(response)
						self.username = request['username']
						self.user[request['username']]['online'] = True
						self.user[request['username']]['socket'] = self.sock
					else:
						response = self.createPacket({'code':403})
						self.sock.send(response)
				else:
					response = self.createPacket({'code':403})
					self.sock.send(response)
					return
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
			elif request['action'] == 8:
				#register
				username = request['username']
				password = request['password']
				
				if username not in self.user:
					#hash password
					md5Hash = hashlib.md5()
					md5Hash.update( (password+self.key).encode('utf-8') )
					password = md5Hash.hexdigest()
				
					#regiser successfully
					self.user[username] = {'online':False,'password':password,'socket':'','mailbox':''}
					response = {'code':200}
					
					userF = open(self.userlistFilename,"w")
					
					#copy data
					userTmp = {}
					for key in self.user.keys():
						userTmp[key] = {'online':False,'password':self.user[key]['password'],'socket':'','mailbox':self.user[key]['mailbox']}
					
					print(json.dumps(userTmp	), file=userF)
					userF.close()
				else:
					response = {'code':900}
				self.sock.send(self.createPacket(response))		
				

	def createPacket(self,data):
		return json.dumps(data).encode('utf-8')
		
	def parsePacket(self,data):
		return json.loads(data.decode('utf-8'))

class backup(threading.Thread):
	def __init__(self, user, userlistFilename):
		threading.Thread.__init__(self)
		self.user = user
		self.userlistFilename = userlistFilename
		
	def run(self):
		while True:
			time.sleep(10)
			userF = open(self.userlistFilename, "w")
			
			#copy data
			userTmp = {}
			for key in self.user.keys():
				userTmp[key] = {'online':False,'password':self.user[key]['password'],'socket':'','mailbox':self.user[key]['mailbox']}
			
			print(json.dumps(userTmp), file=userF)
			userF.close()
			print('backup successfully - ',time.strftime("%d %b %Y %H:%M:%S", time.localtime(time.time())))
		
if __name__ == '__main__':
	#load userlist from file
	userlistFilename = 'userlist.jdb'
	try:
		userF = open(userlistFilename, "r")
		data = userF.read()
		if data != '':
			user = json.loads(data)
		else:
			user = {}
		userF.close()
	except FileNotFoundError:
		print("There isn't an jdb file, it will automatically create one")
		userF = open(userlistFilename,"w")
		userF.close()
		user = {}
		
	#user = {'hi':{'online':False,'password':'hi','socket':'','mailbox':''}, 'hello':{'online':False,'password':'hello','socket':'','mailbox':''}, 'oo':{'online':False,'password':'oo','socket':'','mailbox':''}}

	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.bind( ('localhost',10000) )
	sock.listen(100)

	print("server start")

	#backup daemon
	backupObj = backup(user,userlistFilename)
	backupObj.start()
	
	while True:
		print("wait for client")
		connection, client_address = sock.accept()
		print("recevier: ", client_address)
		handleClientObj = handleClient(connection, user, userlistFilename)
		handleClientObj.start()
		
		
	
		
