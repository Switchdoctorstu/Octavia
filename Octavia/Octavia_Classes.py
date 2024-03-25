##########################################################################
#
#  Shared Classes for Octavia
#
#  Stuart Oldfield 2024
#
# pitch around x
# yaw around y
# roll around z

import json
import socket
import math
from stat import FILE_ATTRIBUTE_READONLY
from xmlrpc.client import Boolean
import numpy as np
from pyquaternion import Quaternion
import mysql.connector
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import glCallList
import pygame
from pygame.locals import *
import time
from myMaths import *

# database config
db_config = {
    'user': 'stu',
    'password': 'v400oom',
    'host': '192.168.0.166',
    'database': 'worldDB',
}
class pilot_command:
    def __init__(self, id, sequence, fire,cx,cy,cz,thrust, message):
        self.id=id
        self.sequence= sequence
        self.fire=fire
        self.cx=float(cx)
        self.cy=float(cy)
        self.cz=float(cz)
        self.thrust=float(thrust)
        self.message = message
        self.sent = True
    def update(self, fire,cx,cy,cz,thrust, message):
        updated=False
        
        if self.fire != fire:
            self.fire = fire
            updated=True
        if self.cx != cx:
            self.cx=float(cx)
            updated=True
        if self.cy != cy:
            self.cy=float(cy)
            updated=True
        if self.cz != cz:
            self.cz=float(cz)
            updated = True
        if self.thrust != thrust:
            self.thrust=float(thrust)
            updated =True
        if self.message != message:
            self.message = message
            updated = True
        if updated:
            self.sequence +=1
            self.sent= False
    def check_sent(self):
        return( self.sent)
    def set_sent(self, state):
        self.sent=Boolean(state)
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class model_list:
    def __init__(self):
        self.models = []
        self.auto_generate = True
        pass
    def get_by_name(self,filename,swapyz):
        # find the model in our list
        found=False
        for model in self.models:
            if model.name==filename:
                # we found it so we don't have to re-load it
                found=True
                return(model)
        if found==False:
            # we didn't find it so we load it and add it to the list
            new_model_3D = model3D(filename, swapyz)      # load the new model
            #new_model_3D.generate()                             # generate it
            self.models.append(new_model_3D)                    # add it to the list
            return new_model_3D

# 3D Object Class
class model3D:
    generate_on_init = True
    @classmethod
    def loadTexture(cls, imagefile):
        surf = pygame.image.load(imagefile)
        image = pygame.image.tostring(surf, 'RGBA', 1)
        ix, iy = surf.get_rect().size
        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        return texid

    @classmethod
    def loadMaterial(cls, filename):
        contents = {}
        mtl = None
        dirname = os.path.dirname(filename)

        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'newmtl':
                mtl = contents[values[1]] = {}
            elif mtl is None:
                raise ValueError("mtl file doesn't start with newmtl stmt")
            elif values[0] == 'map_Kd':
                # load the texture referred to by this declaration
                mtl[values[0]] = values[1]
                imagefile = os.path.join(dirname, mtl['map_Kd'])
                mtl['texture_Kd'] = cls.loadTexture(imagefile)
            else:
                mtl[values[0]] = list(map(float, values[1:]))
        return contents
    def set_rotation(self,rx,ry,rz):
        self.rx=float(rx)
        self.ry=float(ry)
        self.rz=float(rz)
    def set_scale(self,sx,sy,sz):
        self.sx=float(sx)
        self.sy=float(sy)
        self.sz=float(sz)
    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.gl_list = 0
        self.name=filename
        self.rx=float(0)
        self.ry=float(0)
        self.rz=float(0)
        self.sx=float(1)
        self.sy=float(1)
        self.sz=float(1)
        dirname = os.path.dirname(filename)

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = self.loadMaterial(os.path.join(dirname, values[1]))
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
        if self.generate_on_init:
            self.generate()

    def generate(self):
        print("Generating ", self.name)
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        for face in self.faces:
            vertices, normals, texture_coords, material = face

            mtl = self.mtl[material]
            if 'texture_Kd' in mtl:
                # use diffuse texmap
                glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
            else:
                # just use diffuse colour
                glColor(*mtl['Kd'])

            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                if texture_coords[i] > 0:
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        glPushMatrix()
        #glRotate(270,1,0,0)
        glRotatef(self.rx, 1.0, 0.0, 0.0)            #ship rotation
        glRotatef(self.ry, 0.0, 1.0, 0.0)            #ship rotation
        glRotatef(self.rz, 0.0, 0.0, 1.0)            #ship rotation
        glScale(self.sx,self.sy,self.sz)
        glCallList(self.gl_list)
        glPopMatrix()
    def free(self):
        glDeleteLists(self.gl_list,1)
        
