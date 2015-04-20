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

class Client:
    BUFSIZE = 65535
    
    def __init__(self):
        self.IP = ''
        self.submask = ''
        self.router = ''
        self.DNS = ''
        self.MAC = ''

        self.inPacket = DHCP_packet()
        self.outPacket = DHCP_packet()
        
        timeMsg = 'client socket created ({})'.format( datetime.now() )
        print(timeMsg)

    def process(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        #sock.bind( ('192.168.136.1' ,68) )
        sock.bind( ("127.0.0.1" ,20000) )

        #sock.connect( ('192.168.136.134', 67) )

        #set socket timeout
        sock.settimeout(10)
        while True:
            try:
                #send DHCPDISCOVER
                data = self.DHCPDISCOVER()
                print('*** SEND DHCPDISCOVER ***')
                print(data)

                #sock.sendto(data, ('192.168.136.255', 67) )
                sock.sendto(data, ('255.255.255.255', 67) )

                #receive DHCPOFFER
                while True:
                    data, addr = sock.recvfrom(self.BUFSIZE)
                    #if addr[0] != '192.168.136.134':
                    #    continue
                    print('receive DHCPDISCOVER from {}'.format(addr))
                    print(data)
                    break

                self.packetAnalysis(data)

                #send DHCPREQUEST
                data = self.DHCPREQUEST()

                print('*** SEND DHCPREQUEST ***')
                print(data)
                #sock.sendto( data, ('192.168.136.255', 67) )
                sock.sendto(data, ('255.255.255.255', 67) )

                #receive DHCPACK
                while True:
                    data, addr = sock.recvfrom(self.BUFSIZE)
                    #if addr[0] != '192.168.136.134':
                    #    continue
                    print('receive DHCPACK from {}'.format(addr))
                    print(data)
                    break

                self.packetAnalysis(data)
            except socket.timeout:
                print('timeout, DHCPDISCOVER again')
                continue

            break

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
        
        self.outPacket.setField('OP', 1, 1)
        self.outPacket.setField('HTYPE', 1, 1)
        self.outPacket.setField('HLEN', 6, 1)
        self.outPacket.setField('HOPS', 0, 1)
        self.outPacket.setField('XID', int('0x3903F326', base=16), 4)
        self.outPacket.setField('SECS', 0, 2)
        self.outPacket.setField('FLAGS', int('0x8000', base=16), 2) #0x8000  : broadcast
        self.outPacket.setField('CIADDR', 0, 4)
        self.outPacket.setField('YIADDR', 0, 4)
        self.outPacket.setField('SIADDR', 0, 4)
        self.outPacket.setField('GIADDR', 0, 4)
        self.outPacket.setField('CHADDR', int('0x00053C04', base=16), 4)
        self.outPacket.setField('CHADDR', int('0x8D590000', base=16), 4)
        self.outPacket.setField('CHADDR', 0, 8)
        self.outPacket.setField('SNAME', 0, 64)
        self.outPacket.setField('FILE', 0, 128)
        self.outPacket.setField('MAGIC_COOKIE', int('0x63825363', base=16), 4) #DHCP

        #OPTION 53 : DHCPDISCOVER
        self.outPacket.setField('OPTION', 53, 1)
        self.outPacket.setField('OPTION', 1, 1)
        self.outPacket.setField('OPTION', 1, 1)
        #OPTION 50 : request
        self.outPacket.setField('OPTION', 50, 1)
        self.outPacket.setField('OPTION', 4, 1)
        self.outPacket.setField('OPTION', 192, 1)
        self.outPacket.setField('OPTION', 168, 1)
        self.outPacket.setField('OPTION', 1, 1)
        self.outPacket.setField('OPTION', 100, 1)

        #OPTION 255 : end
        self.outPacket.setField('OPTION', 255, 1)
        

        data = self.outPacket.getPacket()

        return data

    def DHCPREQUEST(self):
        self.outPacket.resetPacket()

        packet_field = {
                        'OP' : 1,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : int('0x8000', base=16),
                        'CIADDR' : 0,
                        'YIADDR' : 0,
                        'SIADDR' : 0,
                        'GIADDR' : 0,
                        'CHADDR' : self.inPacket.getField('CHADDR'), 
                        'SNAME' : 0,
                        'FILE' :  0,
                        'MAGIC_COOKIE' : int('0x63825363', base=16)
                        }

        requestedIP = self.decIP_split( self.inPacket.getField('YIADDR') )
        DHCP_serverIP = self.decIP_split( self.inPacket.getField('OPTION')[54] )
        #DHCP_serverIP = self.
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

        index = 0
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
        

if __name__ == "__main__":
    client = Client()
    client.process()

    
