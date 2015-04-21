import socket, time, sys, random, argparse
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

class Client:
    BUFSIZE = 65535
    
    def __init__(self):
        self.IP = ''
        self.submask = ''
        self.router = ''
        self.DNS = ''
        
        #generate random MAC
        self.MAC = ''
        for index in range(12):
            if random.randint(0, 1):
                self.MAC += chr( random.randint(48, 57) )
            else:
                self.MAC += chr( random.randint(97, 102) )
        self.MAC = ( int('0x' + self.MAC[0:8], base=16) ).to_bytes(4, byteorder='big') \
                    + ( int('0x' + self.MAC[8:12] + '0' * 4, base=16) ).to_bytes(4, byteorder='big') \
                    + (0).to_bytes(8, byteorder='big')
        self.MAC = int.from_bytes( self.MAC, byteorder='big' )

        #generate random XID
        self.XID = ''
        for index in range(8):
            if random.randint(0, 1):
                self.XID += chr( random.randint(48, 57) )
            else:
                self.XID += chr( random.randint(97, 102) )
        self.XID = int( '0x' + self.XID, base=16 )

        self.inPacket = DHCP_packet()
        self.outPacket = DHCP_packet()
        
        timeMsg = 'client socket created, MAC (CHADDR in dec): {} ({})'.format( self.MAC,  datetime.now() )
        print(timeMsg)

    def process(self, port, specifyRequestedIP):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        #sock.bind( ('192.168.136.1' ,68) )
        sock.bind( ('192.168.136.1' ,port) )

        #sock.connect( ('192.168.136.134', 67) )

        #set socket timeout
        sock.settimeout(10)

        while True:
            try:
                #send DHCPDISCOVER
                data = self.DHCPDISCOVER()
                print('*** SEND DHCPDISCOVER ***')
                #print(data)

                #sock.sendto(data, ('192.168.136.255', 67) )
                sock.sendto(data, ('255.255.255.255', 67) )

                #receive DHCPOFFER
                while True:
                    data, addr = sock.recvfrom(self.BUFSIZE)
                    if addr[0] != '192.168.136.134':
                        continue
                    print('receive DHCPDISCOVER from {}'.format(addr))
                    #print(data)
                    break

                self.packetAnalysis(data)

                #send DHCPREQUEST
                data = self.DHCPREQUEST( clientIP = 0 ,  FLAGS = int( '0x8000', base=16 ), specifyRequestedIP = specifyRequestedIP )

                print('*** SEND DHCPREQUEST ***')
                #print(data)
                #sock.sendto( data, ('192.168.136.255', 67) )
                sock.sendto(data, ('255.255.255.255', 67) )

                #receive DHCPACK
                while True:
                    data, addr = sock.recvfrom(self.BUFSIZE)
                    if addr[0] != '192.168.136.134':
                        continue
                    
                    self.packetAnalysis(data)
                    
                    if self.inPacket.getField('OPTION')[53] == 6:
                        print('receive DHCPNAK from {}'.format(addr))
                        print(data)
                        sys.exit()
                        
                    print('receive DHCPACK from {}'.format(addr))
                    #print(data)
                    break

                
            except socket.timeout:
                print('timeout, DHCPDISCOVER again')
                continue

            break

        
        #while True:
        for index in range(2):
            clientIP = self.inPacket.getField('YIADDR')
            print('get IP : {}'.format( self.decIP_to_string( clientIP ) ) )

            DHCP_serverIP = self.decIP_to_string( self.inPacket.getField('OPTION')[54] )
            print( 'DHCP_serverIP', DHCP_serverIP )
            
            leaseTime = self.inPacket.getField('OPTION')[51]
            print('lease: {} seconds'.format(leaseTime))
            time.sleep( leaseTime / 2 )

            #send DHCPREQUEST
            data = self.DHCPREQUEST( clientIP, FLAGS = 0, specifyRequestedIP = 0 )

            print('*** SEND DHCPREQUEST ***')
            print(data)
            #sock.sendto( data, ('192.168.136.255', 67) )
            sock.sendto(data, (DHCP_serverIP, 67) )

            #receive DHCPACK
            while True:
                data, addr = sock.recvfrom(self.BUFSIZE)
                print(addr[0])
                if addr[0] != '192.168.136.134':
                    continue
                print('receive DHCPACK from {}'.format(addr))
                print(data)
                break

            self.packetAnalysis(data)

        data = self.DHCPRELEASE(clientIP)
        sock.sendto( data, (DHCP_serverIP, 67) )

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

    def DHCPDISCOVER(self):
        self.outPacket.resetPacket()
        
        CHADDR_byte = ( int('0x00053C04', base=16) ).to_bytes(4, byteorder='big')
        CHADDR_byte += ( int('0x8D590000', base=16) ).to_bytes(4, byteorder='big')
        CHADDR_byte += (0).to_bytes(8, byteorder='big')
        CHADDR = int.from_bytes(CHADDR_byte, byteorder='big')

        packet_field = {
                        'OP' : 1,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.XID,
                        'SECS' : 0,
                        'FLAGS' : int('0x8000', base=16),   #0x8000  : broadcast
                        'CIADDR' : 0,
                        'YIADDR' : 0,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.MAC, 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16) #DHCP
                        }
        

        packet_field_option = [
                        53, #DHCP Message Type
                        1,
                        1,  #DHCPDISCOVER
                        50,  #Requested IP Address
                        4,
                        192,
                        168,
                        136,
                        1
                        ]
        
        return self.constructPacket(packet_field, packet_field_option)


    def DHCPREQUEST(self, clientIP, FLAGS, specifyRequestedIP):
        self.outPacket.resetPacket()

        packet_field = {
                        'OP' : 1,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : FLAGS,
                        'CIADDR' : clientIP,
                        'YIADDR' : 0,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.MAC, 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16)
                        }

        if specifyRequestedIP == 0:
            requestedIP = self.decIP_split( self.inPacket.getField('YIADDR') )
        else:
            requestedIP = list( map( lambda x: int(x), specifyRequestedIP.split('.') ) )
        DHCP_serverIP = self.decIP_split( self.inPacket.getField('OPTION')[54] )

        packet_field_option = [
                        53, #DHCP Message Type
                        1,
                        3,  #DHCPREQUEST
                        50,  #Requested IP Address
                        4,
                        requestedIP[0],
                        requestedIP[1],
                        requestedIP[2],
                        requestedIP[3],
                        54,   #Server Identifier
                        4,
                        DHCP_serverIP[0],
                        DHCP_serverIP[1],
                        DHCP_serverIP[2],
                        DHCP_serverIP[3],
                        ]
        
        return self.constructPacket(packet_field, packet_field_option)

    def DHCPRELEASE(self, clientIP):
        self.outPacket.resetPacket()

        packet_field = {
                        'OP' : 1,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : int( '0x8000', base=16 ),
                        'CIADDR' : clientIP,
                        'YIADDR' : 0,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.MAC, 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16)
                        }

        if specifyRequestedIP == 0:
            requestedIP = self.decIP_split( self.inPacket.getField('YIADDR') )
        else:
            requestedIP = list( map( lambda x: int(x), specifyRequestedIP.split('.') ) )
        DHCP_serverIP = self.decIP_split( self.inPacket.getField('OPTION')[54] )

        packet_field_option = [
                        53, #DHCP Message Type
                        1,
                        7,  #DHCPRELEASE
                        54,  #DHCP Server Identifier
                        4,
                        DHCP_serverIP[0],
                        DHCP_serverIP[1],
                        DHCP_serverIP[2],
                        DHCP_serverIP[3],
                        61,   #Client identifier
                        7,
                        1,
                        ]
        #MAC
        for index in range(6):
            packet_field_option.append( int( '0x' + hex(self.MAC)[2:][index*2:index*2+1+1], base=16 ) )
        
        return self.constructPacket(packet_field, packet_field_option)


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
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser('specify socket argument')
    parser.add_argument('-p', '--port',type=int, default=68,
                        help='the binding port')
    parser.add_argument('-IP', default=0,
                        help='specify requested IP')
    args = parser.parse_args()

    port = args.port
    specifyRequestedIP = args.IP
    
    client = Client()
    client.process( port, specifyRequestedIP )

    
