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




class shape():   
    def __init__(self,ident, name,vertices,edges,triangle_strip):
        self.id=ident
        self.name=name
        self.vertices=vertices
        self.edges=edges
        self.trianglestrip=triangle_strip
        self.gllist=glGenLists(1)           #generated by build
        self.verticelist = []
    def build(self):
        # convert vertices string to vertice list
        self.verticelist.clear()
        for value in self.vertices.split(';'):
            v=vertice.from_string(value)
            self.verticelist.append(v)
        glNewList(self.gllist,GL_COMPILE)
        glBegin(GL_TRIANGLE_STRIP)
        glColor3f(1.0, 1.0, 1.0)  # White color
        for t in self.trianglestrip.split(';'):
            vx, vy, vz = map(float, t.split(','))
            glVertex3f(vx,vy,vz)
        glEnd()
        glBegin(GL_LINES)
        glColor3f(0.0, 0.5, 1.0)  # ?? color
        for edge in self.edges.split(';'):
            for vertex in edge.split(','):
                vx=self.verticelist[int(vertex)].x
                vy=self.verticelist[int(vertex)].y
                vz=self.verticelist[int(vertex)].z
#
                glVertex3f(vx,vy,vz)
        glEnd()
        glEndList()
    def render(self,pos,size,rot , scale):
        glPushMatrix()
        glTranslatef(pos.x,pos.y,pos.z)
        glScale(scale,scale,scale)
        #glColor4f(self.color.r, self.color.g, self.color.b, 1)
        #glBindTexture(GL_TEXTURE_2D,self.texture)   
        glCallList(self.gllist)
        glPopMatrix()
       


class world():
    def __init__(self):
        self.objectList = []
    def __iter__(self):
        return iter(self.objectList)
    def addObject(self,s):
        self.objectList.append(s)
    def getObjectList(self):
        return self.objectList
    def build(self):
        for s in self.objectList:
            s.build()
    def render(self, scale):
        for s in self.objectList:
            s.render(scale)


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

# Check if any players exist in the database
def check_players_exist():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM Ships')
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# Prompt the user to create a new player
def create_new_player():

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


def handle_mouse_movement():
    # Check if the left mouse button is pressed (index 0 corresponds to the left button)
    left_mouse_pressed = pygame.mouse.get_pressed()[0]
    # Check if the right mouse button is pressed (index 2 corresponds to the right button)
    right_mouse_pressed = pygame.mouse.get_pressed()[2]
    
    if left_mouse_pressed:
        mx, my = pygame.mouse.get_rel()
        sensitivity = 0.1
        glRotatef(-mx * sensitivity, 0, 1, 0)
        glRotatef(-my * sensitivity, 1, 0, 0)
    
    if right_mouse_pressed:
        mx, my = pygame.mouse.get_rel()
        translation_speed = 0.01
        glTranslatef(mx * translation_speed, -my * translation_speed, 0)

# Read shapes from database
def read_world(targetWorld):
    # first get a list of shapes
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT ID, name, ModelID, XLocation, YLocation, ZLocation, XScale,YScale,ZScale , Xrot, Yrot, Zrot FROM Objects')
    data = cursor.fetchall()
    conn.close()
    
    global shapelist
    modellist=[] 
    idlist=[]
    n=0
    print("building object data")
    # go through the data to get the shapes
    for obj in data:
        ID, name, ModelID, XLocation, YLocation, ZLocation, XScale,YScale,ZScale , Xrot, Yrot, Zrot = obj
        # see if it is unique
        if ID in idlist :
            # model already e
            a=0
        else:
            #model is new
            file=name=name+".obj"
            modellist.append(OBJ(name, False))  #build new objects and add to our list
            idlist.append(ID)

        
        
        myobject=object(name,XLocation,YLocation,ZLocation,Xrot,Yrot,Zrot,XScale,YScale,ZScale)
        myobject.addObj(modellist[int(ID)])
        # add them to the world
        targetWorld.addObject(myobject)
    

        
##################################################################
# Code starts here
# 
##################################################################
        

# Main function
def main():
    #setup scaling factors for drawing objects
    world_scale = float(0.1)
    ship_scale=float(0.5)
    # setup display
    pygame.init()
    viewport = (1920,1080)
    hx = viewport[0]/2
    hy = viewport[1]/2
    srf = pygame.display.set_mode(viewport, OPENGL | DOUBLEBUF)

    glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)           # 
   
    
    #get a fresh world
    myWorld=world()
    read_world(myWorld)
    #build the shapes
    print("Building World...")
    #myWorld.build()

    player_name="stu"

    if not check_players_exist()  :
        create_new_player()


    # LOAD Ship Shapes
    print("Loading Ships")
    obj = OBJ("YellowSubmarine.obj", swapyz=False)
    #obj.generate()
    print("Done Yellow")
    obj1 = OBJ("RedSubmarine.obj" , swapyz=False)
    #obj1.generate()
    print("Done Red")
    obj2 = OBJ("Dorand.obj" , swapyz=False)
    #obj2.generate()
    print("Done Dorand")
    # get the initial ship data
    #global ship_locations
    print("Getting Ships from DB")
    global myshiplist       # create a new list of ships
    myshiplist=shiplist()
    
    myshiplist.load_from_db()   # read in ships
    
    # add shapes to the ships
    shipcount=0
    for sh in myshiplist.list:
        if shipcount == 0:
            sh.addShape(obj)
        else:
            sh.addShape(obj2)
        shipcount += 1

    dbupdate_timer = 0.5        #seconds between calls
    nextdbupdate = time.time()+dbupdate_timer
    
    # setup clock
    clock = pygame.time.Clock()
    seconds_passed = 0

    #glOrtho(-10, 10, -10, 10, 0.01, 10.0)  # Orthographic projection
    
    #gluLookAt(-2, 2, -2,  # eye position
    #          0, 0, 0,  # center of view
    #          0, 1, 0)  # up vector
    # Set up perspective
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    width, height = viewport
    gluPerspective(90.0, width/float(height), 1, 100.0)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_MODELVIEW)
    
    glTranslatef(0.0, 0.0, -10)

   

    print("Entering main loop....")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        keypress = pygame.key.get_pressed()#Move using WASD
        if keypress[pygame.K_w]:
            glTranslatef(0,0,0.1)
        if keypress[pygame.K_s]:
            glTranslatef(0,0,-0.1)
        if keypress[pygame.K_d]:
            glTranslatef(-0.1,0,0)
        if keypress[pygame.K_a]:
            glTranslatef(0.1,0,0)
        #glRotatef(1, 2, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        handle_mouse_movement()
        
        # Update player position 
        t=time.time()
        if t> nextdbupdate:
            myshiplist.update_from_db()
            #myshiplist.buildships()
            nextdbupdate += dbupdate_timer
                
        myWorld.render(world_scale)        #draw the world
        # draw_ships()                  #draw the ships
       
        myshiplist.render(ship_scale)

        

        pygame.display.flip()
        pygame.time.wait(10)
################################################################################
#  END OF MAIN CODE
###############################################################
          
if __name__ == '__main__':
    main()


