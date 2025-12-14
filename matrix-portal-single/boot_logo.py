"""
Tickertronix Boot Logo (Single Panel 64x32)

Displays a pre-rendered BMP based on the 60x30 PNG, centered on a 64x32
canvas so it does not touch the panel edges. Uses a simple slide-in animation
to avoid boot artifacts and keep init lightweight.
"""

LOGO_PATH = "boot_logo.bmp"
LOGO_WIDTH = 64
LOGO_HEIGHT = 32
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 32


def init_display_hardware():
    """Initialize RGBMatrix display hardware. Returns (display, rgb_core)."""
    import displayio
    import framebufferio
    import rgbmatrix
    import board

    displayio.release_displays()

    rgb = rgbmatrix.RGBMatrix(
        width=MATRIX_WIDTH,
        height=MATRIX_HEIGHT,
        bit_depth=1,
        rgb_pins=[
            board.MTX_R1, board.MTX_G1, board.MTX_B1,
            board.MTX_R2, board.MTX_G2, board.MTX_B2,
        ],
        addr_pins=[
            board.MTX_ADDRA, board.MTX_ADDRB,
            board.MTX_ADDRC, board.MTX_ADDRD,
        ],
        clock_pin=board.MTX_CLK,
        latch_pin=board.MTX_LAT,
        output_enable_pin=board.MTX_OE,
        doublebuffer=False,
    )

    display = framebufferio.FramebufferDisplay(rgb, auto_refresh=True)
    try:
        display.brightness = 0.08
    except Exception:
        pass
    return display, rgb


def show_boot_logo():
    """Display Tickertronix logo immediately. Returns (display, rgb_core)."""
    import displayio
    import time

    try:
        bitmap = displayio.OnDiskBitmap(open(LOGO_PATH, "rb"))
    except Exception as e:
        print(f"[LOGO] Failed to load {LOGO_PATH}: {e}")
        return None, None

    display, rgb_core = init_display_hardware()

    try:
        if bitmap.width != LOGO_WIDTH or bitmap.height != LOGO_HEIGHT:
            print(f"[LOGO] Unexpected size {bitmap.width}x{bitmap.height}; expected {LOGO_WIDTH}x{LOGO_HEIGHT}")
    except Exception:
        pass

    group = displayio.Group()

    try:
        bg_bitmap = displayio.Bitmap(MATRIX_WIDTH, MATRIX_HEIGHT, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0x000000
        group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
    except Exception:
        pass

    logo_x = max(0, (MATRIX_WIDTH - LOGO_WIDTH) // 2)
    logo_y = max(0, (MATRIX_HEIGHT - LOGO_HEIGHT) // 2)
    start_x = -LOGO_WIDTH
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader, x=start_x, y=logo_y)
    group.append(tile_grid)

    display.root_group = group
    try:
        display.refresh()
    except Exception:
        pass

    # Wipe-in / slide from left to center
    try:
        while tile_grid.x < logo_x:
            tile_grid.x = min(tile_grid.x + 4, logo_x)
            try:
                display.refresh()
            except Exception:
                pass
            time.sleep(0.012)
    except Exception as e:
        print("[LOGO] Wipe animation failed:", e)

    print("[LOGO] Tickertronix logo displayed")
    return display, rgb_core
