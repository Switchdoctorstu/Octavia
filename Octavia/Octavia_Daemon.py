###########################################################
##
##  DEAMON PROCESSOR FOR OCTAVIA
##
##  Stuart Oldfield 2024
##  V0.11

## todo:
## ship movement - Done
## munition movement
## terrain collision
#
#   Build in UDP server - Done
#   Write database back only every 10 seconds or so - Done
#
#
#   Principles
#   World movement exists only in this program

## set some bounds for ship movement
WorldWidth = float(20)
WorldHeight= float(20)
WorldDepth = float(20)

import math
import time
from tkinter import LAST
from pyquaternion import Quaternion  # Install using: pip install numpy pyquaternion
import socket
import json
from dataclasses import dataclass
from tokenize import String
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
from Octavia_Classes import *
import mysql.connector


# classes

#local ones
# The classes in the library have graphics functions
         

db_config = {
    'user': 'stu',
    'password': 'v400oom',
    'host': '192.168.0.166',
    'database': 'worldDB',
}


def move_ships(myshiplist,elapsed):
    # need to add concept of time
    for ship in myshiplist.ship_list:
        
        if ship.expiry > 0:
            if time.time()>ship.expiry:
                myshiplist.remove_ship(ship)
                
                continue

        rx=math.fmod(ship.rx+ship.Cx , 360)
        ry=math.fmod(ship.ry+ship.Cy , 360)
        rz=math.fmod(ship.rz+ship.Cz , 360)
        ship.update_rotation(rx,ry,rz)
        
        # apply to angular momentum
        if debug_ships:
            print("Ship:", ship.Name ," rx:", ship.rx, "ry:", ship.ry, "rz:", ship.rz)
        
        # engine thrust's forwards so add 90 degrees
        rz=math.fmod(rz+90 , 360)
        # matrix below takes yaw - pitch - roll
        quaternion =    Quaternion(axis=[0, 1, 0], degrees=ry) * \
                        Quaternion(axis=[1, 0, 0], degrees=rx) * \
                        Quaternion(axis=[0, 0, 1], degrees=rz)

        # Calculate the new position based on the ship's orientation
        displacement = quaternion.rotate([0, ship.Thrust*elapsed, 0])
        if debug_ships:
            print("Displacement:", displacement)
        x = ship.x - displacement[0]       # 1
        y = ship.y - displacement[1]       # 2
        z = ship.z - displacement[2]       # 0
        # are we still in the universe?
        x = max(-WorldWidth,min(x,WorldWidth))
        y = max(-WorldHeight,min(y,WorldHeight))
        z = max(-WorldDepth,min(z,WorldDepth))
        ship.update_location(x,y,z)
        if debug_ships:
            print("New Position - x:", ship.x, "y:", ship.y, "z:", ship.z)
        
        
# String functions
def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]


def munitions():
    # move them
    # check collisions
    # check expiry
    pass

def UDP_broadcast(sender_socket,receiver_ip, receiver_port, myshiplist):
    if debug_UDP:
        print("Server Broadcasting Ships:")
            
    mystring=myshiplist.toJson()
    mybytes=mystring.encode('utf-8')
                
    data_to_send = bytearray(mybytes)
    sender_socket.sendto(data_to_send, (receiver_ip, receiver_port))
   
