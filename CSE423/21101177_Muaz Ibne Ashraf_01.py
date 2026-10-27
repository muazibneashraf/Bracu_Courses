#Task 1

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

display_background = (0.0, 0.0, 0.0, 0.0)
rain_drop_angle = 0.0
raindrops_coordinates = []


def raindrop_design(x1, y1):
    glColor3f(1.0, 0.0, 0.0)
    glPointSize(3)
    glBegin(GL_POINTS)
    glVertex2f(x1, y1)
    glEnd()


def all_raindrops():
    global rain_drop_angle
    for i in range(len(raindrops_coordinates)):
        x, y = raindrops_coordinates[i]
        x += rain_drop_angle
        y -= 5

        if y < 0 or (120 < x < 380 and 100 < y < 300):
            x = random.uniform(0, 500)
            y = random.uniform(400, 600)

        raindrops_coordinates[i] = (x, y)


def build_house():
    roof_left = (100, 300)
    roof_right = (400, 300)
    roof_peak = (250, 400)

    wall_left = 120
    wall_right = 380
    wall_bottom = 100
    wall_top = 300

    door_left = 140
    door_right = 200
    door_bottom = 100
    door_top = 200

    win_left = 300
    win_right = 350
    win_bottom = 200
    win_top = 250

    # Walls
    glColor3f(0.8, 0.8, 0.85)
    glBegin(GL_QUADS)
    glVertex2f(wall_left, wall_bottom)
    glVertex2f(wall_right, wall_bottom)
    glVertex2f(wall_right, wall_top)
    glVertex2f(wall_left, wall_top)
    glEnd()

    # Roof
    glColor3f(0.6, 0.2, 0.2)
    glBegin(GL_TRIANGLES)
    glVertex2f(*roof_left)
    glVertex2f(*roof_right)
    glVertex2f(*roof_peak)
    glEnd()

    # Door
    glColor3f(0.55, 0.35, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(door_left, door_bottom)
    glVertex2f(door_right, door_bottom)
    glVertex2f(door_right, door_top)
    glVertex2f(door_left, door_top)
    glEnd()

    # Window
    glColor3f(0.7, 0.9, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(win_left, win_bottom)
    glVertex2f(win_right, win_bottom)
    glVertex2f(win_right, win_top)
    glVertex2f(win_left, win_top)
    glEnd()

    # Outlines
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)  # wall outline
    glVertex2f(wall_left, wall_bottom)
    glVertex2f(wall_right, wall_bottom)
    glVertex2f(wall_right, wall_top)
    glVertex2f(wall_left, wall_top)
    glEnd()

    # Roof outline
    glBegin(GL_LINE_LOOP)
    glVertex2f(*roof_left)
    glVertex2f(*roof_right)
    glVertex2f(*roof_peak)
    glEnd()

    # Door outline
    glBegin(GL_LINE_LOOP)
    glVertex2f(door_left, door_bottom)
    glVertex2f(door_right, door_bottom)
    glVertex2f(door_right, door_top)
    glVertex2f(door_left, door_top)
    glEnd()

    # Window frame
    WINDOW_W, WINDOW_H = 500, 500
    glBegin(GL_LINE_LOOP)
    glVertex2f(win_left, win_bottom)
    glVertex2f(win_right, win_bottom)
    glVertex2f(win_right, win_top)
    glVertex2f(win_left, win_top)
    glEnd()

    # Window cross
    glBegin(GL_LINES)
    glVertex2f((win_left + win_right) / 2, win_bottom)
    glVertex2f((win_left + win_right) / 2, win_top)
    glVertex2f(win_left, (win_bottom + win_top) / 2)
    glVertex2f(win_right, (win_bottom + win_top) / 2)
    glEnd()

    # Door knob
    glPointSize(5)
    glBegin(GL_POINTS)
    glVertex2f(door_right - 10, door_bottom + 20)
    glEnd()

    # Ground line
    glLineWidth(3)
    glBegin(GL_LINES)
    glVertex2f(0, wall_bottom)
    glVertex2f(WINDOW_W, wall_bottom)
    glEnd()


def draw_raindrops(color_cycle):
    if not color_cycle:
        glColor3f(0.0, 0.4, 1.0)

    if not use_line_drops:
        glPointSize(3)
        glBegin(GL_POINTS)
        for x, y in raindrops:
            if color_cycle:
                t = (y % WINDOW_H) / WINDOW_H
                glColor3f(0.2 + 0.8 * t, 0.3, 1.0 - t * 0.7)
            glVertex2f(x, y)
        glEnd()
    else:
        glLineWidth(1)
        glBegin(GL_LINES)
        for x, y in raindrops:
            if color_cycle:
                t = (y % WINDOW_H) / WINDOW_H
                glColor3f(0.2 + 0.8 * t, 0.3, 1.0 - t * 0.7)
            glVertex2f(x, y)
            glVertex2f(x + wind_strength * 0.4, y - 6)  # short streak
        glEnd()




def specialKeyListener(key, x, y):
    global rain_drop_angle
    if key == GLUT_KEY_RIGHT:
        rain_drop_angle += 1
        print("Slightly bending the rainfall to the right")
    if key == GLUT_KEY_LEFT:
        rain_drop_angle -= 1
        print("Slightly bending the rainfall to the left")

    glutPostRedisplay()


def keyboardListener(key, x, y):
    global display_background
    if key == b"b":
        display_background = (0.0, 0.0, 0.0, 0.0)
    if key == b"w":
        display_background = (1.0, 1.0, 1.0, 0.0)
    glutPostRedisplay()


def animate():
    all_raindrops()
    glutPostRedisplay()


def continious():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def display():
    glClearColor(*display_background)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    continious()
    build_house()
    for drops in raindrops_coordinates:
        raindrop_design(drops[0], drops[1])
    glutSwapBuffers()


glutInit()
glutInitWindowSize(500, 500)
glutInitWindowPosition(0, 0)
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)

