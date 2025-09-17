import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


class BlackHole3D(QGLWidget):
    def __init__(self):
        super().__init__()
        self.particles = []
        self.angle_x = 20
        self.angle_y = 30
        self.last_mouse_pos = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(16)

    def initializeGL(self):
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0, 0, 0, 1)

        glPointSize(5.0)

        self.spawn_particles()

    def spawn_particles(self):
        self.particles = []
        for _ in range(3000):
            r = random.uniform(2.0, 7.0)
            theta = random.uniform(0, 2 * math.pi)
            phi = math.pi / 2 + random.uniform(-0.2, 0.2)
            speed = random.uniform(0.005, 0.02)
            self.particles.append({
                "r": r, "theta": theta, "phi": phi, "speed": speed
            })

    def update_scene(self):
        for p in self.particles:
            p["theta"] += p["speed"]
            p["r"] -= 0.002
            if p["r"] <= 0.5:
                self.respawn_particle(p)
        self.update()

    def respawn_particle(self, p):
        p["r"] = random.uniform(6.0, 7.0)
        p["theta"] = random.uniform(0, 2 * math.pi)
        p["phi"] = math.pi / 2 + random.uniform(-0.1, 0.1)
        p["speed"] = random.uniform(0.02, 0.05)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, -20)
        glRotatef(self.angle_x, 1, 0, 0)
        glRotatef(self.angle_y, 0, 1, 0)

        # --- Trou noir central ---
        glColor3f(0, 0, 0)
        quad = gluNewQuadric()
        gluSphere(quad, 1.5, 32, 32)

        # --- Disque d’accrétion ---
        glBegin(GL_POINTS)
        for p in self.particles:
            x = p["r"] * math.sin(p["phi"]) * math.cos(p["theta"])
            y = p["r"] * math.sin(p["phi"]) * math.sin(p["theta"])
            z = p["r"] * math.cos(p["phi"])

            # Couleur selon la distance → plus chaud proche du centre
            heat = max(0.0, min(1.0, 1 - (p["r"] / 7.0)))
            r = 1.0
            g = heat * 0.6
            b = 0.0
            glColor3f(r, g, b)

            glVertex3f(x, y, z)
        glEnd()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            self.angle_x += dy * 0.5
            self.angle_y += dx * 0.5
            self.update()
            self.last_mouse_pos = event.pos()


def ee3():
    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = BlackHole3D()
    window.setCentralWidget(widget)
    window.setGeometry(100, 100, 1000, 800)
    window.setWindowTitle("Black Hole 3D")
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
    window.show()
    sys.exit(app.exec_())
