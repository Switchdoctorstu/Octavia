###########################################################
##
##  SHIP CONTROLLER FOR OCTAVIA
##
##  Stuart Oldfield 2024
##
##
## todo:
## ship movement
## We have control over:
##      thrust 
##      Cx
##      Cy
##      Cz
## munition movement
## terrain collision
########################################################################################################

import pygame
import sys

import mysql.connector

# Replace 'your_username', 'your_password', 'your_database', and '192.168.0.166' with your actual MySQL credentials and server IP
db_config = {
    'user': 'stu',
    'password': 'v400oom',
    'host': '192.168.0.166',
    'database': 'worldDB',
}



class ship( ):
    def __init__(self, Id, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz ):
        self.Id=Id 
        self.Name=Name 
        self.X=X
        self.Y=Y 
        self.Z=Z
        self.Rx=RX 
        self.Ry=Ry 
        self.Rz=Rz
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



def set_ship():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Ships')
    data = cursor.fetchall()
    for ship in data:
        idShips, ID , Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz = ship
        print("Found Ship", Name )
        # basic thrust along ship axis for now
        speed = Thrust
        # Vx = pitch
        # Vy = yaw
        # Vz = roll
        
        # calculate control surfaces
        # assume they're thrusters for now

        # apply to angular momentum

        # get new ship's rotation

        # calculate thrust vector
        
        # apply to velocities
        
        # calculate new ship's position

        # test for collision

        # write to database
        # Query to update the ship_status
        update_query = "UPDATE Ships SET"
        update_query = update_query + " ID = %s, Name = %s , X = %s , Y = %s  , Z = %s ,"
        update_query = update_query + " Rx = %s , Ry = %s  , Rz = %s , Thrust = %s  ,"
        update_query = update_query + " Drag = %s  , AMx = %s , AMy = %s , AMz = %s , Vx = %s , Vy = %s , Vz = %s ,"
        update_query = update_query + " Cx = %s, Cy =%s, Cz=%s "
        update_query = update_query + " WHERE idShips = %s"
    
        # Execute the update query
        # cursor.execute(update_query, (ID, Name , X, Y , Z, Rx, Ry , Rz, Thrust , Drag , AMx, AMy, AMz, Vx, Vy, Vz, Cx, Cy, Cz ,idShips))

        # Commit the changes
        # conn.commit()

    # Close the cursor and connection
    cursor.close()

    conn.close()

def main():

    # work out which ship we're in

    # Initialize Pygame
    pygame.init()

    # Constants
    WIDTH, HEIGHT = 800, 600
    JOYSTICK_RADIUS = 50

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    # Initialize Pygame window
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Joystick and Thrust Control")

    # Joystick position
    joystick_x, joystick_y = WIDTH // 2, HEIGHT // 2

    # Thrust control
    thrust_on = False
    thrust = 0

    # Main game loop
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    thrust_on = not thrust_on
                if event.key == pygame.K_n:
                    thrust += 5
                if event.key == pygame.K_m:
                    thrust -= 5
        # Ensure thrust is within limits
        thrust = max(0, min(thrust, 150))
        
        # Handle key events
        keys = pygame.key.get_pressed()
        joystick_speed = 5
        thrust_speed = 1

        # Joystick control
        if keys[pygame.K_LEFT]:
            joystick_x -= joystick_speed
        if keys[pygame.K_RIGHT]:
            joystick_x += joystick_speed
        if keys[pygame.K_UP]:
            joystick_y -= joystick_speed
        if keys[pygame.K_DOWN]:
            joystick_y += joystick_speed

        

        # Update screen
        screen.fill(BLACK)

        # Draw joystick
        pygame.draw.circle(screen, WHITE, (int(joystick_x), int(joystick_y)), JOYSTICK_RADIUS)

        # Draw thrust control
        pygame.draw.rect(screen, WHITE, (WIDTH - 50, HEIGHT - 150, 30, 150))
        pygame.draw.rect(screen, WHITE, (WIDTH - 50, HEIGHT - 150 + 150 - thrust, 30, thrust))

         # Display thrust status
        thrust_font = pygame.font.Font(None, 36)
        thrust_text = thrust_font.render(f"Thrust {'ON' if thrust_on else 'OFF'}", True, WHITE)
        screen.blit(thrust_text, (10, 10))


        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

main()