wind = glutCreateWindow(b"Lab Assignment 1 Task 1: House with Rain Drop")

glutDisplayFunc(display)
glutIdleFunc(animate)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)

for cordinates in range(100):
    x2 = random.uniform(100, 400)
    y2 = random.uniform(200, 500)
    raindrops_coordinates.append((x2, y2))

glutMainLoop()
#==================================================================================================

#Task 2

'''
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

random_points = []
speed_constant = 0.1
point_blink = False
freeze_point = False

WINDOW_W, WINDOW_H = 500, 500
BLINK_INTERVAL = 0.5
last_blink_time = time.time()
blink_visible = True

def draw_points(x, y, color):
    glPointSize(8)
    glBegin(GL_POINTS)
    glColor3f(color[0], color[1], color[2])
    glVertex2f(x, y)
    glEnd()

def point_with_speed():
    global speed_constant

    for i in random_points:
        if not freeze_point:
            i['x'] += (speed_constant * i['dx'])
            i['y'] += (speed_constant * i['dy'])
            # Bounce on box walls
            if i['x'] < 0 or i['x'] > WINDOW_W:
                i['dx'] *= -1
                i['x'] = max(min(i['x'], WINDOW_W), 0)
            if i['y'] < 0 or i['y'] > WINDOW_H:
                i['dy'] *= -1
                i['y'] = max(min(i['y'], WINDOW_H), 0)

def mouseListener(button, state, x, y):
    global point_blink

    if not freeze_point:
        if (button == GLUT_RIGHT_BUTTON) and (state == GLUT_DOWN):
            y_gl = WINDOW_H - y
            color = [random.random(), random.random(), random.random()]
            dx, dy = random.choice([(-1, -1), (-1, 1), (1, -1), (1, 1)])
            random_points.append({'x': float(x), 'y': float(y_gl), 'color': color, 'dx': dx, 'dy': dy})
            print("New point at ({}, {})".format(x, y_gl))

        if (button == GLUT_LEFT_BUTTON) and (state == GLUT_DOWN):
            point_blink = not point_blink
            print("Blinking:", point_blink)

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global speed_constant

    if not freeze_point:
        if key == GLUT_KEY_UP:
            speed_constant *= 1.5
            print("Increased Speed By", speed_constant)
        if key == GLUT_KEY_DOWN:
            speed_constant /= 1.5
            print("Decreased Speed By", speed_constant)

    glutPostRedisplay()

def keyboardListener(key, x, y):
    global freeze_point

    if key == b' ':
        freeze_point = not freeze_point
        print("Freeze!!!" if freeze_point else "Unfreeze Points")
    glutPostRedisplay()

def animate():
    global last_blink_time, blink_visible

    if not freeze_point:
        point_with_speed()
        if point_blink:
            now = time.time()
            if now - last_blink_time > BLINK_INTERVAL:
                blink_visible = not blink_visible
                last_blink_time = now
        else:
            blink_visible = True

    glutPostRedisplay()

def continious():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def display():
    glClearColor(0, 0, 0, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    continious()

    for point in random_points:
        x, y = point['x'], point['y']
        color = point['color'] if blink_visible else [0.0, 0.0, 0.0]
        draw_points(x, y, color)

    glutSwapBuffers()

glutInit()
glutInitWindowSize(500, 500)
glutInitWindowPosition(0, 0)
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)

wind = glutCreateWindow(b"Lab Assignment 1 Task 2: Building the Amazing Box")
glutDisplayFunc(display)
glutMouseFunc(mouseListener)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutIdleFunc(animate)
glutMainLoop()
'''