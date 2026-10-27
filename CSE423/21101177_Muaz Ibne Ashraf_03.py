from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

camera_pos = (0, 500, 500)
fovY = 120
GRID_LENGTH = 600
rand_var = 423

player_x, player_y = 0.0, 0.0
player_speed = 6.0
gun_angle_deg = 0.0
player_hit_radius = 40.0
first_person = False

camera_orbit_angle = 25.0
camera_radius = 900.0
camera_height = 360.0

cheat_mode = False
cheat_follow = False
cheat_spin_speed = 1.0
cheat_fire_tolerance_deg = 5.0

bullets = []
bullet_speed = 18.0
bullet_size = 14.0
bullet_cooldown_frames = 14
bullet_cooldown = 0
bullet_max_dist = GRID_LENGTH * 2.0

NUM_ENEMIES = 5
enemies = []
enemy_speed = 1.4
enemy_body_r = 32.0
enemy_head_r = 20.0

score = 0
lives = 5
missed = 0
game_over = False

frame_count = 0
target_frame_dt = 1.0 / 60.0
_last_tick = 0.0

random.seed(rand_var)

def clamp(val, lo, hi):
    return lo if val < lo else (hi if val > hi else val)

def deg2rad(d):
    return d * math.pi / 180.0

def angdiff_deg(a, b):
    return (a - b + 180.0) % 360.0 - 180.0

def within_bounds(x, y, margin=40.0):
    lim = GRID_LENGTH - margin
    return (-lim <= x <= lim) and (-lim <= y <= lim)

def spawn_enemy():
    margin = 120.0
    for _ in range(100):
        ex = random.uniform(-GRID_LENGTH + margin, GRID_LENGTH - margin)
        ey = random.uniform(-GRID_LENGTH + margin, GRID_LENGTH - margin)
        if math.hypot(ex - player_x, ey - player_y) > 250.0:
            return {"x": ex, "y": ey, "phase": random.uniform(0.0, 6.28318)}
    return {"x": GRID_LENGTH - margin, "y": GRID_LENGTH - margin, "phase": 0.0}

def reset_game():
    global score, lives, missed, game_over, bullets, enemies, gun_angle_deg, player_x, player_y, bullet_cooldown
    score, lives, missed = 0, 5, 0
    game_over = False
    bullets.clear()
    enemies[:] = [spawn_enemy() for _ in range(NUM_ENEMIES)]
    gun_angle_deg = 0.0
    player_x, player_y = 0.0, 0.0
    bullet_cooldown = 0

enemies[:] = [spawn_enemy() for _ in range(NUM_ENEMIES)]

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_grid_and_walls():
    tile = 60.0
    half = GRID_LENGTH
    toggle = 0
    for iy in range(int(-half), int(half), int(tile)):
        toggle ^= 1
        for ix in range(int(-half), int(half), int(tile)):
            if toggle:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.85, 0.80, 1.0)
            glBegin(GL_QUADS)
            glVertex3f(ix, iy, 0.0)
            glVertex3f(ix + tile, iy, 0.0)
            glVertex3f(ix + tile, iy + tile, 0.0)
            glVertex3f(ix, iy + tile, 0.0)
            glEnd()
            toggle ^= 1

    wall_h = 120.0
    glBegin(GL_QUADS)
    glColor3f(0.0, 1.0, 0.0)      # +X right (green)
    glVertex3f(half, -half, 0.0); glVertex3f(half,  half, 0.0); glVertex3f(half,  half, wall_h); glVertex3f(half, -half, wall_h)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0.0, 0.0, 1.0)      # -X left (blue)
    glVertex3f(-half, -half, 0.0); glVertex3f(-half,  half, 0.0); glVertex3f(-half,  half, wall_h); glVertex3f(-half, -half, wall_h)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0.0, 1.0, 1.0)      # +Y top/far (cyan)
    glVertex3f(-half, half, 0.0); glVertex3f( half, half, 0.0); glVertex3f( half, half, wall_h); glVertex3f(-half, half, wall_h)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0.0, 1.0, 0.0)      # -Y near (green)
    glVertex3f(-half, -half, 0.0); glVertex3f( half, -half, 0.0); glVertex3f( half, -half, wall_h); glVertex3f(-half, -half, wall_h)
    glEnd()

