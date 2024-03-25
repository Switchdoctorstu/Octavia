# Main Octavia Client
#
#  Stuart Oldfield 2024
#
# pitch around x
# yaw around y
# roll around z

#from asyncio import Handle
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

import socket

from skybox import skybox

# Settings
datamode="udp"


db_config = {
    'user': 'stu',
    'password': 'v400oom',
    'host': '192.168.0.166',
    'database': 'worldDB',
}


# Function to draw the ships

# Read object locations from the MySQL database
def read_ship_locations():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT X,Y,Z , Rx , Ry , Rx FROM Ships')
    data = cursor.fetchall()
    conn.close()
    return data


def check_players_exist():              # Check if any players exist in the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM Ships')
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def create_new_player():            # Prompt the user to create a new player

    # Implement code to get user input for new player creation
    print("No players found. Let's create a new player.")
    pname = (input("Player Name"))
    # Get user input for new player creation
    x = float(input("Enter X coordinate: "))
    y = float(input("Enter Y coordinate: "))
    z = float(input("Enter Z coordinate: "))

    # Insert the new player into the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Assuming 'object_locations' table has columns 'x', 'y', 'z'
    cursor.execute('INSERT INTO Players ( Player_Name , X , Y , Z ) VALUES ( %s , %s , %s , %s)', (pname, x, y, z))

    conn.commit()
    conn.close()

def handle_joystick_movement(joystick):         # Manage Joystick Movement 
    sensitivity = 0.1
    axes = joystick.get_numaxes()
    for i in range(axes):
        axis = joystick.get_axis(i)
        if debug_joystick:
            print( axis, " ", end = "")
        # Adjust camera based on joystick axes
        if i == 0:  # X-axis
            glRotate(axis* sensitivity,0,1,0)
            #glTranslatef(axis, 0.0, 0.0)
        elif i == 1:  # Y-axis
            glRotate(axis* sensitivity,1,0,0)
            #glTranslatef(0.0, -axis, 0.0)
        elif i == 2:  # Z-axis
            glRotate(axis * sensitivity,0,0,1)
            #glTranslatef(0.0, 0.0, axis)
    if debug_joystick:
        print("")


def handle_mouse_movement(thisCamera, viewlock, thisShip):
    # Check if the left mouse button is pressed (index 0 corresponds to the left button)
    left_mouse_pressed = pygame.mouse.get_pressed()[0]
    # Check if the right mouse button is pressed (index 2 corresponds to the right button)
    right_mouse_pressed = pygame.mouse.get_pressed()[2]
    translation_speed = 0.1
    mx, my = pygame.mouse.get_rel()
    
    mx = mx * translation_speed
    my = my * translation_speed
    if not mx==0 or not my==0:
        if viewlock:                    # we're locked to the ship
            if right_mouse_pressed:     # orbit camera
                if debug_mouse:
                    print ("right mouse orbit - locked mx:", mx , " My:",my, thisCamera.rx, thisCamera.ry,thisCamera.rz)
                thisCamera.orbit_relative(my,mx)        # reversed deliberately
            if left_mouse_pressed:      # move camera
                if debug_mouse:
                    print ("left mouse move - locked mx:", mx , " My:",my,thisCamera.rx, thisCamera.ry,thisCamera.rz)
                thisCamera.move_relative(mx,my,0)
       
        else:
            if left_mouse_pressed:      # move camera
            
                thisCamera.move_relative(mx,my,0)
       
    
            if right_mouse_pressed:     # rotate camera
                if debug_mouse:
                    print ("right mouse - unlocked mx:", mx , " My:",my)
                thisCamera.add_rotation(-my,-mx,0)
        
        

def read_world(targetWorld , modelList):            # Read shapes from database
    # first get a list of shapes
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT Object_Name, Model_Name, XLocation, YLocation, ZLocation, XScale,YScale,ZScale , Xrot, Yrot, Zrot FROM Objects')
    data = cursor.fetchall()
    conn.close()
    
    print("building object data")
    # go through the data to get the shapes
    for obj in data:
        Object_Name, Model_Name, XLocation, YLocation, ZLocation, XScale,YScale,ZScale , Xrot, Yrot, Zrot = obj
        
        basemodel = modelList.get_by_name(Model_Name, False)
        
        myobject=object(Object_Name,XLocation,YLocation,ZLocation,Xrot,Yrot,Zrot,XScale,YScale,ZScale)
        myobject.addObj(basemodel)
        # add them to the world
        targetWorld.addObject(myobject)
    
