# socket_programming_course
put homework


	--- hw1 DHCP ---
DISCOVER, OFFER, REQUEST, OFFER, NAK, RELEASE
client would try to DISCOVER DHCP after timeout
client would request lease when lease time was expired
server can serve multiple clients at the same time
server would send NAK when client request unavailable IP
argument : port, specifyRequestedIP (for testing)
XID, MAC generated randomly
client woud send RELEASE to release IP

	testing environment
windows 7 (client)
ubuntu 14.04 (server) in VMware



	--- hw2 messager ---
command mode
	- listuser
	- logout
	- send username message
	- broadcast message

chatting mode
	- talk username

server
	- authenticate username and password
	- provide left message service
	- md5 hash password and authenticate
	- bakup user info in period
	- provide register service

	testing environment
windows 7 (client , server)


	--- hw2 messager ---
support TLS connection
login and logout
post board (post new post)
profile (edit profile)
register : create new user
password is hash with md5 and extra key
auth : authenticate before enter any page of main
ajax to check whether there is new post
search posts

	testing environment
windows 7
framework : django           ( installation : pip install 'django<1.8' )
sslserver : django-sslserver ( installation : pip install django-sslserver )

