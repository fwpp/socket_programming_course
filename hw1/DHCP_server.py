import socket, time, sys
from datetime import datetime

class DHCP_packet:
    #for output order
    fieldList = ['OP','HTYPE','HLEN','HOPS','XID','SECS','FLAGS','CIADDR','YIADDR','SIADDR','GIADDR','CHADDR','SNAME','FILE','MAGIC_COOKIE','OPTION']
    fieldSize = {'OP':1, 'HTYPE':1, 'HLEN':1, 'HOPS':1, 'XID':4, 'SECS':2, 'FLAGS':2, 'CIADDR':4, 'YIADDR':4, 'SIADDR':4, 'GIADDR':4, 'CHADDR':16, 'SNAME':64, 'FILE':128, 'MAGIC_COOKIE': 4}

    def __init__(self):
        self.field = {}

    def setField_directly(self, fieldName, value):
        self.field[fieldName] = value

    def setField(self, fieldName, value, fieldSize):
        if fieldName in self.fieldList:
            if fieldName in self.field:
                self.field[fieldName] += (value).to_bytes(fieldSize, byteorder='big')
            else:
                self.field[fieldName] = (value).to_bytes(fieldSize, byteorder='big')
        else:
            print("Error: fieldName isn't in fieldList")

    def getField(self, fieldName):
        return self.field[fieldName]

    def getPacket(self):
        output = b''
        for key in self.fieldList:
            if key in self.field:
                output += self.field[key]

        return output

    #prcess received packet
    def set_convertField(self, fieldName, value):
        self.field[fieldName] = int.from_bytes(value, byteorder='big')
    
    def resetPacket(self):
        for key in self.field:
            self.field[key] = b''