class object():                 # Object in our 3D world
    def __init__(self,name,x , y, z, rx, ry , rz, sx ,sy,sz):
        self.objList = []
        self.name=name
        self.x = float(x)
        self.y=float(y)
        self.z=float(z)
        self.rx=float(rx)
        self.ry=float(ry)
        self.rz=float(rz)
        self.sx=float(sx)
        self.sy=float(sy)
        self.sz=float(sz)
        
    def __iter__(self):
        return iter(self.objList)
    def addObj(self,s):
        self.objList.append(s)
    def getShapeList(self):
        return self.objList
    def build(self):
        for s in self.objList:
            s.generate()
    def render(self, scale):
        glPushMatrix();                             #save first position
        
        glTranslatef(self.x, self.y, self.z)  #move to object's position
        glRotatef(self.rx, 1.0, 0.0, 0.0)            # rotation
        glRotatef(self.ry, 0.0, 1.0, 0.0)            # rotation
        glRotatef(self.rz, 0.0, 0.0, 1.0)            # rotation
        glScale(scale,scale,scale)
        for s in self.objList:
            s.render()
        glPopMatrix()
class camera():         # our viewpoint on the world
    def __init__(self, X, Y, Z, debug_camera):
        self.position = np.array([X,Y,Z], dtype=float)
        self.target = np.array([0,0,0], dtype=float)
        self.up = np.array([0,1,0], dtype=float)
        self.forward = np.array([0, 0, -1], dtype=float)
        self.right = np.array([1, 0, 0], dtype=float)
        self.up = np.array([0, 1, 0], dtype=float)
        
        self.rx = float(0)       # pitch around x
        self.ry = float(0)         # yaw around y
        self.rz=float(0)          # roll around z
        self.move_speed = 0.1
        self.zoom_speed = 0.1
        self.zoom=float(10)
        self.max_zoom=20
        self.orientation = Quaternion()
        self.orbit_x=0
        self.orbit_y=0
        self.debug = debug_camera
    def look(self):
        glLoadIdentity()  
        glRotatef(-self.rz,    0,  0,  1)
        glRotatef(-self.ry,    0,  1,  0)
        glRotatef(-self.rx,  1,  0,  0)
        glTranslatef(-self.position[0],- self.position[1], -self.position[2])
    
    
    def get_direction(self):
        direction= get_normalized_direction(self.rx,self.ry,self.rz)
        return direction    
    def set_zoom(self,zoom):
        self.zoom=float(zoom)
    def set_move_speed(self, move_speed):
        self.move_speed=move_speed
    def set_zoom_speed(self,zoom_speed):
        self.zoom_speed=zoom_speed
    def zoom_in(self,zoom):
        
        self.zoom -= zoom * self.zoom_speed
        if self.zoom < 0.1: self.zoom = 0.1
        
        # self.move_forward(zoom)
        if self.debug: print("Camera Zoom set to:", self.zoom)
    def zoom_out(self, zoom):
        self.zoom += zoom  * self.zoom_speed
        if self.zoom > self.max_zoom: self.zoom=self.max_zoom
        # self.move_backward(zoom)
        if self.debug: print("Camera Zoom set to:", self.zoom)
    def set_rotation(self,rx,ry,rz):
        self.rx = float(rx)
        self.ry = float(ry)
        self.rz= float(rz)
    def add_rotation(self,rx,ry,rz):
        self.rx += rx
        self.ry += ry
        self.rz+=rz
        
        #self.rx = newMod(self.rx + x, 360) 
        #self.ry = newMod(self.ry + y, 360) 
        #self.rz = newMod(self.rz + z, 360)
        
    def click(self):            # point the camera at the stored target
        direction = self.target - self.position
        
        # Calculate rotation angles
        rx , ry  = direction_to_euler(direction)
        # Calculate roll angle using quaternion
        quaternion = Quaternion(1,direction[0],direction[1],direction[2])
       
        rotation_matrix = quaternion.rotation_matrix
        rz = math.degrees(math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0]))
        
        # Update camera attributes
        self.rx = rx
        self.ry = ry
        #self.rz = rz
    
    def point_at(self, target_x, target_y, target_z):
        self.target[0] = float(target_x)
        self.target[1] = float( target_y) 
        self.target[2] = float( target_z)
        self.click()
    


    def move_backward(self, distance):
        """Move the camera forward along its orientation."""
        distance = distance * self.move_speed
        direction = self.get_direction()
        self.position += distance*direction
        
        

    def move_forward(self, distance):
        """Move the camera backward along its orientation."""
        distance = distance * self.move_speed
        direction = self.get_direction()
        self.position -= distance*direction
        
    def move_out(self):
        self.position[2] -= self.move_speed
    def move_in(self):
        self.position[2] += self.move_speed
    def move_left(self):
        self.position[0] -= self.move_speed
    def move_right(self):
        self.position[0] += self.move_speed
    def move_relative(self,X,Y,Z):
        self.position += [X,Y,Z]
        
    def set_location(self,X,Y,Z):
        self.position = [X,Y,Z]
    def orbit_relative1(self, rx, ry):
        #self.orbit_x = newMod(float(rx)+self.orbit_x,360)
        #self.orbit_y = newMod(float(ry)+self.orbit_y,360)
        self.orbit_x += float(rx)
        self.orbit_y += float(ry)
        
        z=self.zoom
        # Calculate the new position relative to the target
        dx = z * math.cos(math.radians(self.orbit_x)) * math.sin(math.radians(self.orbit_y))
        dy = z * math.sin(math.radians(self.orbit_x))
        dz = z * math.cos(math.radians(self.orbit_x)) * math.cos(math.radians(self.orbit_y))
        
        # Update the camera position
        self.position = self.target + np.array([dx, dy, dz])
       
        self.click()



    def orbit_relative(self, rx, ry,rz=0):
        """Set the camera to orbit around a target with relative movement."""
        self.add_rotation(rx, ry, rz)
        direction = self.target - self.position
        direction /= np.linalg.norm(direction)
        direction *= self.zoom
             
        
        # Apply rotation to the camera's position relative to the target
        dx, dy, dz = self.rotate_point(direction[0],direction[1],direction[2] , rx, ry, rz)

        # Update the camera's position relative to the target
        self.position[0] = self.target[0] + dx
        self.position[1] = self.target[1] + dy
        self.position[2] = self.target[2] + dz

        # Update the camera's orientation to look at the target
        self.click()

    def rotate_point(self, x, y, z, rx, ry, rz):
        """Rotate a point (x, y, z) around the origin."""
        # Convert rotation angles to radians
        rx = math.radians(rx)
        ry = math.radians(ry)
        rz = math.radians(rz)

        # Create quaternions representing the rotation
        qx = Quaternion(axis=[1, 0, 0], angle=rx)
        qy = Quaternion(axis=[0, 1, 0], angle=ry)
        qz = Quaternion(axis=[0, 0, 1], angle=rz)

        # Combine the quaternions to represent the overall rotation
        q = qx * qy * qz

        # Convert point to quaternion representation
        p = Quaternion(0, x, y, z)

        # Rotate the point using quaternion multiplication
        rotated_point = q.rotate(p)

        return rotated_point.vector


 

