import sys
import math
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QMainWindow, QSizePolicy
)

PLANETS = [
    {"name": "Mercury", "radius": 50, "period_days": 87.969, "color": QColor(170, 170, 170), "size": 6},
    {"name": "Venus", "radius": 80, "period_days": 224.701, "color": QColor(255, 210, 120), "size": 8},
    {"name": "Earth", "radius": 110, "period_days": 365.256, "color": QColor(90, 140, 255), "size": 9},
    {"name": "Mars", "radius": 150, "period_days": 686.980, "color": QColor(255, 100, 70), "size": 7},
    {"name": "Jupiter", "radius": 210, "period_days": 4332.589, "color": QColor(240, 160, 120), "size": 12},
    {"name": "Saturn", "radius": 270, "period_days": 10759, "color": QColor(230, 200, 150), "size": 11},
    {"name": "Uranus", "radius": 325, "period_days": 30688, "color": QColor(140, 200, 230), "size": 10},
    {"name": "Neptune", "radius": 380, "period_days": 60182, "color": QColor(120, 140, 255), "size": 10},
]

MAX_YEAR_OFFSET = 1000
TIMER_INTERVAL_MS = 30


class SolarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(900, 700)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.now_real = datetime.now()
        self.year_offset = 0
        self.simulated_time = datetime.now()
        self.speed_multiplier = 1
        self.paused = False

        self.view_angle = 0.0
        self._dragging = False
        self._last_mouse_pos = QPoint()

        self.timer = QTimer(self)
        self.timer.setInterval(TIMER_INTERVAL_MS)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start()

        self.center = (self.width() // 2, self.height() // 2)
        self.show_orbits = True

    def set_year_offset(self, years: int):
        self.year_offset = years
        self._recompute_sim_time_from_now()

    def set_speed_multiplier(self, m: int):
        self.speed_multiplier = m

    def set_paused(self, paused: bool):
        self.paused = paused

    def toggle_pause(self):
        self.paused = not self.paused

    def _recompute_sim_time_from_now(self):
        base = datetime.now() + timedelta(days=365.25 * self.year_offset)
        self.simulated_time = base

    def _on_tick(self):
        if not self.paused:
            delta_seconds = (TIMER_INTERVAL_MS / 1000.0) * self.speed_multiplier
            self.simulated_time = self.simulated_time + timedelta(seconds=delta_seconds)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        self.center = (w // 2, h // 2 - 20)

        painter.fillRect(0, 0, w, h, QColor(8, 8, 12))

        self._draw_sun(painter)

        for planet in PLANETS:
            self._draw_orbit(painter, planet)
        for planet in PLANETS:
            self._draw_planet(painter, planet)

        painter.setPen(QColor(200, 200, 210))
        font = QFont("Helvetica", 10)
        painter.setFont(font)
        sim_time_str = self.simulated_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        painter.drawText(12, h - 60, f"Simulated time: {sim_time_str}")
        painter.drawText(12, h - 40,
                         f"Year offset: {self.year_offset:+d} yrs    Speed: {self.speed_multiplier}x    {'PAUSED' if self.paused else ''}")
        painter.drawText(12, h - 20, "Drag mouse to rotate view · Toggle orbits with 'O' key")

        painter.end()

    def _draw_sun(self, painter: QPainter):
        cx, cy = self.center
        for i, alpha in enumerate([30, 50, 90, 150], start=1):
            r = 40 + i * 20
            color = QColor(255, 200 - i * 10, 80, alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.setBrush(QColor(255, 220, 120))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - 18, cy - 18, 36, 36)

    def _draw_orbit(self, painter: QPainter, planet_def):
        if not self.show_orbits:
            return
        cx, cy = self.center
        radius = planet_def["radius"]
        painter.setPen(QColor(80, 80, 90, 140))
        painter.setBrush(Qt.NoBrush)
        tilt = math.cos(math.radians(self.view_angle)) * 0.7 + 0.5
        rx = radius
        ry = int(radius * tilt)
        painter.drawEllipse(cx - rx, cy - ry, rx * 2, ry * 2)

    def _planet_position(self, planet_def):
        j2000 = datetime(2000, 1, 1, 12)
        delta = self.simulated_time - j2000
        days = delta.total_seconds() / 86400.0

        period = planet_def["period_days"]
        frac = (days % period) / period
        angle = 2.0 * math.pi * frac

        name_hash = sum(ord(c) for c in planet_def["name"])
        phase = (name_hash % 100) / 100.0 * 2.0 * math.pi
        angle += phase

        r = planet_def["radius"]
        x = r * math.cos(angle)
        y = r * math.sin(angle)

        theta = math.radians(self.view_angle)
        xr = x * math.cos(theta) - y * math.sin(theta)
        yr = x * math.sin(theta) + y * math.cos(theta)

        tilt = math.cos(math.radians(self.view_angle)) * 0.6 + 0.5
        yr *= tilt

        cx, cy = self.center
        return cx + xr, cy + yr

    def _draw_planet(self, painter: QPainter, planet_def):
        x, y = self._planet_position(planet_def)
        size = planet_def.get("size", 6)
        color = planet_def.get("color", QColor(200, 200, 200))
        glow_color = QColor(color)
        glow_color.setAlpha(120)
        painter.setBrush(glow_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x - size * 2), int(y - size * 2), int(size * 4), int(size * 4))
        painter.setBrush(color)
        painter.setPen(QColor(30, 30, 30, 200))
        painter.drawEllipse(int(x - size), int(y - size), int(size * 2), int(size * 2))
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        planet_name = planet_def.get("name", "")
        painter.drawText(int(x + size + 2), int(y), planet_name)

    def mousePressEvent(self, ev):
        self._dragging = True
        self._last_mouse_pos = ev.pos()

    def mouseMoveEvent(self, ev):
        if not self._dragging:
            return
        dx = ev.x() - self._last_mouse_pos.x()
        self.view_angle = (self.view_angle + dx * 0.3) % 360
        self._last_mouse_pos = ev.pos()
        self.update()

    def mouseReleaseEvent(self, ev):
        self._dragging = False

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_O:
            self.show_orbits = not self.show_orbits
            self.update()


class SolarWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Solar System")
        self.widget = SolarWidget()
        self.setCentralWidget(self.widget)

        controls = QWidget()
        h = QHBoxLayout()
        controls.setLayout(h)

        self.year_label = QLabel("Year offset: 0")
        h.addWidget(self.year_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(-MAX_YEAR_OFFSET)
        self.slider.setMaximum(MAX_YEAR_OFFSET)
        self.slider.setValue(0)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self._on_slider)
        h.addWidget(self.slider, 1)

        self.speed_buttons = []
        speeds = [1, 2048, 4096, 8192, 16384, 32768]
        for s in speeds:
            btn = QPushButton(f"{s}×")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, s=s*365.25: self._on_speed_button(s))
            self.speed_buttons.append(btn)
            h.addWidget(btn)

        self.play_btn = QPushButton("Pause")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self._on_play_pause)
        h.addWidget(self.play_btn)

        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self._on_reset_view)
        h.addWidget(reset_btn)

        self.time_label = QLabel("")
        h.addWidget(self.time_label)

        v = QVBoxLayout()
        v.addWidget(self.widget)
        v.addWidget(controls)
        container = QWidget()
        container.setLayout(v)
        self.setCentralWidget(container)

        self._select_speed_button(1)
        self.widget.set_paused(False)

        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(200)
        self.ui_timer.timeout.connect(self._update_ui_labels)
        self.ui_timer.start()

    def _on_slider(self, value):
        self.year_label.setText(f"Year offset: {value:+d}")
        self.widget.set_year_offset(value)

    def _on_speed_button(self, speed):
        self._select_speed_button(speed)
        self.widget.set_speed_multiplier(speed)
        if self.widget.paused:
            pass
        else:
            self.widget.set_paused(False)
            self.play_btn.setChecked(False)
            self.play_btn.setText("Pause")

    def _select_speed_button(self, speed):
        for btn in self.speed_buttons:
            btn_speed = int(btn.text()[:-1])  # "4×" -> 4
            btn.setChecked(btn_speed == speed)

    def _on_play_pause(self, checked):
        self.widget.set_paused(checked)
        if checked:
            self.play_btn.setText("Play")
        else:
            self.play_btn.setText("Pause")

    def _on_reset_view(self):
        self.widget.view_angle = 0
        self.widget.update()

    def _update_ui_labels(self):
        st = self.widget.simulated_time
        self.time_label.setText(st.strftime("%Y-%m-%d %H:%M:%S"))
        self._select_speed_button(self.widget.speed_multiplier)


def ee4():
    app = QApplication(sys.argv)
    window = SolarWindow()
    window.resize(1100, 820)
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
    window.show()
    sys.exit(app.exec_())
