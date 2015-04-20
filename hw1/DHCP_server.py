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
                print( data )

                #send DHCPOFFER
                data = self.DHCPOFFER()
                print('send DHCPOFFER')
                print( data )
                sock.sendto( data, ('255.255.255.255', 68) )
                #sock.sendto( data, ('255.255.255.255', 20000) )    #for testing local

                #wait DHCPREQUEST
                data, addr = sock.recvfrom(self.BUFSIZE)
                self.packetAnalysis(data)

                destIP = '255.255.255.255'
            else:
                destIP = self.decIP_to_string( self.inPacket.getField('CIADDR') )

            #receive DHCPREQUEST
            print('receive DHCPREQUEST packet from {}'.format(addr))
            print(data)

            #send DHCPACK
            data = self.DHCPACK()
            print('send DHCPACK')
            print(data)
            sock.sendto( data, (destIP, 68) )
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

        packet_field = {
                        'OP' : 2,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : int('0x8000', base=16),
                        'CIADDR' : 0,
                        'YIADDR' : int('0xc0a8881', base=16),
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
                        20,
                        54, #DHCP Server
                        4,
                        192,
                        168,
                        136,
                        134
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

    def DHCPACK(self):
        self.outPacket.resetPacket()

        packet_field = {
                        'OP' : 2,
                        'HTYPE' : 1,
                        'HLEN' : 6,
                        'HOPS' :  0,
                        'XID' : self.inPacket.getField('XID'),
                        'SECS' : 0,
                        'FLAGS' : int('0x8000', base=16),
                        'CIADDR' : 0,
                        'YIADDR' : int('0xc0a8881', base=16),
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
                        20,
                        54, #DHCP Server
                        4,
                        192,
                        168,
                        136,
                        134
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

    def decIP_to_string(self, decIP):
        IP = ''
        
        hexIP = hex(decIP)
        for index in range(0, 3+1):
            if IP != '':
                IP += '.'
            IP += str( int('0x' + hexIP[ (index+1) * 2 : (index+2)*2 ], base=16) )

        return IP

if __name__ == "__main__":
    server = Server()
    server.process()

    
