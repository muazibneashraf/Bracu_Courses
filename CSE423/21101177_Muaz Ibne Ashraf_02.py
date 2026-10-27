from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

win_w, win_h = 500, 700

gem_x, gem_y = random.uniform(50, 450), 650
bowl_x, bowl_y = 250, 20
btn_play_x, btn_play_y = 250, 675
btn_restart_x, btn_restart_y = 0, 675
btn_exit_x, btn_exit_y = 450, 700
fall_speed = 0.06
score = 0
gem_rgb = [random.uniform(0.7, 1.0), random.uniform(0.3, 1.0), random.uniform(0.9, 1.0)]
bowl_rgb = [1, 1, 1]
playing = True
game_over = False

def ogl_coords(x, y):
    return x, win_h - y

def zone_original(x, y, z):
    if z == 0: return x, y
    if z == 1: return y, x
    if z == 2: return -y, x
    if z == 3: return -x, y
    if z == 4: return -x, -y
    if z == 5: return -y, -x
    if z == 6: return y, -x
    if z == 7: return x, -y

def zone_to0(x, y, z):
    if z == 0: return x, y
    if z == 1: return y, x
    if z == 2: return y, -x
    if z == 3: return -x, y
    if z == 4: return -x, -y
    if z == 5: return -y, -x
    if z == 6: return -y, x
    if z == 7: return x, -y

def draw_line(x1, y1, x2, y2, rgb):
    dx = x2 - x1
    dy = y2 - y1
    zone = 0
    if abs(dx) > abs(dy):
        if dx >= 0 and dy >= 0: zone = 0
        elif dx < 0 and dy >= 0: zone = 3
        elif dx < 0 and dy < 0: zone = 4
        elif dx >= 0 and dy < 0: zone = 7
    else:
        if dx >= 0 and dy >= 0: zone = 1
        elif dx < 0 and dy >= 0: zone = 2
        elif dx < 0 and dy < 0: zone = 5
        elif dx >= 0 and dy < 0: zone = 6
    glColor3f(*rgb)
    glPointSize(2)
    glBegin(GL_POINTS)
    glVertex2f(x1, y1)
    x1, y1 = zone_to0(x1, y1, zone)
    x2, y2 = zone_to0(x2, y2, zone)
    dx = x2 - x1
    dy = y2 - y1
    d = 2 * dy - dx
    dE = 2 * dy
    dNE = 2 * (dy - dx)
    x, y = x1, y1
    while x <= x2:
        if d <= 0:
            d += dE
        else:
            d += dNE
            y += 1
        ox, oy = zone_original(x, y, zone)
        glVertex2f(ox, oy)
        x += 1
    glEnd()

def draw_gem(x, y, rgb):
    draw_line(x, y, x - 15, y - 20, rgb)
    draw_line(x - 15, y - 20, x, y - 40, rgb)
    draw_line(x, y - 40, x + 15, y - 20, rgb)
    draw_line(x + 15, y - 20, x, y, rgb)

def draw_bowl(x, y, rgb):
    draw_line(x - 70, y, x + 70, y, rgb)
    draw_line(x - 40, 1, x + 40, 1, rgb)
    draw_line(x - 40, 1, x - 70, y, rgb)
    draw_line(x + 40, 1, x + 70, y, rgb)

def draw_exit(x, y, rgb):
    draw_line(x, y, x + 50, y - 50, rgb)
    draw_line(x, y - 50, x + 50, y, rgb)

def draw_restart(x, y, rgb):
    draw_line(x, y, x + 50, y, rgb)
    draw_line(x, y, x + 20, y + 25, rgb)
    draw_line(x, y, x + 20, y - 25, rgb)

def draw_play_button(x, y, rgb):
    if playing:
        draw_line(x - 15, y + 25, x - 15, y - 25, rgb)
        draw_line(x + 15, y + 25, x + 15, y - 25, rgb)
    else:
        draw_line(x - 15, y + 25, x - 15, y - 25, rgb)
        draw_line(x - 15, y + 25, x + 20, y, rgb)
        draw_line(x - 15, y - 25, x + 20, y, rgb)

def key_listener(key, x, y):
    global playing
    if key == b' ':
        playing = not playing
    glutPostRedisplay()

def special_listener(key, x, y):
    global bowl_x
    if not game_over and playing:
        if key == GLUT_KEY_RIGHT and bowl_x + 70 <= 500:
            bowl_x += 10
        if key == GLUT_KEY_LEFT and bowl_x - 70 >= 0:
            bowl_x -= 10

def mouse_listener(button, state, x, y):
    global playing, gem_rgb, gem_x, gem_y, game_over, fall_speed, score, bowl_rgb
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        x, y = ogl_coords(x, y)
        if btn_restart_x <= x <= btn_restart_x + 50 and btn_restart_y - 25 <= y <= btn_restart_y + 25:
            playing = True
            game_over = False
            gem_x = random.uniform(100, 500)
            gem_y = 700
            fall_speed = 0.06
            score = 0
            bowl_rgb = [1, 1, 1]
            gem_rgb = [random.random(), random.random(), random.random()]
        if btn_play_x - 25 <= x <= btn_play_x + 25 and btn_play_y - 25 <= y <= btn_play_y + 25:
            if not game_over:
                playing = not playing
        if btn_exit_x <= x <= btn_exit_x + 50 and btn_exit_y - 50 <= y <= btn_exit_y:
            print("Your Total Score is:", score)
            glutLeaveMainLoop()
    glutPostRedisplay()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0, 0, 0, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, 500, 700)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 700, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    global gem_x, gem_y, bowl_x, bowl_y, gem_rgb, bowl_rgb, game_over
    if not game_over:
        draw_gem(gem_x, gem_y, gem_rgb)
    draw_bowl(bowl_x, bowl_y, bowl_rgb)
    draw_exit(btn_exit_x, btn_exit_y, [1, 0, 0])
    draw_restart(btn_restart_x, btn_restart_y, [0, 0, 1])
    draw_play_button(btn_play_x, btn_play_y, [0, 1, 0])
    glutSwapBuffers()

def animate():
    glutPostRedisplay()
    global gem_x, gem_y, fall_speed, score, gem_rgb, bowl_rgb, playing, game_over
    if playing:
        if math.floor(gem_y - 45) == bowl_y and bowl_x - 75 < gem_x < bowl_x + 75:
            gem_x = random.uniform(100, 500)
            gem_y = 650
            fall_speed += 0.02
            score += 1
            gem_rgb = [random.random(), random.random(), random.random()]
            print("Your Score:", score)
        elif math.floor(gem_y - 40) > bowl_y:
            gem_y -= fall_speed
        else:
            print("Game is Over! Your Score:", score)
            score = 0
            bowl_rgb = [1, 0, 0]
            playing = False
            game_over = True

def init():
    glClearColor(0, 0, 0, 0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(104, 1, 1, 1000.0)

glutInit()
glutInitWindowSize(win_w, win_h)
glutInitWindowPosition(0, 0)
glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)
window = glutCreateWindow(b"lab2")
init()
glutDisplayFunc(display)
glutIdleFunc(animate)
glutKeyboardFunc(key_listener)
glutSpecialFunc(special_listener)
glutMouseFunc(mouse_listener)
glutMainLoop()