def get_udp_data(socket, myShipList, myModels):               # Listen to UDP Socket
    gotsome=False
    try:
        data, addr = socket.recvfrom(4096)
        gotsome=True
    except Exception as e:
        if debug_UDP:
            print("UDP Check Failed")
        gotsome=False
        pass

    if gotsome:
        decoded=json.loads(data)
        these_ships=decoded.get('ship_list',[])
        if debug_UDP:
            print("Octavia Client - Got UDP data")
            print(decoded)
        
        for ships in these_ships:              # loop thru the data
            objects= ships["objects"]
            AMx = ships["AMx"]
            AMy = ships["AMy"]
            AMz = ships["AMz"]
            Cx = ships["Cx"]
            Cy = ships["Cy"]
            Cz = ships["Cz"]
            Drag = ships["Drag"]
            Id = ships["Id"]
            Name = ships["Name"]
            Thrust = ships["Thrust"]
            Vx = ships["Vx"]
            Vy = ships["Vy"]
            Vz = ships["Vz"]
            rx = ships["rx"]
            ry = ships["ry"]
            rz = ships["rz"]
            x = ships["x"]
            y = ships["y"]
            z = ships["z"]
            expiry = ships["expiry"]
            model_name=ships["base_model"]
            index=float(Id)
            # find the relevant entry
            found = False
            for ship in myShipList.ship_list:
                if index == ship.Id:
                    found=True
                    # updata the relevant ship with details from the UDP received
                    ship.update( Name , model_name, x, y , z, rx, ry , rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz, expiry)
            if found == False:
                # we've not seen this ship before
                # build a new ship
                newShip =   ship_GL(Id, Name, model_name , x, y , z, rx, ry , rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz, expiry)
                newModel =  myModels.get_by_name(model_name,True)
                newShip.add_model(newModel)
                # add it to the shiplist
                myShipList.add_ship(newShip)    
    # remove any expired ships
    now = time.time()
    for ship in myShipList.ship_list:
        
        if ship.expiry > 0:
            if now>ship.expiry:
                myShipList.remove_ship(ship)
                
    
def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

def display_message(message, xpos , ypos,font, surface):         # Function to display a message 
    # Display the message
    # define the RGB value for white,
    #  green, blue colour .
    white = (255, 255, 255)
    green = (0, 255, 0)
    blue = (0, 0, 128)
    text_surface = font.render(message, True, green , blue)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(xpos,ypos)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def send_command(command_to_send, sender_socket,receiver_ip, receiver_port):         
    mystring=command_to_send.toJson()
    if debug_command:
        print("Sending Command:", mystring)
    mybytes=mystring.encode('utf-8')
                
    data_to_send = bytearray(mybytes)
    sender_socket.sendto(data_to_send, (receiver_ip, receiver_port))
    command_to_send.set_sent(True)
            
