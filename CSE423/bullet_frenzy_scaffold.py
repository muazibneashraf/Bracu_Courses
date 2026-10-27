# bullet_frenzy_scaffold.py
# Drop-in scaffold for the "Bullet Frenzy" PyOpenGL assignment.
# Uses only: glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glScalef, glColor3f, gluPerspective, gluLookAt.
# All primitive drawing must come from the TEMPLATE (drawSphere, drawCylinder, drawCuboid, drawGridDynamic, drawBoundaries, drawText2D).
#
# Hooking instructions:
#   reshape(w,h) -> BF_apply_projection(w,h)
#   display()    -> BF_draw_scene()
#   animate()/idle() -> BF_update()      (do NOT add glutTimerFunc per assignment)
#   keyboardListener(key, x, y)     -> BF_on_key_down(key)
#   keyboardUpListener(key, x, y)   -> BF_on_key_up(key)  [if available]
#   specialKeyListener(key, x, y)   -> BF_on_special_key(key)
#   mouseListener(button, state, x, y) -> BF_on_mouse(button, state, x, y)
#
# Produced by ChatGPT ("GPT-5 Pro") on 2025-08-22.

from math import sin, cos, atan2, sqrt, radians, degrees, pi
import random, time

from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glScalef, glColor3f
from OpenGL.GLU import gluPerspective, gluLookAt

WORLD_HALF = 50.0
GRID_SPACING = 2.0
WALL_HEIGHT = 8.0

PLAYER_MOVE_SPEED = 0.35
PLAYER_TURN_SPEED = 2.2
PLAYER_RADIUS = 1.2

BULLET_SPEED = 1.2
BULLET_SIZE = 0.35
BULLET_COOLDOWN = 0.15
BULLET_MAX_RANGE = WORLD_HALF * 2.0

ENEMY_COUNT = 5
ENEMY_BASE_RADIUS = 1.1
ENEMY_OSC_AMP = 0.18
ENEMY_SPEED = 0.18

LOS_ANGLE_DEG = 5.0
ENEMY_RESPAWN_MARGIN = 10.0

LIVES_INIT = 5
MISS_LIMIT = 10

CAM_FOV_DEFAULT = 70.0
CAM_FOV_CHEAT = 85.0
CAM_DIST = 26.0
CAM_HEIGHT = 10.0
CAM_MIN_HEIGHT = 4.0
CAM_MAX_HEIGHT = 25.0

def clamp(v, lo, hi): return max(lo, min(hi, v))
def length2d(x, z): return sqrt(x*x + z*z)
def normalize2d(x, z):
    d = length2d(x, z)
    return (0.0, 0.0) if d <= 1e-8 else (x/d, z/d)
def within_bounds(x, z):
    return (-WORLD_HALF <= x <= WORLD_HALF) and (-WORLD_HALF <= z <= WORLD_HALF)

class Player:
    def __init__(self):
        self.x = 0.0; self.y = 0.0; self.z = 0.0
        self.yaw = 0.0; self.pitch = 0.0
        self.last_shot_time = 0.0

class Enemy:
    def __init__(self, x, z):
        self.x = x; self.z = z
        self.scale_phase = random.uniform(0, 2*pi)
    def scaled_radius(self, dt_seconds=0.0):
        self.scale_phase += dt_seconds * 2.0
        s = 1.0 + ENEMY_OSC_AMP * sin(self.scale_phase)
        return ENEMY_BASE_RADIUS * s, s

class Bullet:
    def __init__(self, x, y, z, yaw_deg):
        self.x = x; self.y = y; self.z = z
        self.yaw = yaw_deg; self.alive = True; self.distance_travelled = 0.0

class Camera:
    def __init__(self):
        self.first_person = False
        self.yaw = 45.0
        self.height = CAM_HEIGHT
        self.fov = CAM_FOV_DEFAULT
        self.auto_cheat_follow = False
        self.eye = (0.0,0.0,0.0); self.center=(0.0,0.0,0.0); self.up=(0.0,1.0,0.0)

