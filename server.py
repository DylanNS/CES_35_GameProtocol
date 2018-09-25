#!/usr/bin/env python

"""
CES-35 Lab3 Game Application Protocol
Author: Dylan N Sugimoto Gabriel Adriano de Melo
Data: 23/09/2018
"""

import socket
from copy import copy
from struct import pack, unpack, iter_unpack, calcsize
from threading import Thread, Lock
class Menssage:

    def __init__(self, format):

        self.format = format
        self.last_message = ""
        self.last_pack =""
        self.last_list_message =[]
    def packing(self, values):
        self.last_pack = pack(self.format,* values) 
        return copy(self.last_pack)
    def unpacking(self, bytestream):
        self.last_message = unpack(self.format,bytestream)
        return copy(self.last_message)
    def calc_format_size(self):
        return calcsize(self.format)
    def iterate_buffer_unpacking(self,buffer):

        self.last_list_message = []
        tuples = iter_unpack(self.format,buffer)
        for t in tuples:
            self.last_list_message.append(t)
        return copy(self.last_list_message)
    def get_format (self):
        return copy(self.format)
    def get_last_pack(self):
        return copy(self.last_pack)
    def get_last_message(self):
        return copy(self.last_message)
    def get_last_list_message(self):
        return copy(self.last_list_message)

class Client:

    def __init__(self,address,socket,id=None,name = None):

        self.name = name
        self.socket = socket
        self.address = address
        self.id = id
        self.color = ""
        self.room = ""
        self.socket_lock_recebe = Lock()
        self.socket_lock_envia = Lock()
        self.pronto = False
    
    def GET(self,data_size):
        self.socket_lock_recebe.acquire(1)
        chunks = []
        bytes_recd = 0
        #print('getting')
        while bytes_recd < data_size:
            #print('pedindo', min(data_size - bytes_recd, 2048))
            chunk = self.socket.recv(1024) # É o tamanho máximo do buffer
            if chunk == b'':
                self.socket_lock_recebe.release()
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        self.socket_lock_recebe.release()
        return b''.join(chunks)
    def POST(self,data):
        self.socket_lock_envia.acquire(1)
        totalsent = 0
        while totalsent < len(data):
            sent = self.socket.send(data[totalsent:])
            if sent == 0:
                self.socket_lock_envia.release()
                raise RuntimeError("socket connection broken")
            totalsent += + sent
        self.socket_lock_envia.release()
        return


            
       
host = 'localhost'
port = 50019  #server port
backlog = 64 # buffer size
#allocate socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#link host to port
s.bind((host,port))
#enable to receive connection
s.listen(backlog)
#Tamanho da Sala
room_Max_Size = 32
#Numero de Salas
max_number_rooms = 1


'''     msg1_cliente :  "msg Type(unsigned char), name ( 32 string), cor (int)"
        msg2_servidor:  "msg Type(unsigned char),sim/nao (bool),Sala (int),id (int)"
        msg3_cliente:   "msg Type(unsigned char)" baixar mapa
        msg4_sevidor:   "msg Type(unsigned char), float,float,float,float" initmapa
        msg5_servidor:  "msg Type(unsigned char)" fimdemapa
        msg6_cliente:   "msg Type(unsigned char),ID (int),posx (float),posy (float),vx (float),vy (float),ax (float),ay (float)"
        msg7_servidor:  "msg Type(unsigned char),ID (int), posx (float), posy (float),vx (float),vy (float),ax (float),ay (float)" broadcast

            Format | C Type      |   Python Type | Size
            B	   |unsigned char|	 integer     |	1
            ?	   | _Bool	     |   bool	     |  1
            i	   |int	         |   integer	 |  4
            f	   |float	     |   float	     |  4
            s	   |char[]	     |   bytes	 
'''
list_msg_format = [0,
                    "B32si",
                    "B?ii",
                    "B",
                    "Bffff",
                    "B",
                    "Biffffff",
                    "Biffffff"
                    ]
list_msg = []
dic_clients = {}
rooms =[]
#init rooms
for i in range(max_number_rooms):
    rooms.append({})
#init list_msg
for f in list_msg_format:
    list_msg.append(Menssage(f))

iis = [0 for i in range(32)]