def handle_keyboard(myCamera, helm,viewlock):
    command=False                       # we don't have a command yet
    fire=False
    cx=helm.cx
    cy=helm.cy
    cz=helm.cz
    thrust=helm.thrust
    running = True
    status_text=""
    # test resetting controls
    cx=0
    cy=0
    cz=0
    #thrust=0.1
    
    last_helm=helm
    for event in pygame.event.get():
       if event.type == pygame.QUIT:
           running= False
       elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_LSHIFT or event.key == K_RSHIFT:
                # Left Shift or Right Shift is pressed
                thrust=0.1
                status_text="Thrust!"
                command=True
       elif event.type == KEYUP:
            if event.key == K_LSHIFT or event.key == K_RSHIFT:
                # Left Shift or Right Shift is released
                thrust=0.0
                status_text=""
                command=True
       elif event.type == MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll Up
                
                myCamera.zoom_in(1)
               
                myCamera.move_forward(myCamera.zoom_speed*1/myCamera.move_speed)
                if debug_mouse: print("Mouse Event 4 - Zoom:", myCamera.zoom)
            elif event.button == 5:  # Scroll Down
                myCamera.zoom_out(1)
                myCamera.move_backward(myCamera.zoom_speed*1/myCamera.move_speed)
                if debug_mouse: print("Mouse Event 5 - Zoom:", myCamera.zoom)
    # Handle Individual Keys
    #region 
    keypress = pygame.key.get_pressed()
    
    if keypress[pygame.K_UP]:
       myCamera.move_forward(1)
       #myCamera.move_in()
    if keypress[pygame.K_DOWN]:
       #myCamera.move_out()
       myCamera.move_backward(1)
    if keypress[pygame.K_RIGHT]:
       myCamera.move_right()
    if keypress[pygame.K_LEFT]:
       myCamera.move_left()
    if keypress[pygame.K_l]:
        # lock / unlock display to ship
        if viewlock:
            status_text="View Undocked"
            viewlock=False
        else:
            status_text="View Docked"
            viewlock=True
    if keypress[pygame.K_w]:
        # yaw+
        command=True
        cx=1
    if keypress[pygame.K_s]:
        # yaw 
        cx=-1
        command=True
    if keypress[pygame.K_e]:
        # pitch +
        cy=1
        command=True
    if keypress[pygame.K_q]:
        #pitch -
        cy=-1
        command=True
    if keypress[pygame.K_a]:
        # roll +
        cz=1
        command=True
    if keypress[pygame.K_d]:
        # roll -
        cz=-1
        command=True
    if keypress[pygame.K_SPACE]:
        # fire !
        fire=True
        status_text="Fire!"
        command=True
    if keypress[pygame.K_r]:
        # respawn
        
        status_text="Respawn"
        command=True
    if keypress[pygame.K_z]:
        # reset camera
        myCamera.set_location(0,0,0)
        myCamera.set_rotation(0,0,0)

    #endregion

        
        
    helm.update(fire, cx,cy,cz,thrust, status_text)
        
       
    return(running, viewlock, status_text)

def pre_load_models(myModels):          # preset some of the object rotations
    obj=myModels.get_by_name("YellowSubmarine.obj", False)
    obj.set_rotation(00,0,0)
    #obj=myModels.get_by_name("RedSubmarine.obj", False)
    #obj.set_rotation(00,00,0)
    #obj=myModels.get_by_name("missile1.obj", False)
    #obj.set_rotation(90,0,270)
    #obj.set_scale(0.1,0.1,0.1)
##################################################################
# Code starts here
# 
##################################################################
     
debug_UDP = False
debug_command = False    
debug_joystick = False
debug_mouse = True
debug_ships = False  
debug_camera = True
debug_texture = True