class GameState:
    def __init__(self):
        self.player = Player(); self.camera = Camera()
        self.enemies = []; self.bullets = []
        self.score = 0; self.missed = 0; self.lives = LIVES_INIT
        self.game_over = False; self.cheat = False
        self._cheat_spin_speed = 1.8
        self._last_time = time.time()
        self._hurt_cooldown = 0.0
        self.key_w = self.key_s = self.key_a = self.key_d = False
        self.reset_enemies()
    def reset_enemies(self):
        self.enemies = [Enemy(*self._random_spawn()) for _ in range(ENEMY_COUNT)]
    def _random_spawn(self):
        while True:
            x = random.uniform(-WORLD_HALF+1.0, WORLD_HALF-1.0)
            z = random.uniform(-WORLD_HALF+1.0, WORLD_HALF-1.0)
            if length2d(x,z) > ENEMY_RESPAWN_MARGIN: return x,z
    def reset_game(self):
        self.__init__()
    def on_key_down(self, key):
        if self.game_over and (key in ('r','R')): self.reset_game(); return
        if   key in ('w','W'): self.key_w=True
        elif key in ('s','S'): self.key_s=True
        elif key in ('a','A'): self.key_a=True
        elif key in ('d','D'): self.key_d=True
        elif key in ('c','C'): self.cheat=not self.cheat
        elif key in ('v','V'): self.camera.auto_cheat_follow=not self.camera.auto_cheat_follow
    def on_key_up(self, key):
        if   key in ('w','W'): self.key_w=False
        elif key in ('s','S'): self.key_s=False
        elif key in ('a','A'): self.key_a=False
        elif key in ('d','D'): self.key_d=False
    def on_special_key(self, key):
        GLUT_KEY_LEFT=100; GLUT_KEY_UP=101; GLUT_KEY_RIGHT=102; GLUT_KEY_DOWN=103
        if key==GLUT_KEY_LEFT and not self.camera.first_person:  self.camera.yaw -= 3.0
        elif key==GLUT_KEY_RIGHT and not self.camera.first_person: self.camera.yaw += 3.0
        elif key==GLUT_KEY_UP and not self.camera.first_person:    self.camera.height = clamp(self.camera.height+0.8, CAM_MIN_HEIGHT, CAM_MAX_HEIGHT)
        elif key==GLUT_KEY_DOWN and not self.camera.first_person:  self.camera.height = clamp(self.camera.height-0.8, CAM_MIN_HEIGHT, CAM_MAX_HEIGHT)
    def on_mouse(self, button, state, x, y):
        GLUT_LEFT_BUTTON=0; GLUT_RIGHT_BUTTON=2; GLUT_DOWN=0
        if self.game_over: return
        if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN: self.try_fire()
        elif button==GLUT_RIGHT_BUTTON and state==GLUT_DOWN: self.camera.first_person = not self.camera.first_person
    def update(self):
        now=time.time(); dt=now-self._last_time; self._last_time=now
        target_fov = CAM_FOV_DEFAULT
        if self.cheat and self.camera.first_person and self.camera.auto_cheat_follow: target_fov = CAM_FOV_CHEAT
        self.camera.fov += (target_fov - self.camera.fov)*0.15
        if self.game_over:
            self.player.pitch = min(90.0, self.player.pitch + 120.0*dt); return
        if self.key_a: self.player.yaw += PLAYER_TURN_SPEED
        if self.key_d: self.player.yaw -= PLAYER_TURN_SPEED
        dir_x = sin(radians(self.player.yaw)); dir_z = cos(radians(self.player.yaw))
        move=0.0
        if self.key_w: move += PLAYER_MOVE_SPEED
        if self.key_s: move -= PLAYER_MOVE_SPEED
        if abs(move)>1e-6:
            nx=self.player.x + dir_x*move; nz=self.player.z + dir_z*move
            if within_bounds(nx,nz): self.player.x, self.player.z = nx, nz
        if self.cheat:
            self.player.yaw += self._cheat_spin_speed
            if self._has_enemy_in_los(): self.try_fire()
        for e in self.enemies:
            vx=self.player.x-e.x; vz=self.player.z-e.z; ux,uz = normalize2d(vx,vz)
            e.x += ux*ENEMY_SPEED; e.z += uz*ENEMY_SPEED
            if not within_bounds(e.x,e.z):
                e.x = clamp(e.x,-WORLD_HALF,WORLD_HALF); e.z=clamp(e.z,-WORLD_HALF,WORLD_HALF)
        self._hurt_cooldown = max(0.0, self._hurt_cooldown - dt)
        if self._hurt_cooldown<=0.0:
            for e in self.enemies:
                er,_ = e.scaled_radius(dt_seconds=dt)
                if self._sphere_sphere(self.player.x,self.player.z,PLAYER_RADIUS, e.x,e.z,er):
                    self.lives -= 1; self._hurt_cooldown=0.6
                    if self.lives<=0: self._trigger_game_over()
                    break
        for b in list(self.bullets):
            if not b.alive: continue
            bx = sin(radians(b.yaw))*BULLET_SPEED; bz = cos(radians(b.yaw))*BULLET_SPEED
            b.x += bx; b.z += bz; b.distance_travelled += BULLET_SPEED
            if (not within_bounds(b.x,b.z)) or (b.distance_travelled>BULLET_MAX_RANGE):
                b.alive=False; self.missed += 1
                if self.missed>=MISS_LIMIT: self._trigger_game_over()
                continue
            for e in self.enemies:
                er,_ = e.scaled_radius(dt_seconds=dt)
                if self._sphere_box_hit(e.x,e.z,er, b.x,b.z, BULLET_SIZE*0.5):
                    b.alive=False; self.score+=1; e.x,e.z = self._random_spawn(); break
        self.bullets = [b for b in self.bullets if b.alive]
    def try_fire(self):
        t=time.time()
        if t - self.player.last_shot_time < BULLET_COOLDOWN: return
        self.player.last_shot_time = t
        yaw=self.player.yaw; dirx=sin(radians(yaw)); dirz=cos(radians(yaw))
        bx=self.player.x + dirx*1.8; by=1.0; bz=self.player.z + dirz*1.8
        self.bullets.append(Bullet(bx,by,bz,yaw))
    def _has_enemy_in_los(self):
        pyaw=self.player.yaw; px,pz=self.player.x,self.player.z
        for e in self.enemies:
            vx=e.x-px; vz=e.z-pz
            if abs(vx)<1e-5 and abs(vz)<1e-5: continue
            angle=degrees(atan2(vx,vz))
            d=abs((angle-pyaw+180.0)%360.0-180.0)
            if d<=LOS_ANGLE_DEG: return True
        return False
    def _trigger_game_over(self): self.game_over=True
    @staticmethod
    def _sphere_sphere(x1,z1,r1, x2,z2,r2):
        dx=x1-x2; dz=z1-z2; return (dx*dx+dz*dz) <= (r1+r2)**2
    @staticmethod
    def _sphere_box_hit(cx,cz,cr, bx,bz,half):
        closest_x = clamp(cx, bx-half, bx+half); closest_z = clamp(cz, bz-half, bz+half)
        dx=cx-closest_x; dz=cz-closest_z; return (dx*dx+dz*dz) <= (cr*cr)