class Client_t (Thread):
   def __init__(self, threadID, name, cliente):
      Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.cliente = cliente
      self.i=0
   
   def run(self):
       client = self.cliente
       while True:
            #hear client request
            try:
                rawdata = client.GET(list_msg[3].calc_format_size())
                msg_info = list_msg[3].unpacking(rawdata[:1])
            except:
                print('problema detectado, abortando!!!')
                self.close_conn(client)
                return
            if msg_info[0] == 3:
                print("Received ",msg_info," from ",client.address)
                #send map to client
                msg4 = (4,7.0,19.0,20.0,111.0)
                try:
                    client.POST(list_msg[4].packing(msg4))
                    print("Send ",msg4," to client ",client.address)
                except:
                    self.close_conn(client)
                    return
                msg5 = (5,)
                try:
                    client.POST(list_msg[5].packing(msg5))
                    print("Send ",msg5," to client ",client.address)
                    client.pronto = True
                except:
                    print('Erro ao enviar confimação de fim de mapa')
                    self.close_conn(client)
                    return
                
            elif msg_info[0] == 6:
                #get rest of the menssage
                try:
                    #rawdata = client.GET(list_msg[6].calc_format_size())
                    msg_info = list_msg[6].unpacking(rawdata)
                    self.i += 1
                    if self.i%1 == 0:
                        print("Received ",msg_info," from ",client.address)
                except:
                    print('Erro ao receber informações do cliente')
                    self.close_conn(client)
                    return
                #msg7 : "7,id,pox,posy,velx,vely,ax,ay"
                msg7 = (7,) + msg_info[1:]
                #send coord and other attributes to all others clients in the room

                self.multicast(client,msg7)
       return
   def multicast(self,client,msg):
        #multicast in client's room
        for c in rooms[client.room].values():

            if c.id == client.id or not c.pronto:
                next
            else:
                #send msg7 to client
                try:
                    c.POST(list_msg[7].packing(msg))
                    iis[c.id] += 1
                    if iis[c.id]%1 == 0:
                        print("Send ",msg," to client ",c.address)
                except:
                    print('Erro ao enviar para o cliente', c.address)
                    next
        return
        
   def close_conn(self,client):
        client.socket.close()
        dic_clients.pop(client.id)
        rooms[client.room].pop(client.id)
        return

class Accept_client_t (Thread):
    def __init__(self, threadID, name):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.clients_t = []
   
    def run(self):
        self.Accept_client()
        self.wait_for_client_t()
        return
    def Accept_client(self):
        next_client_id = 1
        while True:
            #receive client socket and address
            socket_client, address = s.accept()
            #instance client
            new_c = Client(address,socket_client)
            #get msg1 from client
            try:
                rawdata1 = new_c.GET(list_msg[1].calc_format_size())
                erro1 = False
            except:
                print("Fail to read socket", new_c.address)
                erro1 = True
            #verify if there is a slot in any room
            has_room = False
            new_c_room = -1
            if not erro1:
                for r in rooms:
                    if len(r) < room_Max_Size:
                        new_c.room = new_c_room = rooms.index(r)
                        r[next_client_id] = new_c
                        new_c.id =  next_client_id
                        next_client_id+=1
                        has_room = True
                        break
            if has_room:
                #decode rawdata1
                msg1 = list_msg[1].unpacking(rawdata1)
                new_c_name = msg1[1].split(b'\x00')[0].decode('utf-8')
                print("Received Type: ",msg1[0],"name: ",new_c_name,"color: ",msg1[2]," from ",new_c.address)
                #add to client dic
                dic_clients[new_c.id]=new_c
                #register name
                new_c.name = msg1[1]
                #register color
                new_c.color = msg1[2]
                #build msg2 "2,True,room.id,id"
                msg2 = (2,True,new_c_room,new_c.id)
                #create Client thread
                self.clients_t.append(Client_t(new_c.id,"Thread Client",new_c).start())
            else:
                #decline conn, build msg2 "2,False,-1,-1"
                msg2 = (2,False,-1,-1)
                
            try:
                #send msg2 to client
                new_c.POST(list_msg[2].packing(msg2))
                print("Send ",msg2," to client ",new_c.address)
            except:
                print("Fail to send msg2 to client!",new_c.address)
            print('cliente tratado', new_c.address)
                    

        return
    def wait_for_client_t(self):
        for t in self.clients_t:
            t.join()
        return




#create accept client thread
print("Server is Online!")
acct = Accept_client_t(1,"Accept Client Thread")
acct.start()
acct.join()
