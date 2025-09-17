import math
import random
from Cocoa import (
    NSApplication, NSWindow, NSColor, NSView,
    NSBackingStoreBuffered, NSScreen, NSGraphicsContext
)
from Quartz import CoreGraphics as CG
from PyObjCTools import AppHelper


class BlackHoleView(NSView):
    def __init__(self):
        self.particles = []
        self.center_x = 0
        self.center_y = 0

    def drawRect_(self, rect):
        ctx = NSGraphicsContext.currentContext().CGContext()
        CG.CGContextClearRect(ctx, rect)

        for p in self.particles:
            color = p["color"]
            color.set()
            radius = p["size"]
            CG.CGContextFillEllipseInRect(ctx, ((p["x"] - radius / 2, p["y"] - radius / 2), (radius, radius)))

    def startAnimation(self):
        screen_h = int(self.frame().size.height)
        screen_w = int(self.frame().size.width)

        self.center_x = screen_w // 2
        self.center_y = screen_h // 2

        self.particles = []
        for _ in range(1500):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(50, min(screen_w, screen_h) // 2)
            size = max(1, 5 * (r / (screen_w // 2)))
            speed = random.uniform(0.05, 0.15) * (50 / r)
            fall_speed = random.uniform(1.5, 3.0)
            color = random.choice([
                NSColor.redColor(), NSColor.orangeColor(), NSColor.yellowColor(),
                NSColor.greenColor(), NSColor.blueColor(), NSColor.purpleColor()
            ])
            self.particles.append({
                "r": r,
                "theta": angle,
                "size": size,
                "speed": speed,
                "fall_speed": fall_speed,
                "color": color
            })

        self.animate()

    def animate(self):
        new_particles = []
        for p in self.particles:
            p["theta"] += p["speed"]
            p["r"] -= p["fall_speed"]

            if p["r"] > 0:
                p["x"] = self.center_x + p["r"] * math.cos(p["theta"])
                p["y"] = self.center_y + p["r"] * math.sin(p["theta"])
                new_particles.append(p)

        self.particles = new_particles
        self.setNeedsDisplay_(True)

        if self.particles:
            AppHelper.callLater(0.03, self.animate)
        else:
            self.window().orderOut_(None)


def ee2():
    app = NSApplication.sharedApplication()
    screen = NSScreen.mainScreen().frame()

    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        screen,
        0,
        NSBackingStoreBuffered,
        False
    )
    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setLevel_(CG.kCGMaximumWindowLevelKey)
    window.setIgnoresMouseEvents_(True)

    view = BlackHoleView.alloc().initWithFrame_(screen)
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)

    view.startAnimation()