_gs = GameState()

def BF_apply_projection(width, height):
    aspect = max(1, width) / float(max(1, height))
    gluPerspective(_gs.camera.fov, aspect, 0.1, 500.0)

def BF_apply_view():
    if _gs.camera.first_person:
        yaw=radians(_gs.player.yaw); fx=sin(yaw); fz=cos(yaw)
        eye=(_gs.player.x, 1.6, _gs.player.z); center=(eye[0]+fx, eye[1]+0.0, eye[2]+fz); up=(0.0,1.0,0.0)
        _gs.camera.eye, _gs.camera.center, _gs.camera.up = eye, center, up
        gluLookAt(eye[0],eye[1],eye[2], center[0],center[1],center[2], up[0],up[1],up[2])
    else:
        yaw=radians(_gs.camera.yaw); eye_x=sin(yaw)*CAM_DIST; eye_z=cos(yaw)*CAM_DIST
        eye=(eye_x, _gs.camera.height, eye_z); center=(0.0,0.0,0.0); up=(0.0,1.0,0.0)
        _gs.camera.eye, _gs.camera.center, _gs.camera.up = eye, center, up
        gluLookAt(eye[0],eye[1],eye[2], center[0],center[1],center[2], up[0],up[1],up[2])

# Template hooks (must be provided by TEMPLATE)
def drawSphere(radius): raise NotImplementedError("Provide drawSphere(radius) from the template.")
def drawCylinder(radius,height): raise NotImplementedError("Provide drawCylinder(radius,height) from the template.")
def drawCuboid(x,y,z): raise NotImplementedError("Provide drawCuboid(x,y,z) from the template.")
def drawGridDynamic(size,spacing): raise NotImplementedError("Provide drawGridDynamic(size,spacing) from the template.")
def drawBoundaries(size,height): raise NotImplementedError("Provide drawBoundaries(size,height) from the template.")
def drawText2D(x,y,msg): pass  # optional