class Server:
    BUFSIZE = 65535
    
    def __init__(self):
        self.inPacket = DHCP_packet()
        self.outPacket = DHCP_packet()

        self.IP_pool = [ int('0xc0a88801', base=16), int('0xc0a88802', base=16 ) ]
        self.assigned_IP_table = {}   #IP : [MAC, ASSIGNED time]  (expired when exceeding 1 min)

        timeMsg = 'server socket created ({})'.format( datetime.now() )
        print(timeMsg)

    def process(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        sock.bind( ("", 67) )

        while True:
            data, addr = sock.recvfrom(self.BUFSIZE)
            self.packetAnalysis(data)

            if self.inPacket.getField('OPTION')[53] == 1:
                #receive DHCPDISCOVER
                print('receive DHCPDISCOVER packet from {}'.format(addr))
                #print( data )

                if self.checkAvailableIP() == False:
                    print('There is no available IP')
                    continue
                #send DHCPOFFER
                data = self.DHCPOFFER()
                print('send DHCPOFFER')
                #print( data )
                #sock.sendto( data, ('255.255.255.255', 68) )
                sock.sendto( data, ('255.255.255.255', addr[1]) )   #for testing multiple client
                #sock.sendto( data, ('255.255.255.255', 20000) )    #for testing local

                #wait DHCPREQUEST
                data, addr = sock.recvfrom(self.BUFSIZE)
                self.packetAnalysis(data)

                destIP = '255.255.255.255'
            elif self.inPacket.getField('OPTION')[53] == 7:
                print('receive DHCPRELEASE packet from {}'.format(addr))
                releaseIP = self.inPacket.getField('CIADDR')
                self.IP_pool.append( releaseIP )
                self.assigned_IP_table[releaseIP][0] = ''
                self.assigned_IP_table[releaseIP][1] = ''
                continue
            else:
                destIP = self.decIP_to_string( self.inPacket.getField('CIADDR') )

            #receive DHCPREQUEST
            print('receive DHCPREQUEST packet from {}'.format(addr))
            #print(data)

            requestedIP = self.inPacket.getField('OPTION')[50]
            if destIP != '255.255.255.255':
                FLAGS = 0
            else:
                FLAGS = int( '0x8000', base=16 )
            if self.checkIPAvailable( requestedIP ):
                #send DHCPACK
                print('send DHCPACK')
                data = self.DHCPACK( requestedIP, FLAGS )
            else:
                #send DHCPNAK
                print('send DHCPNAK')
                data = self.DHCPNAK( FLAGS )

            #print(data)
            #sock.sendto( data, (destIP, 68) )
            if destIP != '255.255.255.255':
                destIP = addr[0]
            sock.sendto( data, (destIP, addr[1]) )   #for testing multiple client
            #sock.sendto( data, ('255.255.255.255', 20000) )    #for testing local

                

    def packetAnalysis(self, data):
        for fieldItem in self.inPacket.fieldList:
            if fieldItem == 'OPTION':
                continue
            
            fieldSize = self.inPacket.fieldSize[fieldItem]
            value = data[:fieldSize]

            self.inPacket.set_convertField(fieldItem, value)

            print( fieldItem, fieldSize, value, self.inPacket.getField(fieldItem) )

            data = data[fieldSize:]

        #analyze option
        option = {}
        while True:
            optionCode = data[0]
            if optionCode == 255:
                break
            
            optionLength = data[1]
            optionData = int.from_bytes(data[2:2+optionLength], byteorder='big')

            option[optionCode] = optionData

            data = data[2+optionLength:]


        self.inPacket.setField_directly('OPTION', option)
        print( 'OPTION', self.inPacket.getField('OPTION') )
    
    def DHCPOFFER(self):
        self.outPacket.resetPacket()

        YIADDR = self.IP_pool[0]

        packet_field = {
                        'OP' : 2,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : int('0x8000', base=16),
                        'CIADDR' : 0,
                        'YIADDR' : YIADDR,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.inPacket.getField('CHADDR'), 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16)
                        }

        packet_field_option = [
                        53, #DHCP Message Type
                        1,
                        2,  #DHCPOFFER
                        1,  #Subnet Mask
                        4,
                        255,
                        255,
                        255,
                        0,
                        3,   #Router
                        4,
                        192,
                        168,
                        1,
                        250,
                        51, #IP Address Lease Time
                        4,
                        0,
                        0,
                        0,
                        60,
                        54, #DHCP Server
                        4,
                        192,
                        168,
                        136,
                        134
                        ]

        return self.constructPacket( packet_field, packet_field_option )

    def DHCPACK(self, requestedIP, FLAGS):
        self.outPacket.resetPacket()

        packet_field = {
                        'OP' : 2,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : FLAGS,
                        'CIADDR' : 0,
                        'YIADDR' : requestedIP,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.inPacket.getField('CHADDR'), 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16)
                        }

        packet_field_option = [
                        53, #DHCP Message Type
                        1,
                        5,  #DHCPACK
                        1,  #Subnet Mask
                        4,
                        255,
                        255,
                        255,
                        0,
                        3,   #Router
                        4,
                        192,
                        168,
                        1,
                        250,
                        51, #IP Address Lease Time
                        4,
                        0,
                        0,
                        0,
                        60,
                        54, #DHCP Server
                        4,
                        192,
                        168,
                        136,
                        134
                        ]
       
        #record IP in assigned_IP_table
        self.assigned_IP_table[ requestedIP ] = [ self.inPacket.getField('CHADDR'), datetime.now()  ]

        #remove IP from IP pool
        if requestedIP in self.IP_pool:
            self.IP_pool.remove( requestedIP )

        return self.constructPacket( packet_field, packet_field_option )
 
    def DHCPNAK(self, FLAGS):
        self.outPacket.resetPacket()

        packet_field = {
                        'OP' : 2,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : FLAGS,
                        'CIADDR' : 0,
                        'YIADDR' : 0,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.inPacket.getField('CHADDR'), 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16)
                        }

        packet_field_option = [
                        53, #DHCP Message Type
                        1,
                        6,  #DHCPNAK
                        56, #Message
                        31 #length
                        ]
        message = '7265717565737465642061646472657373206e6f7420617661696c61626c65'
        for index in range(0, int( len(message) / 2 ) ):
            packet_field_option.append( int( '0x' + message[ index*2 : index*2+1+1 ], base=16) ) 

        return self.constructPacket( packet_field, packet_field_option )


    def constructPacket(self, packet_field, packet_field_option):
        for fieldItem in self.outPacket.fieldList:
            if fieldItem != 'OPTION':
                self.outPacket.setField(fieldItem, packet_field[fieldItem], self.outPacket.fieldSize[fieldItem])
            else:
                for optionVal in packet_field_option:
                    self.outPacket.setField('OPTION', optionVal, 1)

        self.outPacket.setField('OPTION', 255, 1)

        return self.outPacket.getPacket()
        

    def decIP_split(self, decIP):
        IP = []

        hexIP = hex(decIP)
        for index in range(0, 3+1):
            IP.append(int('0x' + hexIP[ (index+1) * 2 : (index+2)*2 ], base=16))

        return IP

    def decIP_to_string(self, decIP):
        IP = ''
        
        hexIP = hex(decIP)
        for index in range(0, 3+1):
            if IP != '':
                IP += '.'
            IP += str( int('0x' + hexIP[ (index+1) * 2 : (index+2)*2 ], base=16) )

        return IP


    def checkAvailableIP(self):
        now = datetime.now()
        for IP, IPinfo in self.assigned_IP_table.items():
            if IPinfo[1] != '':
                if (now - IPinfo[1]).seconds > 60:
                    IPinfo[0] = ''
                    IPinfo[1] = ''
                    self.IP_pool.append( IP )

        if len(self.IP_pool) != 0:
            return True

        return False
        
    def checkIPAvailable(self, IP):
        self.checkAvailableIP()

        if IP in self.assigned_IP_table:
            if self.assigned_IP_table[IP][0] != self.inPacket.getField('CHADDR') and self.assigned_IP_table[IP][1] != '':
                return False
            
        return True

if __name__ == "__main__":
    server = Server()
    server.process()

    
