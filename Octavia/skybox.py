import sys
import math
import Octavia_Classes
import xml.etree.ElementTree as ET
#import numpy as np
import json
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# Windows forms tools
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
#from tkinter import font

# Classes 
# Vertice Class
class Vertice():
    def __init__(self, x,y,z):
        self.x= x
        self.y=y 
        self.z=z
    
    def getX(self):
        return self.x

    def setX(self,x):
      self.x= x

class Scale():
    def __init__(self,sx,sy,sz):
        self.sx=sx
        self.sy=sy
        self.sz=sz
#Size Class
class Size():
    def __init__(self,height,width,depth):
        self.height=height
        self.width=width
        self.depth=depth

#Color Class
class color():
    def __init__(self, rin, gin, bin):
        self.r=rin
        self.g=gin
        self.b=bin
    def setColor(self,rin,gin,bin):
        self.r=rin
        self.g=gin
        self.b=bin

# skybox
class skybox():   
    def __init__(self, filename, tex_list):
        self.gllist=glGenLists(1)
       
        self.size = Size(20,20,20)
        self.scale = Scale(1,1,1)
        self.position = Vertice(0,0,0)
        # get or build the texture
        self.tex=tex_list.get_by_name(filename)
        
        h=self.size.height
        w=self.size.width
        d=self.size.depth
        
        glNewList(self.gllist,GL_COMPILE)  
        glBindTexture(GL_TEXTURE_2D,self.tex.texture_id)
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        
        glBegin(GL_QUADS)

        
        #bottom
        glTexCoord(0,0)
        glVertex3f(0,0,d)
        glTexCoord(0,1)
        glVertex3f(0,w,d)
        glTexCoord(1,1)
        glVertex3f(h,w,d)
        glTexCoord(1,0)
        glVertex3f(h,0,d)       
        #front
        glVertex3f(h,0,-d)
        glVertex3f(h,0,d)
        glVertex3f(h,w,d)
        glVertex3f(h,w,-d)
        #back
        glVertex3f(0,0,-d)
        glVertex3f(0,0,d)
        glVertex3f(0,w,d)
        glVertex3f(0,w,-d) 
        #left
        glVertex3f(0,w,-d)
        glVertex3f(0,w,d)
        glVertex3f(h,w,d)
        glVertex3f(h,w,-d)
        #right
        glVertex3f(h,0,d)
        glVertex3f(0,0,d)
        glVertex3f(0,0,-d)
        glVertex3f(h,0,-d)
        #top  
        glTexCoord2fv((1,0))
        glVertex3f(0,0,-d)
        glTexCoord2fv((1,1))
        glVertex3f(0,w,-d)
        glTexCoord2fv((0,1))
        glVertex3f(h,w,-d)
        glTexCoord2fv((0,0))
        glVertex3f(h,0,-d)
        
        glEnd()
        glEndList()

    def render(self):
        glPushMatrix()
        
        glTranslatef(self.position.x,self.position.y,self.position.z)
        
        glCallList(self.gllist)
        glPopMatrix()

