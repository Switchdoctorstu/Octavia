################################################################################################
#
#  Octavia Server
# Open Database and stream items on UDP
#
################################################################################################


import socket


import json
from dataclasses import dataclass
from tokenize import String
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import mysql.connector
import pygame
from pygame.locals import *
import time
from Octavia_Classes import *

# classes

class localshiplist():
    def __init__(self): 
        self.ship_list = []
        self.count=0
        self.lastcount=0
        self.auto_build=True
    def load_from_db(self):
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Ships')
        data = cursor.fetchall()
        self.ship_list.clear()
        countships=0
        for each_ship in data:
            idShips, ID, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = each_ship
            # convert text to floats
            x=float(X)
            y=float(Y)
            z=float(Z)
            rx=float(Rx)
            ry = float(Ry)
            rz = float(Rz)
            cx= float(Cx)
            cy=float(Cy)
            cz=float(Cz)
            amx= float(AMx)
            amy=float(AMy)
            amz=float(AMz)
            thrust=float(Thrust)
            drag=float(Drag)
            vx=float(Vx)
            vy=float(Vy)
            vz=float(Vz)
            
            newShip = localship(ID, Name , x, y , z, rx, ry , rz, thrust , drag , amx, amy, amz, vx, vy, vz, cx, cy, cz)
            self.ship_list.append(newShip)
            countships+=1
        self.count=countships
    def update_from_db(self):
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Ships')
        data = cursor.fetchall()
        
        countships=0
        for each_ship in data:
            idShips, ID, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = each_ship
            # convert text to floats
            x=float(X)
            y=float(Y)
            z=float(Z)
            rx=float(Rx)
            ry = float(Ry)
            rz = float(Rz)
            cx= float(Cx)
            cy=float(Cy)
            cz=float(Cz)
            amx= float(AMx)
            amy=float(AMy)
            amz=float(AMz)
            thrust=float(Thrust)
            drag=float(Drag)
            vx=float(Vx)
            vy=float(Vy)
            vz=float(Vz)
            
            self.ship_list[countships].update(ID, Name , x, y , z, rx, ry , rz, thrust , drag , amx, amy, amz, vx, vy, vz, cx, cy, cz)
         
            countships+=1
        self.count=countships
    def buildships(self):
        for obj in self.ship_list:
            obj.build()
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)


class localship( ):
    def __init__(self, Id, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz ):
        self.objects =[]
        self.Id=Id 
        self.Name=Name 
        self.x=X
        self.y=Y 
        self.z=Z
        self.rx=Rx 
        self.ry=Ry 
        self.rz=Rz
        self.Thrust = Thrust 
        self.Drag = Drag 
        self.AMx = AMx
        self.AMy = AMy
        self.AMz = AMz
        self.Vx = Vx
        self.Vy = Vy 
        self.Vz = Vz
        self.Cx= Cx 
        self.Cy = Cy
        self.Cz = Cz 
        
    def update(self, Id, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz):
        self.Id=Id 
        self.Name=Name 
        self.x=X
        self.y=Y 
        self.z=Z
        self.rx=Rx 
        self.ry=Ry 
        self.rz=Rz
        self.Thrust = Thrust 
        self.Drag = Drag 
        self.AMx = AMx
        self.AMy = AMy
        self.AMz = AMz
        self.Vx = Vx
        self.Vy = Vy 
        self.Vz = Vz
        self.Cx= Cx 
        self.Cy = Cy
        self.Cz = Cz 
    def build(self):
        
        for obj in self.objects:
            obj.generate()
    def addShape(self,newOBJ):
        self.objects.append(newOBJ)
    
    def toJson(self):
        me = self.Id,      self.Name, self.x, self.y, self.z, self.rx, self.ry, self.rz, self.Thrust, self.Drag, self.AMx, self.AMy , self.AMz, self.Vx, self.Vy, self.Vz ,self.Cx, self.Cy, self.Cz  
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    def fromJson(self, json_object):
        Id, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = json_object
        self.update(Id, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz)
        
            

db_config = {
    'user': 'stu',
    'password': 'v400oom',
    'host': '192.168.0.166',
    'database': 'worldDB',
}



        
##################################################################
# Code starts here
# 
##################################################################
        

# Main function
def main():
    
    print("Getting Ships from DB")
    global myshiplist       # create a new list of ships
    myshiplist=localshiplist()
    
    myshiplist.load_from_db()   # read in ships
    
    numShips= myshiplist.count
    print("Found ",numShips," Ships")
    
    dbupdate_timer = 0.5        #seconds between calls
    nextdbupdate = time.time()+dbupdate_timer
    
    print("Setting up Sockets")
    # Sender's IP and port
    sender_ip = '127.0.0.1'
    sender_port = 12345

    # Create UDP socket
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Receiver's IP and port (broadcast address)
    receiver_ip = '255.255.255.255'  # Broadcast address
    receiver_port = 12345

    # Set socket to allow broadcast
    sender_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    broadcast_timer = 0.5        #seconds between calls
    nextbroadcast = time.time()+broadcast_timer

   

    print("Entering main loop....")

    while True:
        

        
        # Update player position 
        t=time.time()
        if t> nextdbupdate:
            myshiplist.update_from_db()
            #myshiplist.buildships()
            nextdbupdate += dbupdate_timer
            print("server fetched ships from DB:")
            for s in myshiplist.ship_list:
                print( s.toJson())
        if t > nextbroadcast:
            print("Server Broadcasting Ships:")
            #for s in myshiplist.list:
            #    print("Sending",s.Name)
            #    mystring = s.toJson()
            mystring=myshiplist.toJson()
            mybytes=mystring.encode('utf-8')
                
            data_to_send = bytearray(mybytes)
            sender_socket.sendto(data_to_send, (receiver_ip, receiver_port))
            nextbroadcast += broadcast_timer

################################################################################
#  END OF MAIN CODE
###############################################################
          
if __name__ == '__main__':
    main()


