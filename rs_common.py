"""Shared RealSense helpers for the Braccio vision scripts."""
import numpy as np

DEPTH_W, DEPTH_H, FPS = 848, 480, 30
COLOR_W, COLOR_H = 640, 480


def start_pipeline(color=True, depth=True):
    """Start the D435. Returns (rs, pipeline, profile, depth_scale)."""
    import pyrealsense2 as rs

    ctx = rs.context()
    devs = ctx.query_devices()
    if len(devs) == 0:
        raise SystemExit("No RealSense camera found. Check the cable (blue USB 3 port) and run `rs-enumerate-devices`.")
    dev = devs[0]
    name = dev.get_info(rs.camera_info.name)
    serial = dev.get_info(rs.camera_info.serial_number)
    fw = dev.get_info(rs.camera_info.firmware_version)
    usb = dev.get_info(rs.camera_info.usb_type_descriptor) if dev.supports(rs.camera_info.usb_type_descriptor) else "?"
    print(f"Camera: {name}  serial {serial}  firmware {fw}  USB {usb}")
    if not usb.startswith("3"):
        print("!! WARNING: camera is on USB 2. Use a blue USB 3 port and a USB 3 cable, "
              "or depth will be limited / unstable.")

    pipe = rs.pipeline()
    cfg = rs.config()
    cfg.enable_device(serial)
    if depth:
        cfg.enable_stream(rs.stream.depth, DEPTH_W, DEPTH_H, rs.format.z16, FPS)
    if color:
        cfg.enable_stream(rs.stream.color, COLOR_W, COLOR_H, rs.format.bgr8, FPS)
    profile = pipe.start(cfg)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    # Make sure the IR pattern projector is on (better depth on plain tables)
    if depth_sensor.supports(rs.option.emitter_enabled):
        depth_sensor.set_option(rs.option.emitter_enabled, 1)
    # Let auto-exposure settle
    for _ in range(30):
        pipe.wait_for_frames()
    return rs, pipe, profile, depth_scale


def colorize_depth(depth_m, max_m=1.5):
    """Depth in metres -> BGR image for display (near = warm, far = cool, 0 = black)."""
    import cv2
    d = np.clip(depth_m / max_m, 0, 1)
    img = cv2.applyColorMap((255 - d * 255).astype(np.uint8), cv2.COLORMAP_JET)
    img[depth_m <= 0] = 0
    return img
