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
