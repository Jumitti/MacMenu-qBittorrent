import math
import random

from Cocoa import NSApplication
from Cocoa import (
    NSApplication, NSWindow, NSColor, NSView,
    NSBackingStoreBuffered, NSScreen, NSGraphicsContext
)
from PyObjCTools import AppHelper
from Quartz import CoreGraphics as CG


class ConfettiView(NSView):
    def __init__(self):
        self.confettis = []

    def drawRect_(self, rect):
        ctx = NSGraphicsContext.currentContext().CGContext()
        CG.CGContextClearRect(ctx, rect)

        for conf in self.confettis:
            color = conf["color"].colorWithAlphaComponent_(conf["alpha"])
            color.set()

            CG.CGContextSaveGState(ctx)
            CG.CGContextTranslateCTM(ctx, conf["x"] + conf["size"]/2, conf["y"] + conf["size"]/2)
            CG.CGContextRotateCTM(ctx, math.radians(conf["angle"]))
            CG.CGContextTranslateCTM(ctx, -conf["size"]/2, -conf["size"]/2)

            CG.CGContextFillRect(ctx, ((0, 0), (conf["size"], conf["size"])))
            CG.CGContextRestoreGState(ctx)

    def startAnimation(self):
        screen_h = int(self.frame().size.height)
        screen_w = int(self.frame().size.width)

        cx = screen_w // 2
        cy = screen_h // 1.5

        self.confettis = []
        for _ in range(2500):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(6, 20)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            self.confettis.append({
                "x": cx,
                "y": cy,
                "vx": vx,
                "vy": vy,
                "angle": random.uniform(0, 360),
                "rotation_speed": random.uniform(-10, 10),
                "size": random.uniform(4, 12),
                "alpha": 1.0,
                "color": random.choice([
                    NSColor.redColor(),
                    NSColor.blueColor(),
                    NSColor.greenColor(),
                    NSColor.yellowColor(),
                    NSColor.orangeColor(),
                    NSColor.purpleColor()
                ])
            })

        self.animate()

    def animate(self):
        gravity = 0.3
        new_confettis = []

        for conf in self.confettis:
            conf["x"] += conf["vx"] + random.uniform(-5, 5)
            conf["y"] += conf["vy"]
            conf["vy"] -= gravity
            conf["angle"] += conf["rotation_speed"]
            conf["alpha"] -= 0.015

            if conf["y"] > 0 and conf["alpha"] > 0:
                new_confettis.append(conf)

        self.confettis = new_confettis
        self.setNeedsDisplay_(True)

        if self.confettis:
            AppHelper.callLater(0.03, self.animate)
        else:
            self.window().orderOut_(None)
            AppHelper.stopEventLoop()


def ee1():
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

    view = ConfettiView.alloc().initWithFrame_(screen)
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)

    view.startAnimation()

    AppHelper.runEventLoop()