def _draw_player():
    p=_gs.player
    glPushMatrix(); glTranslatef(p.x,p.y,p.z)
    if _gs.game_over: glRotatef(p.pitch, 1.0,0.0,0.0)
    glRotatef(p.yaw, 0.0,1.0,0.0)
    glPushMatrix(); glColor3f(0.3,0.6,0.9); glTranslatef(0.0,1.0,0.0); glRotatef(-90.0, 1.0,0.0,0.0); drawCylinder(0.5,2.0); glPopMatrix()
    glPushMatrix(); glColor3f(0.9,0.8,0.6); glTranslatef(0.0,2.2,0.0); drawSphere(0.55); glPopMatrix()
    glPushMatrix(); glColor3f(0.1,0.1,0.1); glTranslatef(0.0,1.5,1.0); glScalef(0.3,0.3,2.0); drawCuboid(1.0,1.0,1.0); glPopMatrix()
    glPushMatrix(); glColor3f(0.3,0.6,0.9); glTranslatef(0.6,1.6,0.0); glRotatef(90.0,0.0,1.0,0.0); drawCylinder(0.15,1.3); glPopMatrix()
    glPushMatrix(); glColor3f(0.3,0.6,0.9); glTranslatef(-0.6,1.6,0.0); glRotatef(90.0,0.0,1.0,0.0); drawCylinder(0.15,1.3); glPopMatrix()
    glPopMatrix()

def _draw_enemy(e, dt_seconds):
    radius, scale = e.scaled_radius(dt_seconds)
    glPushMatrix(); glTranslatef(e.x,0.0,e.z)
    glPushMatrix(); glColor3f(0.9,0.2,0.2); glScalef(scale,scale,scale); drawSphere(radius); glPopMatrix()
    glPushMatrix(); glColor3f(1.0,0.6,0.6); glTranslatef(0.0, radius*1.1, 0.0); glScalef(scale*0.8,scale*0.8,scale*0.8); drawSphere(radius*0.8); glPopMatrix()
    glPopMatrix()

def _draw_bullet(b):
    glPushMatrix(); glTranslatef(b.x,b.y,b.z); glRotatef(b.yaw, 0.0,1.0,0.0); glColor3f(1.0,1.0,0.2)
    glScalef(BULLET_SIZE,BULLET_SIZE,BULLET_SIZE*2.0); drawCuboid(1.0,1.0,1.0); glPopMatrix()

def BF_draw_scene():
    BF_apply_view()
    glPushMatrix(); glColor3f(0.8,0.8,0.8); drawGridDynamic(WORLD_HALF, GRID_SPACING); glPopMatrix()
    glPushMatrix(); glColor3f(0.5,0.5,0.5); drawBoundaries(WORLD_HALF, WALL_HEIGHT); glPopMatrix()
    _draw_player()
    dt_for_draw=0.016
    for e in _gs.enemies: _draw_enemy(e, dt_for_draw)
    for b in _gs.bullets: _draw_bullet(b)
    if drawText2D is not None:
        drawText2D(10,10, f"Score: {_gs.score}")
        drawText2D(10,30, f"Lives: {_gs.lives}")
        drawText2D(10,50, f"Missed: {_gs.missed}/{MISS_LIMIT}")
        drawText2D(10,70, f"Mode: {'FP' if _gs.camera.first_person else 'TP'} | Cheat: {'ON' if _gs.cheat else 'OFF'}")
        if _gs.game_over: drawText2D(10,100, "GAME OVER - press 'R' to restart")

def BF_update(): _gs.update()

def BF_on_key_down(key):
    if isinstance(key, bytes): key = key.decode('utf-8', errors='ignore')
    _gs.on_key_down(key)
def BF_on_key_up(key):
    if isinstance(key, bytes): key = key.decode('utf-8', errors='ignore')
    _gs.on_key_up(key)
def BF_on_special_key(key): _gs.on_special_key(key)
def BF_on_mouse(button, state, x, y): _gs.on_mouse(button, state, x, y)
def BF_get_state(): return _gs