def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, 0.0)
    if game_over:
        glRotatef(90.0, 0.0, 1.0, 0.0)
    glRotatef(gun_angle_deg, 0.0, 0.0, 1.0)
    glColor3f(0.9, 0.2, 0.2)
    gluCylinder(gluNewQuadric(), 22.0, 22.0, 70.0, 12, 8)
    glPushMatrix()
    glTranslatef(0.0, 0.0, 88.0)
    glColor3f(0.95, 0.85, 0.7)
    gluSphere(gluNewQuadric(), 20.0, 12, 12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-14.0, -12.0, 8.0); glScalef(1.6, 0.6, 0.5); glColor3f(0.2, 0.2, 0.2); glutSolidCube(20.0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(14.0, -12.0, 8.0); glScalef(1.6, 0.6, 0.5); glColor3f(0.2, 0.2, 0.2); glutSolidCube(20.0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(18.0, 0.0, 48.0); glRotatef(90.0, 0.0, 1.0, 0.0); glColor3f(0.1, 0.1, 0.1)
    gluCylinder(gluNewQuadric(), 5.5, 5.0, 60.0, 10, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-5.0, -4.0, 48.0); glScalef(1.6, 0.5, 0.4); glColor3f(0.15, 0.15, 0.2); glutSolidCube(16.0)
    glPopMatrix()
    glPopMatrix()

def draw_enemy(enemy, scale_breath=1.0):
    ex, ey = enemy["x"], enemy["y"]
    glPushMatrix()
    glTranslatef(ex, ey, 0.0)
    glScalef(scale_breath, scale_breath, scale_breath)
    glPushMatrix()
    glTranslatef(0.0, 0.0, enemy_body_r); glColor3f(0.1, 0.6, 0.9)
    gluSphere(gluNewQuadric(), enemy_body_r, 14, 12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 0.0, enemy_body_r * 2.0 + enemy_head_r * 0.7); glColor3f(0.05, 0.3, 0.7)
    gluSphere(gluNewQuadric(), enemy_head_r, 12, 10)
    glPopMatrix()
    glPopMatrix()

def draw_bullet(b):
    glPushMatrix()
    glTranslatef(b["x"], b["y"], b["z"])
    ang = math.degrees(math.atan2(b["dy"], b["dx"]))
    glRotatef(ang, 0.0, 0.0, 1.0)
    glScalef(1.8, 0.6, 0.6)
    glColor3f(1.0, 0.9, 0.2)
    glutSolidCube(bullet_size)
    glPopMatrix()

def keyboardListener(key, x, y):
    global player_x, player_y, gun_angle_deg, cheat_mode, cheat_follow, fovY, game_over
    global score, lives, missed, bullet_cooldown
    if game_over:
        if key == b'r':
            reset_game()
        return
    if key == b'w':
        rad = deg2rad(gun_angle_deg)
        nx = player_x + math.cos(rad) * player_speed
        ny = player_y + math.sin(rad) * player_speed
        if within_bounds(nx, ny): player_x, player_y = nx, ny
    if key == b's':
        rad = deg2rad(gun_angle_deg)
        nx = player_x - math.cos(rad) * player_speed
        ny = player_y - math.sin(rad) * player_speed
        if within_bounds(nx, ny): player_x, player_y = nx, ny
    if key == b'a': gun_angle_deg = (gun_angle_deg + 4.0) % 360.0
    if key == b'd': gun_angle_deg = (gun_angle_deg - 4.0) % 360.0
    if key == b'c': cheat_mode = not cheat_mode
    if key == b'v': cheat_follow = not cheat_follow
    if key == b'r': reset_game()

def specialKeyListener(key, x, y):
    global camera_orbit_angle, camera_height
    if key == GLUT_KEY_LEFT:  camera_orbit_angle = (camera_orbit_angle + 2.0) % 360.0
    if key == GLUT_KEY_RIGHT: camera_orbit_angle = (camera_orbit_angle - 2.0) % 360.0
    if key == GLUT_KEY_UP:    camera_height = clamp(camera_height + 12.0, 120.0, 1200.0)
    if key == GLUT_KEY_DOWN:  camera_height = clamp(camera_height - 12.0, 80.0, 1200.0)

def mouseListener(button, state, x, y):
    global first_person
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        try_fire_bullet()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        rad = deg2rad(gun_angle_deg)
        eye_x = player_x + math.cos(rad) * 10.0
        eye_y = player_y + math.sin(rad) * 10.0
        eye_z = 70.0
        ctr_x = eye_x + math.cos(rad) * 400.0
        ctr_y = eye_y + math.sin(rad) * 400.0
        ctr_z = 60.0
        gluLookAt(eye_x, eye_y, eye_z, ctr_x, ctr_y, ctr_z, 0.0, 0.0, 1.0)
    else:
        rad = deg2rad(camera_orbit_angle)
        eye_x = player_x - math.cos(rad) * camera_radius
        eye_y = player_y - math.sin(rad) * camera_radius
        eye_z = camera_height
        gluLookAt(eye_x, eye_y, eye_z, player_x, player_y, 50.0, 0.0, 0.0, 1.0)

def try_fire_bullet():
    global bullet_cooldown, bullets, missed
    if bullet_cooldown > 0 or game_over: return
    rad = deg2rad(gun_angle_deg)
    bx = player_x + math.cos(rad) * 60.0
    by = player_y + math.sin(rad) * 60.0
    bz = 48.0
    bullets.append({"x": bx, "y": by, "z": bz, "dx": math.cos(rad), "dy": math.sin(rad), "dist": 0.0})
    bullet_cooldown = bullet_cooldown_frames

def update_bullets():
    global bullets, missed, score
    alive = []
    for b in bullets:
        b["x"] += b["dx"] * bullet_speed
        b["y"] += b["dy"] * bullet_speed
        b["dist"] += bullet_speed
        if not within_bounds(b["x"], b["y"]) or b["dist"] > bullet_max_dist:
            missed_plus_one(); continue
        hit_any = False
        for e in enemies:
            if (b["x"] - e["x"])**2 + (b["y"] - e["y"])**2 <= (enemy_body_r + bullet_size * 0.5)**2:
                score_plus_one(); respawn_enemy(e); hit_any = True; break
        if not hit_any: alive.append(b)
    bullets = alive

def score_plus_one():
    global score
    score += 1

def missed_plus_one():
    global missed, game_over
    missed += 1
    if missed >= 10: game_over = True

def respawn_enemy(enemy):
    new_e = spawn_enemy()
    enemy["x"], enemy["y"], enemy["phase"] = new_e["x"], new_e["y"], new_e["phase"]

def update_enemies():
    global lives, game_over
    for e in enemies:
        vx = player_x - e["x"]; vy = player_y - e["y"]; d = math.hypot(vx, vy)
        if d > 1e-3:
            e["x"] += (vx / d) * enemy_speed
            e["y"] += (vy / d) * enemy_speed
        if (e["x"] - player_x)**2 + (e["y"] - player_y)**2 <= (player_hit_radius + enemy_body_r * 0.5)**2:
            lives -= 1; respawn_enemy(e)
            if lives <= 0: game_over = True

def update_cheat_logic():
    global gun_angle_deg
    if not cheat_mode or game_over: return
    gun_angle_deg = (gun_angle_deg + cheat_spin_speed) % 360.0
    for e in enemies:
        ang = math.degrees(math.atan2(e["y"] - player_y, e["x"] - player_x)) % 360.0
        if abs(angdiff_deg(ang, gun_angle_deg)) <= cheat_fire_tolerance_deg:
            try_fire_bullet(); break

def update_camera_effects():
    global fovY
    if first_person and cheat_mode and cheat_follow:
        fovY = 120.0 + 6.0 * math.sin(frame_count * 0.08)
    else:
        fovY = 120.0

def update_cooldowns():
    global bullet_cooldown
    if bullet_cooldown > 0: bullet_cooldown -= 1

def idle():
    global frame_count, _last_tick
    now = time.time()
    if now - _last_tick < target_frame_dt: return
    _last_tick = now
    frame_count += 1
    if not game_over:
        update_cooldowns()
        update_cheat_logic()
        update_bullets()
        update_enemies()
    update_camera_effects()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()
    draw_grid_and_walls()
    for e in enemies:
        s = 1.0 + 0.12 * math.sin(frame_count * 0.10 + e["phase"])
        draw_enemy(e, s)
    draw_player()
    for b in bullets:
        draw_bullet(b)
    draw_text(10, 770, f"Player Life Remaining: {lives}")
    draw_text(10, 750, f"Game Score: {score}")
    draw_text(10, 730, f"Player Bullet Missed: {missed}")
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy - CSE423 Lab 03")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