def check_inputs(socket, myshiplist):
    # check for commands from pilots
    pass
    gotsome=False
    try:
        data, addr = socket.recvfrom(1024)
        gotsome=True
    except Exception as e:
        # print("UDP Check Failed")
        gotsome=False
        pass

    if gotsome:
        mystring=data.decode('utf-8')
        now=time.time()
        if debug_command:
            print("Octavia Client - Got UDP data")
            # {"id": 0, "sequence": 71, "fire": false, "cx": 1, "cy": -1, "cz": -1, "thrust": 0, "message": "Fire!", "sent": false}
            print(mystring)
            
        # Parse the JSON string into a Python dictionary
        parsed_data = json.loads(mystring)

        # Access the variables from the dictionary
        id_value = parsed_data["id"]
        sequence_value = parsed_data["sequence"]
        fire_state = parsed_data["fire"]
        cx_value = parsed_data["cx"]
        cy_value = parsed_data["cy"]
        cz_value = parsed_data["cz"]
        thrust_value = parsed_data["thrust"]
        message_value = parsed_data["message"]
        sent_value = parsed_data["sent"]
        
        if message_value=="Respawn":
            for this_ship in myshiplist.ship_list:
                if float(this_ship.Id)==float(id_value):
                    this_ship.reset()

        if debug_command:
            # Now you can use these variables as needed
            print(f"ID: {id_value}")
            print(f"Sequence: {sequence_value}")
            print(f"Fire: {fire_state}")
            print(f"Cx: {cx_value}")
            print(f"Cy: {cy_value}")
            print(f"Cz: {cz_value}")
            print(f"Thrust: {thrust_value}")
            print(f"Message: {message_value}")
            print(f"Sent: {sent_value}")
        
        # now we write the ship data back to the shiplist object
        for this_ship in myshiplist.ship_list:
            if float(this_ship.Id)==float(id_value):
                if fire_state:
                    # the pilot hit fire
                    
                    # spawn off a new ship based on the current ship vectors
                    newID=float(this_ship.Id)+0.1
                    ammo_thrust = 1
                    ammo_drag = 0
                    expiry=now+5
                    shot =ship(newID,"shot","missile1.obj", this_ship.x, this_ship.y, this_ship.z, this_ship.rx, this_ship.ry, this_ship.rz, ammo_thrust, ammo_drag,0,0,0,0,0,0,0,0,0,expiry)
                    shot.set_expiry(time.time()+5)
                    myshiplist.add_ship(shot)
                    if debug_command:
                        print("New object created")

                else: 
                    this_ship.set_controls(thrust_value,cx_value,cy_value,cz_value)
                

##################################################################
# Main Loop 
# 
# Code starts here
# 
##################################################################
 
debug_UDP       = False
debug_command   = True    
debug_db        = False
debug_ships     = False


def main():
    print("We're running")
    now=time.time()                     # what time is it now
    last_move_time=now                  # keep track of time intervals between moves
    global debug_UDP
    global debug_command
    global debug_db
    global debug_ships

    print("Getting Ships from DB")
    # create a new list of ships
    
    myshiplist=shiplist(False, False)   # no need to build or for graphics
    
    myshiplist.load_from_db()   # read in ships
    
    numShips= myshiplist.count
    print("Found ",numShips," Ships")
    
    #setup timing for triggering updates
    ship_update_timer = 0.2
    munitions_update_time = 0.5
    
    ship_trigger=now+ship_update_timer
    munitions_trigger=now+munitions_update_time
    dbupdate_timer = 10        #seconds between DB comits
    nextdbupdate = now+dbupdate_timer
    broadcast_timer = 0.2        #seconds between braodcasts
    nextbroadcast = time.time()+broadcast_timer

    print("Setting up Sockets")
    
    
    # Sender's IP and port
    #sender_ip = '127.0.0.1'
    #sender_port = 12345

    # Create UDP socket
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Receiver's IP and port (broadcast address)
    target_ip = '255.255.255.255'  # Broadcast address
    target_port = 12345

    # Set socket to allow broadcast
    sender_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # setup udp sockets for catching ship broadcasts
    # Receiver's IP and port
    receiver_ip = '0.0.0.0'  # Listen on all available interfaces
    receiver_port = 12346

    # Create UDP socket
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the receiver's IP and port
    receiver_socket.bind((receiver_ip, receiver_port))
    # Set socket to non-blocking
    receiver_socket.setblocking(False)




    # MAIN LOOP
    while True:
        now=time.time()
        check_inputs(receiver_socket, myshiplist)               # process commands from pilots
        move_ships(myshiplist,now - last_move_time)              # move ships
        last_move_time=now    
        if now > munitions_trigger:
            munitions()             # move munitions
            munitions_trigger += munitions_update_time
        
        if now> nextbroadcast:
            UDP_broadcast(sender_socket, target_ip,target_port,myshiplist )
            nextbroadcast += broadcast_timer
            
        if now > nextdbupdate:
            if debug_db:
                print("Commiting to DB ")
            myshiplist.write_to_db()            # write the current data to DB server
            nextdbupdate = now+dbupdate_timer
       
    
     
# Actually launch the code
if __name__ == '__main__':
    main()
##################################################################
#  END OF CODE
##################################################################

