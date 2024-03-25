###########################################################
##
##  DEAMON PROCESSOR FOR OCTAVIA
##
##  Stuart Oldfield 2024
##

## todo:
## ship movement
## munition movement
## terrain collision

## set some bounds for ship movement
WorldWidth = float(10)
WorldHeight= float(10)
WorldDepth = float(10)

import math
import time
from pyquaternion import Quaternion  # Install using: pip install numpy pyquaternion

import mysql.connector

# Replace 'your_username', 'your_password', 'your_database', and '192.168.0.166' with your actual MySQL credentials and server IP
db_config = {
    'user': 'stu',
    'password': 'v400oom',
    'host': '192.168.0.166',
    'database': 'worldDB',
}


def ships():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Ships')
    data = cursor.fetchall()
    for ship in data:
        idShips, ID, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = ship
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
        thrust=float(Thrust)
        drag=float(Drag)
        vx=float(Vx)
        vy=float(Vy)
        vz=float(Vz)
        
        print("Found Ship", Name )
        # basic thrust along ship axis for now
        speed = Thrust
        print("Speed:", speed, " Cx:" , Cx ," Cy:", Cy ," Cz:",Cz)
        # Vx = pitch
        # Vy = yaw
        # Vz = roll
        # 
        # calculate control surfaces - add control to rotation
        rx=rx+cx
        ry=ry+cy
        rz=rz+cz

        # apply to angular momentum

        
        # matrix below takes yaw - pitch - roll
        quaternion =    Quaternion(axis=[0, 0, 1], degrees=ry) * \
                        Quaternion(axis=[1, 0, 0], degrees=rx) * \
                        Quaternion(axis=[0, 1, 0], degrees=rz)

        # Calculate the new position based on the ship's orientation
        displacement = quaternion.rotate([0, speed, 0])
        x = x + displacement[0]
        y = y + displacement[1]
        z = z + displacement[2]

        # Update the ship's position
       

        

        # calculate thrust vector
        
        # apply to velocities
        
        # calculate new ship's position

        # test for collision with edge of the world
        x = min( WorldWidth, x)
        x = max( -WorldWidth, x)
        y = min(WorldHeight, y)
        y = max(-WorldHeight, y)
        z = min(WorldDepth,z)
        z = max(-WorldDepth,z)
        
        # convert back to strings
        X = str(x)
        Y = str(y)
        Z = str(z)
        Rx = str(rx)
        Ry = str(ry)
        Rz = str(rz)
        Cx = str(cx)
        Cy = str(cy)
        Cz = str(cz)
        Thrust = str(thrust)
        Drag = str(drag)
        Vx = str(vx)
        Vy = str(vy)
        Vz = str(vz)

        # write to database
        # Query to update the ship_status
        update_query = "UPDATE Ships SET"
        update_query = update_query + " ID = %s, Name = %s , X = %s , Y = %s  , Z = %s ,"
        update_query = update_query + " Rx = %s , Ry = %s  , Rz = %s , Thrust = %s  ,"
        update_query = update_query + " Drag = %s  , AMx = %s , AMy = %s , AMz = %s , Vx = %s , Vy = %s , Vz = %s ,"
        update_query = update_query + " Cx = %s , Cy = %s , Cz = %s "
        update_query = update_query + " WHERE idShips = %s"
    
        # Execute the update query
        cursor.execute(update_query, (ID, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz ,idShips))

        # Commit the changes
        conn.commit()

    # Close the cursor and connection
    cursor.close()

    conn.close()


def munitions():
    # move them
    # check collisions
    # check expiry
    a=0

def main():
    print("We're running")
    
    #setup timing for triggering updates
    ship_update_timer = 2
    munitions_update_time = 1
    now=time.time()
    ship_trigger=now+ship_update_timer
    munitions_trigger=now+munitions_update_time
    
    # MAIN LOOP
    while True:
        now=time.time()
        if now>ship_trigger:
            ships()                 # move ships
            
            ship_trigger += ship_update_timer
        if now > munitions_trigger:
            munitions()             # move munitions
            munitions_trigger += munitions_update_time
        time.sleep(0.1)
    
     
# Actually launch the code
if __name__ == '__main__':
    main()
##################################################################
#  END OF CODE
##################################################################

