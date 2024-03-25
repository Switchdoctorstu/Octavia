
# bits of maths used by my code
# Stuart Oldfield 2024


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

# length of a vector
def vector_length(v):
    return math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])

class Vector():
    def __init__(self, x , y, z):
        self.np = np.array[x,y,z]
    def x(self):
        return self.np[0]
    def y(self):
        return self.np[1]
    def z(self):
        return self.np[2]

def dot(v0, v1):            # dot product
    return v0[0]*v1[0]+v0[1]*v1[1]+v0[2]*v1[2]

def cross(v0, v1):          # cross product
    return [
        v0[1]*v1[2]-v1[1]*v0[2],
        v0[2]*v1[0]-v1[2]*v0[0],
        v0[0]*v1[1]-v1[0]*v0[1]]


def normalize(v):
    l = vector_length(v)
    return [v[0]/l, v[1]/l, v[2]/l]

def m3dLookAt(eye, target, up):
    mz = normalize( (eye[0]-target[0], eye[1]-target[1], eye[2]-target[2]) ) # inverse line of sight
    mx = normalize( cross( up, mz ) )
    my = normalize( cross( mz, mx ) )
    tx =  dot( mx, eye )
    ty =  dot( my, eye )
    tz = -dot( mz, eye )   
    return np.array([mx[0], my[0], mz[0], 0, mx[1], my[1], mz[1], 0, mx[2], my[2], mz[2], 0, tx, ty, tz, 1])


def direction_to_euler(direction):
    # Ensure the direction vector is normalized
    magnitude = np.linalg.norm(direction)
    direction /= magnitude

    # Calculate pitch (rotation around x-axis)
    pitch = np.arcsin(-direction[1])

    # Calculate yaw (rotation around y-axis)
    yaw = np.arctan2(-direction[0], -direction[2])

    # Roll is assumed to be zero, as we only have a direction vector

    # Convert angles from radians to degrees
    pitch_degrees = np.degrees(pitch)
    yaw_degrees = np.degrees(yaw)

    return  pitch_degrees ,  yaw_degrees 
def get_normalized_direction(rx, ry, rz):
    """
    Create a normalized direction vector from Euler angles.
    """
    rotation_matrix = euler_to_rotation_matrix(rx, ry, rz)
    
    # Extract the forward direction vector
    direction = rotation_matrix[:, 2]  # Extract the third column (forward direction)
    
    # Normalize the direction vector
    direction /= np.linalg.norm(direction)
    
    return direction
def euler_to_rotation_matrix(rx, ry, rz):
    """
    Convert Euler angles to a rotation matrix.
    """
    rx = math.radians(rx)
    ry = math.radians(ry)
    rz = math.radians(rz)
    
    # Rotation matrices for each axis
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(rx), -np.sin(rx)],
                   [0, np.sin(rx), np.cos(rx)]])
    
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                   [0, 1, 0],
                   [-np.sin(ry), 0, np.cos(ry)]])
    
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                   [np.sin(rz), np.cos(rz), 0],
                   [0, 0, 1]])
    
    # Combine rotation matrices
    rotation_matrix = Rx.dot(Ry.dot(Rz))
    return rotation_matrix

# some common functions
def newMod(a, b):
    return (a % b + b) % b

def euler_to_quaternion(rx, ry, rz):
    # Convert Euler angles to radians
    rx = np.radians(rx)
    ry = np.radians(ry)
    rz = np.radians(rz)

    # Compute half angles
    hr = rz * 0.5
    hp = ry * 0.5
    hy = rx * 0.5

    # Compute sin and cos values for half angles
    sr = np.sin(hr)
    cr = np.cos(hr)
    sp = np.sin(hp)
    cp = np.cos(hp)
    sy = np.sin(hy)
    cy = np.cos(hy)

    # Compute quaternion components
    qw = cr * cp * cy + sr * sp * sy
    qx = cr * sp * cy + sr * cp * sy
    qy = cr * cp * sy - sr * sp * cy
    qz = sr * cp * cy - cr * sp * sy

    return Quaternion(qw, qx, qy, qz)

def quaternion_to_euler(q):
    # Extract quaternion components
    qw, qx, qy, qz = q.w, q.x, q.y, q.z

    # Roll (x-axis rotation)
    rx = np.arctan2(2*(qw*qx + qy*qz), 1 - 2*(qx**2 + qy**2))
    # Pitch (y-axis rotation)
    ry = np.arcsin(2*(qw*qy - qz*qx))
    # Yaw (z-axis rotation)
    rz = np.arctan2(2*(qw*qz + qx*qy), 1 - 2*(qy**2 + qz**2))

    # Convert angles from radians to degrees
    rx = np.degrees(rx)
    ry = np.degrees(ry)
    rz = np.degrees(rz)

    return rx, ry, rz