class armory():
    def __init__(self):
        self.shape_list=[]
        pass

class shiplist():
    def __init__(self,  AUTO_BUILD, INCLUDE_GL): 
        self.ship_list = []
        self.count= 0
        
        self.auto_build=AUTO_BUILD
        self.include_gl=INCLUDE_GL
    def load_from_db(self):
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Ships')
        data = cursor.fetchall()
        self.ship_list.clear()
        countships=0
        for each_ship in data:
            idShips, ID, Name, Model , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = each_ship
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
            expiry=float(-1)
            if self.include_gl:
                newShip = ship_GL(ID, Name, Model , x, y , z, rx, ry , rz, thrust , drag , amx, amy, amz, vx, vy, vz, cx, cy, cz , expiry)
            else:
                newShip = ship(ID, Name ,Model, x, y , z, rx, ry , rz, thrust , drag , amx, amy, amz, vx, vy, vz, cx, cy, cz, expiry)
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
    def write_to_db(self):
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for ship in self.ship_list:
            # Extract ship attributes
            id_ship = ship.Id
            name = ship.Name
            x = str(ship.x)
            y = str(ship.y)
            z = str(ship.z)
            rx = str(ship.rx)
            ry = str(ship.ry)
            rz = str(ship.rz)
            thrust = str(ship.Thrust)
            drag = str(ship.Drag)
            amx = str(ship.AMx)
            amy = str(ship.AMy)
            amz = str(ship.AMz)
            vx = str(ship.Vx)
            vy = str(ship.Vy)
            vz = str(ship.Vz)
            cx = str(ship.Cx)
            cy = str(ship.Cy)
            cz = str(ship.Cz)

            # Update the corresponding record in the database
            cursor.execute(
                '''
                UPDATE Ships 
                SET X = %s, Y = %s, Z = %s, Rx = %s, Ry = %s, Rz = %s, 
                Thrust = %s, Drag = %s, AMx = %s, AMy = %s, AMz = %s, 
                Vx = %s, Vy = %s, Vz = %s, Cx = %s, Cy = %s, Cz = %s
                WHERE ID = %s
                ''',
                (x, y, z, rx, ry, rz, thrust, drag, amx, amy, amz, vx, vy, vz, cx, cy, cz, id_ship)
            )

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
    def buildships(self):
        for obj in self.ship_list:
            obj.build()
    def render(self, shipscale):
        for obj in self.ship_list:
            obj.render(shipscale)
    def update_from_udp(self,receiver_socket):
        data, addr = receiver_socket.recvfrom(1024)
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
    @classmethod
    def new_from_json(cls, json_data):
        data_dict = json.loads(json_data)
        return cls(**data_dict)    
    def add_ship(self,ship):
        self.ship_list.append(ship)
        self.count += 1
    def remove_ship(self,this_ship):
        self.ship_list.remove(this_ship)
        self.count -=1
        