# Main function
def main():
    # main code starts here
    running = True
    # set debug message levels
    global debug_UDP
    global debug_command
    global debug_joystick
    global debug_mouse
    global debug_ships
    global debug_camera
    global debug_texture
    status_text=""
    
    
    viewlock=False                       # lock the view to the ship
    # setup udp sockets for catching ship broadcasts
    print("Setting up Sockets")
    
    #setup IP Connection Definitions
    #region Setup IP
    # Create UDP socket
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Receiver's IP and port (broadcast address)
    target_ip = '255.255.255.255'  # Broadcast address
    target_port = 12346

    # Set socket to allow broadcast
    sender_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # setup udp sockets for catching ship broadcasts
    # Receiver's IP and port
    receiver_ip = '0.0.0.0'  # Listen on all available interfaces
    receiver_port = 12345

    # Create UDP socket
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the receiver's IP and port
    receiver_socket.bind((receiver_ip, receiver_port))
    # Set socket to non-blocking
    receiver_socket.setblocking(False)
    #endregion

    #setup screen
    #region
    #setup scaling factors for drawing objects
    world_scale = float(0.1)
    ship_scale=float(0.5)
    # setup display
    screen_width=960
    screen_height=640
    pygame.init()               # <- It all starts here
    pygame.display.set_caption('Octavia Client V0.1')
    viewport = (screen_width,screen_height)
    display_surface = pygame.display.set_mode(viewport, OPENGL | DOUBLEBUF)
    glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)           # 
    #endregion
    
    # Set up perspective
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90.0, screen_width/float(screen_height), 1, 100.0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_MODELVIEW)
    

    # setup camera
    myCamera = camera(0,-10,0,debug_camera)
    #myCamera= camera_new(position=[0, 0, 3], target=[0, 0, 0], up = [0,1,0], debug=debug_camera)
    #glTranslatef(0.0, 0.0, -10)         # move to starting position
    myCamera.point_at(0,0,0)
    
    font = pygame.font.SysFont('freesansbold.ttf', 32) # Set up font

    # Initialize Joystick
    pygame.joystick.init()
    joystick_count = pygame.joystick.get_count()
    
    if joystick_count == 0:
        print("No joystick found.")
    else:
        print("Found ", joystick_count, " Joysticks")
        joystick = pygame.joystick.Joystick(0)
    
    #get a fresh world
    print("Building World...")
    myModels = model_list()             # an empty set of models
    myWorld=world()                     # an empty world
    read_world(myWorld, myModels)
    
    #setup texture manager
    myTextures = texture_list(DEBUG=debug_texture)

    # and the skybox
    mySkybox = skybox("sea2.jpg", myTextures)
    player_name="stu"

    if not check_players_exist()  :
        create_new_player()

    # pre-load the models we want
    pre_load_models(myModels)
    
    #region
    print("Loading Ships")
    # create a new list of ships
    myshiplist=shiplist(True,True)       # set to auto-build and include GL
  
    # get the initial ship data
    
    print("Getting Ships from DB")
     
    myshiplist.load_from_db()   # read in ships
    
    # add shapes to the ships
    
    for sh in myshiplist.ship_list:
        obj=myModels.get_by_name(sh.base_model, True)
        sh.addShape(obj)
    #endregion

    dbupdate_timer = 0.5        #seconds between calls
    nextdbupdate = time.time()+dbupdate_timer
    
    # setup clock
    clock = pygame.time.Clock()
    seconds_passed = 0

    

    my_ship_id=float(0)
    my_helm = pilot_command(my_ship_id,0,False,0,0,0,0,"Hello")
    # get my ship
    for s in myshiplist.ship_list:
        if float(s.Id)==float(my_ship_id):
            myShip = s
    myCamera.point_at(myShip.x,myShip.y,myShip.z)
    myCamera.set_zoom(10)
    
    print("Entering main loop....")

    while running:
        # each frame we clear the buffer 
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)                # clear our screen buffer
        # set the viewpoint
        #region
        
        myCamera.look()
        
        #endregion
        # get keyboard input 
        running, viewlock , status_text = handle_keyboard(myCamera, my_helm ,viewlock)
        if not my_helm.sent:
            # we have an unsent command
            send_command(my_helm,sender_socket,target_ip,target_port)
            # my_helm.set_sent(True)
        handle_mouse_movement(myCamera,viewlock, myShip)
        
        if joystick_count>0:
            handle_joystick_movement(joystick)        

        # Update player position 
        lastcount=myshiplist.count
        t=time.time()
        if t> nextdbupdate:
            if datamode == "database":          # from settings at top of code
                myshiplist.update_from_db()
            
            #myshiplist.buildships()
            nextdbupdate += dbupdate_timer
        if datamode=="udp":
            if debug_UDP:
                print("getting udp")
            get_udp_data(receiver_socket, myshiplist, myModels)   
        if debug_ships:
            if myshiplist.count != lastcount:
                print(" Number of ships changed to:", myshiplist.count)
       
        mySkybox.render()                  # draw the skybox
        myWorld.render(world_scale)        #draw the world
        
        
        myshiplist.render(ship_scale)       # draw_ships()                  #draw the ships
        
        
        if status_text != "":
            display_message(status_text, 64, 64,font , display_surface)
        if debug_camera:
            cam_text = "loc:"
            for i in myCamera.position:
                cam_text += f" {i:.2f}"  # Display only first two decimals
            cam_text += f" Rx:{myCamera.rx:.2f} Ry:{myCamera.ry:.2f} Rz:{myCamera.rz:.2f}"
            display_message(cam_text, 32, 64, font, display_surface)
            cam_text = f" Tx:{myCamera.target[0]:.2f} Ty:{myCamera.target[1]:.2f} Tz:{myCamera.target[2]:.2f}"
            display_message(cam_text, 32, 32, font, display_surface)


        pygame.display.flip()
        pygame.time.wait(10)
    #shutdown gracefuly
    for ships in myshiplist.ship_list:
        for things in ships.objects:
            things.free()
    pygame.quit()
    quit()
################################################################################
#  END OF MAIN CODE
###############################################################
          
if __name__ == '__main__':
    main()