class ship():
    def __init__(self, Id, Name ,model_name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz , expiry ):
        self.objects =[]
        self.Id=float(Id) 
        self.Name=Name 
        self.x=float(X)
        self.y=float(Y) 
        self.z=float(Z)
        self.rx=float(Rx )
        self.ry=float(Ry )
        self.rz=float(Rz)
        self.Thrust = float(Thrust )
        self.Drag = float(Drag )
        self.AMx = float(AMx)
        self.AMy = float(AMy)
        self.AMz = float(AMz)
        self.Vx = float(Vx)
        self.Vy = float(Vy )
        self.Vz = float(Vz)
        self.Cx= float(Cx )
        self.Cy = float(Cy)
        self.Cz = float(Cz )
        self.expiry= expiry
        self.created = time.time()
        self.base_model=model_name
    def add_model(self,model):
        self.objects.append(model)
    def set_expiry(self, value):
        self.expiry=value
    def reset(self):
        self.x=0
        self.y=0
        self.z=0
        self.rx=0
        self.ry=0
        self.rz=0
        self.Thrust = 0
        self.Drag = 0
        self.AMx = 0
        self.AMy = 0
        self.AMz =0
        self.Vx = 0
        self.Vy = 0
        self.Vz = 0
        self.Cx=0
        self.Cy = 0
        self.Cz = 0
    def update_location(self,X,Y,Z):
        self.x=X
        self.y=Y
        self.z=Z
    def update(self, Name , model_name, X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz , expiry):
        self.expiry=expiry
        self.Name=Name 
        self.x=float(X)
        self.y=float(Y) 
        self.z=float(Z)
        self.rx=float(Rx) 
        self.ry=float(Ry) 
        self.rz=float(Rz)
        self.Thrust = float(Thrust) 
        self.Drag = float(Drag )
        self.AMx = float(AMx)
        self.AMy = float(AMy)
        self.AMz = float(AMz)
        self.Vx = float(Vx)
        self.Vy = float(Vy )
        self.Vz = float(Vz)
        self.Cx= float(Cx )
        self.Cy = float(Cy)
        self.Cz = float(Cz )
        self.base_model=model_name
    def set_controls(self,Thrust,Cx, Cy, Cz):
        self.Thrust = float(Thrust) 
        self.Cx= float(Cx )
        self.Cy = float(Cy)
        self.Cz = float(Cz )
    def update_rotation(self,Rx,Ry,Rz):
        self.rx=float(Rx) 
        self.ry=float(Ry) 
        self.rz=float(Rz)
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
    
    def fromJson(self, json_object):
        Id, Name ,base_model, X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = json_object
        self.update(Id, Name, base_model , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz)
    @classmethod
    def new_from_json(cls, json_data):
        data_dict = json.loads(json_data)
        return cls(**data_dict)    
            
class ship_GL(ship):                    # extension of ship classs to include graphics functions
    def __init__(self, Id, Name ,base_model, X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz, expiry):
        super().__init__(Id, Name , base_model, X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz , expiry)
        
        self.gllist=glGenLists(1)        #generated by build
    def render(self,scale):
        #draw the ship
        glPushMatrix();                             #save first position
        
        glTranslatef(self.x, self.y, self.z)  #move to ship's position
        glRotatef(self.rx, 1.0, 0.0, 0.0)            #ship rotation
        glRotatef(self.ry, 0.0, 1.0, 0.0)            #ship rotation
        glRotatef(self.rz, 0.0, 0.0, 1.0)            #ship rotation
        glScale(scale,scale,scale)
        for obj in self.objects:
            obj.render()
        glPopMatrix()
    def build(self):
        
        for obj in self.objects:
            obj.generate()
    def addShape(self,newOBJ):
        self.objects.append(newOBJ)

#Size Class
class size():
    def __init__(self,height,width,depth):
        self.height=height
        self.width=width
        self.depth=depth
        
class color():
    def __init__(self, rin, gin, bin):
        self.r=rin
        self.g=gin
        self.b=bin
    def set(self,rin,gin,bin):
        self.r=rin
        self.g=gin
        self.b=bin

class location():
    def __init__(self, x,y,z):
        self.x= float(x)
        self.y=float(y) 
        self.z=float(z)



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
class texture:
    def __init__(self, filepath):
        surface = pygame.image.load(filepath)
        self.data = pygame.image.tostring(surface, "RGB", 1)

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, surface.get_width(), surface.get_height(), 0, GL_RGB, GL_UNSIGNED_BYTE, self.data)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        self.name = filepath
        
        
class texture_list:
    def __init__(self, DEBUG=False):
        self.textures = []
        self.id = []
        self.auto_generate = True
        self.debug=DEBUG
    def get_by_name(self,filename):
        found=False
        # see if we've already loaded it
        for tex in self.textures:
            if tex.name== filename:
                return tex
                found=True
                if self.debug: print(" Texture found in list:", tex.name)
                break
        if found==False:
            newTexture=texture(filename)
            self.add_texture(newTexture)
            if self.debug: print(" Texture loaded:", newTexture.name)
            return newTexture
    def add_texture(self,tex):
        self.textures.append(tex)