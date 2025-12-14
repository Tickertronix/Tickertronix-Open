"""
Matrix Portal S3 — Multi-Panel Scrolling Firmware with Orphaned Recovery

- Uses provisioning switch (A1 to GND) and wifi.dat/device_config.json for credentials
- Performs time synchronisation before authenticated requests
- Supports single-line or dual-line scrolling across four chained 64x32 panels
- Handles orphaned devices by displaying recovery/claim instructions
"""

import time
import gc
import ssl
import os
import json
import random
import supervisor

try:
    import board
    import digitalio
except Exception:
    board = None
    digitalio = None

try:
    import wifi
    import socketpool
    import adafruit_requests
except Exception as e:
    raise RuntimeError("Required networking libraries not found: {}".format(e))

try:
    from api_client import LocalHubAPI
except Exception as e:
    raise RuntimeError("api_client.py not found in this folder: {}".format(e))

try:
    import boot_logo
except Exception:
    boot_logo = None

try:
    from secrets import secrets
except Exception:
    secrets = {}

# Display libs
try:
    import displayio
    import framebufferio
    import rgbmatrix
    from adafruit_bitmap_font import bitmap_font
    import adafruit_ticks
except Exception:
    displayio = None
    framebufferio = None
    rgbmatrix = None
    bitmap_font = None
    adafruit_ticks = None

# ---- Panel configuration ----
PANEL_WIDTH = 64
PANEL_HEIGHT = 32
NUM_PANELS = 4
DISPLAY_WIDTH = PANEL_WIDTH * NUM_PANELS
DISPLAY_HEIGHT = PANEL_HEIGHT

# ---- Scrolling behaviour ----
FETCH_INTERVAL = 30        # seconds between refresh attempts (overridden by server)
SCROLL_SPEED = 0.025       # seconds per pixel for single-line mode (lower = faster)
SCROLL_STEP = 1            # pixels per movement
TOP_LINE_SCROLL_SPEED = 0.020    # seconds per pixel for dual-line top row
BOTTOM_LINE_SCROLL_SPEED = 0.030 # seconds per pixel for dual-line bottom row
DUAL_FRAMELOCK_ENABLED = False
DUAL_FRAMELOCK_FPS = 60

# ---- Fonts & layout ----
SINGLE_LINE_FONT_PATH = "fonts/spleen-16x32.bdf"
DUAL_LINE_FONT_PATH = "fonts/spleen-8x16.bdf"
SINGLE_LINE_Y_POS = -6  # center 32px font on 32px panel
TOP_LINE_Y_POS = 0
BOTTOM_LINE_Y_POS = 16
CHUNK_WIDTH_MULTIPLIER = 16
MESSAGE_CHAR_SPACING = 2

# Palette indices
COL_BLACK = 0
COL_WHITE = 1
COL_GREEN = 2
COL_RED = 3

# Brightness guard for multi-panel rig
MAX_BRIGHTNESS_PERCENT = 10

# Globals
_matrix = None
_rgb_core = None
_root_group = None
_bg_palette = None
_scroll_group = None
_top_scroll_group = None
_bottom_scroll_group = None
_single_line_font = None
_dual_line_font = None
_display_mode = "dark"


# ---------------- Wi-Fi & Credentials ----------------
def _load_wifi_dat():
    try:
        with open("wifi.dat", "r") as f:
            data = f.read().strip()
        if ";" in data:
            ssid, pwd = data.split(";", 1)
            ssid = ssid.strip()
            pwd = pwd.strip()
            if ssid:
                print("[WIFI] Loaded wifi.dat for SSID:", ssid)
                return ssid, pwd
    except Exception as e:
        print("[WIFI] No wifi.dat or parse error:", e)
    return None, None


def _get_hardware_id():
    try:
        import binascii
        try:
            mac = wifi.radio.mac_address  # type: ignore[attr-defined]
        except Exception:
            mac = None
        if mac:
            return binascii.hexlify(mac).decode("utf-8").upper()
    except Exception:
        pass
    try:
        import microcontroller
        uid = getattr(microcontroller.cpu, "uid", None)
        if uid:
            import binascii
            return binascii.hexlify(uid).decode("utf-8").upper()
    except Exception:
        pass
    return None


def connect_wifi(max_attempts=5, ssid=None, pwd=None):
    if ssid is None:
        ssid_dat, pwd_dat = _load_wifi_dat()
        if ssid_dat:
            ssid, pwd = ssid_dat, pwd_dat
        else:
            ssid = secrets.get("WIFI_SSID")
    if pwd is None and ssid == secrets.get("WIFI_SSID"):
        pwd = secrets.get("WIFI_PASSWORD")

    if not ssid or not pwd:
        print("[WIFI] No stored Wi-Fi; use provisioning (A1 to GND)")
        return False

    for attempt in range(1, max_attempts + 1):
        try:
            print("[WIFI] Connecting... (attempt {} of {})".format(attempt, max_attempts))
            wifi.radio.connect(ssid, pwd)  # type: ignore[attr-defined]
            print("[WIFI] Connected! IP:", wifi.radio.ipv4_address)  # type: ignore[attr-defined]
            return True
        except Exception as e:
            print("[WIFI] Connect failed:", e)
            time.sleep(2)
    return False


def _a1_switch_closed():
    try:
        if not board or not digitalio:
            return False
        pin = digitalio.DigitalInOut(board.A1)
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.UP
        val = pin.value
        pin.deinit()
        return not val
    except Exception:
        return False


def _load_prov_key_from_config():
    try:
        with open("device_config.json", "r") as f:
            cfg = json.loads(f.read())
        key = (cfg or {}).get("device_key")
        if key and isinstance(key, str) and key.startswith("PROV-"):
            print("[AUTH] Using PROV key from device_config.json")
            return key
    except Exception as e:
        print("[AUTH] No device_config.json or parse error:", e)
    return None


def _ensure_device_key(cfg_path="device_config.json"):
    """
    Load device_key/device_id. Only generate/write when A1 is grounded (provisioning).
    """
    cfg = {}
    try:
        with open(cfg_path, "r") as f:
            cfg = json.loads(f.read()) or {}
    except Exception:
        cfg = {}

    device_id = cfg.get("device_key") or cfg.get("device_id")
    if device_id and isinstance(device_id, str):
        return cfg

    # If A1 is grounded (provisioning), allow generation/write; otherwise, read-only.
    if _a1_switch_closed():
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        rand = "".join(random.choice(alphabet) for _ in range(8))
        device_id = f"PROV-{rand}"
        cfg["device_key"] = device_id
        cfg.setdefault("device_type", "matrix_portal_scroll")
        try:
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)
            print("[HUB] Generated device_key (provisioning):", device_id)
        except Exception as e:
            print("[HUB] Could not persist device_key during provisioning:", e)
    else:
        print("[HUB] No device_key found; run provisioning (A1 to GND) to create one.")

    return cfg


def ensure_credentials(api, prov_key=None) -> bool:
    # Local hub requires no device registration
    return True


# ---------------- Display helpers ----------------
def _init_matrix_once():
    global _matrix, _rgb_core, _root_group, _bg_palette
    global _scroll_group, _top_scroll_group, _bottom_scroll_group
    global _single_line_font, _dual_line_font

    if not displayio or not framebufferio or not rgbmatrix:
        print("[MATRIX] Display libraries not available; skipping visual output")
        return

    already_have_hw = _matrix is not None
    if already_have_hw:
        try:
            if (_matrix.width != DISPLAY_WIDTH) or (_matrix.height != DISPLAY_HEIGHT):
                print("[MATRIX] Existing display size mismatch; reinitializing hardware")
                _matrix = None
                _rgb_core = None
                already_have_hw = False
        except Exception:
            _matrix = None
            _rgb_core = None
            already_have_hw = False

    if already_have_hw and _root_group is not None:
        print("[MATRIX] Display hardware already initialized")
        return

    try:
        if not already_have_hw:
            displayio.release_displays()
            rgb = rgbmatrix.RGBMatrix(
                width=DISPLAY_WIDTH,
                height=DISPLAY_HEIGHT,
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
            _rgb_core = rgb
            _matrix = framebufferio.FramebufferDisplay(rgb, auto_refresh=True)
        else:
            rgb = _rgb_core
            try:
                _matrix.auto_refresh = True
            except Exception:
                pass
        try:
            _matrix.brightness = 0.1
            print("[MATRIX] Set brightness to 10% for power safety")
        except Exception as e:
            print("[MATRIX] Could not set brightness:", e)

        _root_group = displayio.Group()
        _scroll_group = displayio.Group()
        _top_scroll_group = displayio.Group()
        _bottom_scroll_group = displayio.Group()

        bg_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0x000000
        _bg_palette = bg_palette
        _root_group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

        try:
            _single_line_font = bitmap_font.load_font(SINGLE_LINE_FONT_PATH)
            print("[MATRIX] Loaded single-line font:", SINGLE_LINE_FONT_PATH)
        except Exception as e:
            print("[MATRIX] Failed to load single-line font:", e)
            _single_line_font = None

        try:
            _dual_line_font = bitmap_font.load_font(DUAL_LINE_FONT_PATH)
            print("[MATRIX] Loaded dual-line font:", DUAL_LINE_FONT_PATH)
        except Exception as e:
            print("[MATRIX] Failed to load dual-line font:", e)
            _dual_line_font = None

        _root_group.append(_scroll_group)
        _matrix.root_group = _root_group
        print("[MATRIX] Initialized scrolling display {}x{} ({} panels)".format(DISPLAY_WIDTH, DISPLAY_HEIGHT, NUM_PANELS))
    except Exception as e:
        print("[MATRIX] Init error:", e)


def _apply_brightness(brightness_percent):
    try:
        if brightness_percent is None:
            return
        bp = int(brightness_percent)
        if bp < 1:
            bp = 1
        if bp > MAX_BRIGHTNESS_PERCENT:
            print(f"[DISPLAY] Requested brightness {bp}% exceeds cap; limiting to {MAX_BRIGHTNESS_PERCENT}%")
            bp = MAX_BRIGHTNESS_PERCENT
    except Exception:
        return

    try:
        if _matrix and hasattr(_matrix, "brightness"):
            _matrix.brightness = bp / 100.0
            print(f"[DISPLAY] Brightness applied via display: {bp}%")
            return
    except Exception:
        pass

    try:
        if _rgb_core and hasattr(_rgb_core, "brightness"):
            try:
                _rgb_core.brightness = bp / 100.0
            except Exception:
                _rgb_core.brightness = int(255 * bp / 100)
            print(f"[DISPLAY] Brightness applied via RGB core: {bp}%")
            return
    except Exception:
        pass

    print(f"[DISPLAY] Brightness control not available (requested {bp}%).")


def _apply_display_mode(mode):
    global _display_mode
    m = (mode or "dark").lower()
    if m not in ("dark", "lite", "light"):
        m = "dark"
    _display_mode = "lite" if m in ("lite", "light") else "dark"
    if _display_mode == "lite" and NUM_PANELS > 1:
        print("[DISPLAY] Lite mode draws too much power on multi-panel rig; forcing dark mode")
        _display_mode = "dark"
    try:
        if _bg_palette is not None:
            _bg_palette[0] = 0xFFFFFF if _display_mode == "lite" else 0x000000
    except Exception:
        pass


def _clamp(value, low, high):
    try:
        if value < low:
            return low
        if value > high:
            return high
    except Exception:
        return low
    return value


def _effective_fetch_interval(cfg):
    try:
        raw = (cfg or {}).get("update_interval")
        if raw is None:
            raise ValueError
        return _clamp(int(raw), 15, 900)
    except Exception:
        return FETCH_INTERVAL


def _effective_scroll_speed(display_settings):
    try:
        raw = float((display_settings or {}).get("scroll_speed"))
        if raw and raw > 0:
            secs_per_px = 1.0 / raw
            return _clamp(secs_per_px, 0.005, 0.1)
    except Exception:
        pass
    return SCROLL_SPEED


def _cleanup_scroll_groups():
    if _scroll_group is not None:
        try:
            while len(_scroll_group) > 0:
                _scroll_group.pop()
        except Exception:
            pass
    if _top_scroll_group is not None:
        try:
            while len(_top_scroll_group) > 0:
                _top_scroll_group.pop()
        except Exception:
            pass
    if _bottom_scroll_group is not None:
        try:
            while len(_bottom_scroll_group) > 0:
                _bottom_scroll_group.pop()
        except Exception:
            pass


def _measure_text(font, text):
    if not font or not text:
        return 0
    width = 0
    for ch in text:
        g = font.get_glyph(ord(ch))
        if g:
            width += g.width + MESSAGE_CHAR_SPACING
    if width > 0:
        width -= MESSAGE_CHAR_SPACING
    return width


def _draw_text(bm, font, text, x, y, color_idx):
    if not font or not text:
        return
    pen = x
    for ch in text:
        g = font.get_glyph(ord(ch))
        if not g:
            pen += MESSAGE_CHAR_SPACING
            continue
        gw = g.width
        gh = g.height
        dy = getattr(g, "dy", 0)
        for yy in range(gh):
            by = y + yy + dy
            if 0 <= by < bm.height:
                for xx in range(gw):
                    if g.bitmap[xx, yy]:
                        bx = pen + xx
                        if 0 <= bx < bm.width:
                            bm[bx, by] = color_idx
        pen += gw + MESSAGE_CHAR_SPACING


def _show_message(lines, dwell_seconds=0):
    """Display a centered message consisting of strings or (text, color_idx) tuples."""
    if not displayio or not _matrix or not _root_group:
        return

    entries = []
    for line in lines:
        if isinstance(line, tuple):
            text, color_idx = line
        else:
            text, color_idx = line, COL_WHITE
        entries.append((str(text), color_idx))

    font = _dual_line_font or _single_line_font
    if not font:
        print("[DISPLAY] No font available to render message")
        return

    _cleanup_scroll_groups()

    try:
        while len(_root_group) > 1:
            _root_group.pop()
    except Exception:
        pass

    palette = displayio.Palette(4)
    if _display_mode == "lite":
        palette[COL_BLACK] = 0xFFFFFF
        palette[COL_WHITE] = 0x000000
        palette[COL_GREEN] = 0x006600
        palette[COL_RED] = 0x880000
    else:
        palette[COL_BLACK] = 0x000000
        palette[COL_WHITE] = 0xFFFFFF
        palette[COL_GREEN] = 0x00FF00
        palette[COL_RED] = 0xFF0000

    bm = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 4)

    try:
        bbox = font.get_bounding_box()
        line_height = bbox[1] if bbox and bbox[1] > 0 else 16
    except Exception:
        line_height = 16

    total_height = len(entries) * line_height + max(0, len(entries) - 1) * 4
    start_y = max(0, (DISPLAY_HEIGHT - total_height) // 2)

    for idx, (text, color_idx) in enumerate(entries):
        width = _measure_text(font, text)
        x = 0 if width >= DISPLAY_WIDTH else (DISPLAY_WIDTH - width) // 2
        y = start_y + idx * (line_height + 4)
        _draw_text(bm, font, text, x, y, color_idx if 0 <= color_idx < 4 else COL_WHITE)

    tile = displayio.TileGrid(bm, pixel_shader=palette, x=0, y=0)
    _root_group.append(tile)
    try:
        _matrix.refresh()
    except Exception:
        pass

    if dwell_seconds > 0:
        t0 = time.monotonic()
        while time.monotonic() - t0 < dwell_seconds:
            time.sleep(0.1)


# ---------------- Data formatting helpers ----------------
def _combine_ticker_data(stocks, crypto, forex):
    combined = []
    try:
        for it in (stocks or []):
            ticker = it.get("ticker", "?")
            last = float(it.get("tngoLast", 0) or 0)
            chg = float(it.get("prcChange", 0) or 0)
            arrow = "↑" if chg >= 0 else "↓"
            combined.append((ticker, "${:.2f}".format(last), arrow, "{:+.2f}".format(chg), chg >= 0))
        for it in (crypto or []):
            ticker = (it.get("ticker") or "?").upper()
            last = float(it.get("lastPrice", 0) or 0)
            pct = float(it.get("prcChangePct", 0) or 0)
            arrow = "↑" if pct >= 0 else "↓"
            combined.append((ticker, "${:.2f}".format(last), arrow, "{:+.2f}%".format(pct), pct >= 0))
        for it in (forex or []):
            ticker = (it.get("ticker") or "?").upper()
            mid = it.get("mid_price") or "0.0000"
            combined.append((ticker, str(mid), "", "", True))
    except Exception as e:
        print("[DATA] Combine error:", e)
    return combined


def _format_stock_data(stocks):
    formatted = []
    try:
        for it in (stocks or []):
            ticker = it.get("ticker", "?")
            last = float(it.get("tngoLast", 0) or 0)
            chg = float(it.get("prcChange", 0) or 0)
            arrow = "↑" if chg >= 0 else "↓"
            formatted.append((ticker, "${:.2f}".format(last), arrow, "{:+.2f}".format(chg), chg >= 0))
    except Exception as e:
        print("[DATA] Format stock error:", e)
    return formatted


def _format_crypto_data(crypto):
    formatted = []
    try:
        for it in (crypto or []):
            ticker = (it.get("ticker") or "?").upper()
            last = float(it.get("lastPrice", 0) or 0)
            pct = float(it.get("prcChangePct", 0) or 0)
            arrow = "↑" if pct >= 0 else "↓"
            formatted.append((ticker, "${:.2f}".format(last), arrow, "{:+.2f}%".format(pct), pct >= 0))
    except Exception as e:
        print("[DATA] Format crypto error:", e)
    return formatted


def _format_forex_data(forex):
    formatted = []
    try:
        for it in (forex or []):
            ticker = (it.get("ticker") or "?").upper()
            mid = it.get("mid_price") or "0.0000"
            formatted.append((ticker, str(mid), "", "", True))
    except Exception as e:
        print("[DATA] Format forex error:", e)
    return formatted


def _filter_ticker_data_by_source(stocks, crypto, forex, sources):
    combined = []
    try:
        if 'stocks' in (sources or []):
            combined.extend(_format_stock_data(stocks))
        if 'crypto' in (sources or []):
            combined.extend(_format_crypto_data(crypto))
        if 'forex' in (sources or []):
            combined.extend(_format_forex_data(forex))
    except Exception as e:
        print("[DATA] Filter error:", e)
    return combined


# ---------------- Scrolling builders ----------------
def _render_single_line_bitmap_chunk(combined, font, start_index=0, max_width=1024, y_position=None, target_group=None, clear_group=False):
    if not displayio or not _matrix or not font:
        return None, 0, start_index

    n = len(combined or [])
    if n == 0:
        return None, 0, start_index

    if y_position is None:
        y_position = SINGLE_LINE_Y_POS
    if target_group is None:
        target_group = _scroll_group

    char_spacing = 2
    block_spacing = 10
    text_width = 0
    elements = []
    max_ascent = 0

    def add_text(text, color_idx):
        nonlocal text_width, max_ascent
        for ch in text:
            g = font.get_glyph(ord(ch))
            if g:
                elements.append((g, color_idx, text_width))
                text_width += g.width + char_spacing
                asc = g.height + getattr(g, "dy", 0)
                if asc > max_ascent:
                    max_ascent = asc

    i = start_index % n
    placed_any = False
    start_loop = True

    while True:
        ticker, price, arrow, change, is_pos = combined[i]
        arrow_color = COL_GREEN if is_pos else COL_RED
        change_color = arrow_color

        prev_width = text_width
        add_text(ticker, COL_WHITE)
        text_width += 8
        add_text(price, COL_WHITE)
        if arrow:
            text_width += 8
            add_text(arrow, arrow_color)
        if change:
            text_width += 8
            add_text(change, change_color)
        text_width += block_spacing
        placed_any = True

        if text_width > max_width and prev_width > 0:
            elements = [e for e in elements if e[2] < prev_width]
            text_width = prev_width
            break

        i = (i + 1) % n
        if i == start_index and not start_loop:
            break
        start_loop = False
        if text_width >= max_width:
            break

    if text_width <= 0 or not placed_any:
        return None, 0, start_index

    bitmap_height = 16 if y_position in (TOP_LINE_Y_POS, BOTTOM_LINE_Y_POS) else DISPLAY_HEIGHT
    bm = displayio.Bitmap(text_width, bitmap_height, 4)
    palette = displayio.Palette(4)
    if _display_mode == "lite":
        palette[COL_BLACK] = 0xFFFFFF
        palette[COL_WHITE] = 0x000000
        palette[COL_GREEN] = 0x006600
        palette[COL_RED] = 0x880000
    else:
        palette[COL_BLACK] = 0x000000
        palette[COL_WHITE] = 0xFFFFFF
        palette[COL_GREEN] = 0x00FF00
        palette[COL_RED] = 0xFF0000

    vertical_offset = 2 if bitmap_height == 16 else 6
    for g, color_idx, xoff in elements:
        baseline_offset = max_ascent - (g.height + getattr(g, "dy", 0)) + vertical_offset
        for y in range(g.height):
            by = y + baseline_offset
            if 0 <= by < bitmap_height:
                for x in range(g.width):
                    if g.bitmap[x, y]:
                        bx = xoff + x
                        if 0 <= bx < text_width:
                            bm[bx, by] = color_idx

    tile = displayio.TileGrid(bm, pixel_shader=palette, x=DISPLAY_WIDTH, y=y_position)
    if clear_group and target_group is not None:
        while len(target_group) > 0:
            target_group.pop()
    if target_group is not None:
        target_group.append(tile)
    return tile, text_width, i


def _safe_group_remove(group, tile):
    if not group or tile is None:
        return
    try:
        for idx in range(len(group) - 1, -1, -1):
            if group[idx] is tile:
                group.pop(idx)
                break
    except Exception:
        pass


def _build_all_chunks(combined, font, max_width, y_position=None, target_group=None):
    n = len(combined or [])
    if n == 0:
        return [], 0, 0
    chunks = []
    start = 0
    covered = 0
    guard = 0
    total_width = 0
    while covered < n and guard < (n + 5):
        tile, width, nxt = _render_single_line_bitmap_chunk(
            combined,
            font,
            start_index=start,
            max_width=max_width,
            y_position=y_position,
            target_group=target_group,
            clear_group=False,
        )
        if not tile or width <= 0:
            break
        inc = (nxt - start) % n
        if inc == 0:
            inc = max(1, n - covered)
        chunks.append({'tile': tile, 'width': width, 'start': start, 'next': nxt, 'inc': inc})
        covered += inc
        total_width += width
        start = nxt
        guard += 1
    return chunks, covered, total_width


def _scroll_single_line_until_update(combined, fetch_interval, speed, step):
    if not _single_line_font:
        return

    chunk_width = min(DISPLAY_WIDTH * CHUNK_WIDTH_MULTIPLIER, 4096)
    chunks, covered, _cycle_width = _build_all_chunks(
        combined,
        _single_line_font,
        chunk_width,
        SINGLE_LINE_Y_POS,
        _scroll_group,
    )
    if not chunks:
        return

    if _root_group is not None:
        while len(_root_group) > 1:
            _root_group.pop()
        _root_group.append(_scroll_group)

    ci_a = 0
    ci_b = 1 % len(chunks) if len(chunks) > 1 else 0
    tile_a = chunks[ci_a]['tile']
    w_a = chunks[ci_a]['width']
    inc_a = chunks[ci_a]['inc']
    tile_b = chunks[ci_b]['tile'] if len(chunks) > 1 else None
    w_b = chunks[ci_b]['width'] if tile_b else 0
    inc_b = chunks[ci_b]['inc'] if tile_b else 0

    pos = DISPLAY_WIDTH
    if tile_a:
        tile_a.x = pos
    if tile_b:
        tile_b.x = pos + w_a

    step_ms = max(1, int(speed * 1000))
    shown_count = 0
    start_seconds = time.monotonic()
    allow_recycle = True
    pending_shutdown = False

    # Helper for tile removal - inline to avoid nonlocal issues
    def _remove_tile(tile):
        _safe_group_remove(_scroll_group, tile)

    # Handle wrap logic - expanded inline to avoid complex nonlocal
    def _do_wrap():
        # Must return all updated variables since nonlocal is problematic
        _pos, _tile_a, _w_a, _inc_a, _tile_b, _w_b, _inc_b, _shown, _ci_a, _ci_b = pos, tile_a, w_a, inc_a, tile_b, w_b, inc_b, shown_count, ci_a, ci_b

        while _tile_a and (_pos + _w_a) < 0:
            _shown = (_shown + _inc_a) if len(combined) else _shown
            old_tile = _tile_a
            old_width = _w_a
            next_tile = _tile_b
            next_width = _w_b
            next_inc = _inc_b

            _remove_tile(old_tile)
            _tile_b = None
            _w_b = 0
            _inc_b = 0

            if allow_recycle:
                if next_tile:
                    _tile_a = next_tile
                    _w_a = next_width
                    _inc_a = next_inc
                    _pos += old_width
                    _tile_a.x = _pos
                    # Queue next tile inline
                    if len(chunks) > 1:
                        _ci_a = (_ci_a + 1) % len(chunks)
                        _ci_b = (_ci_b + 1) % len(chunks)
                        _tile_b = chunks[_ci_b]['tile']
                        _w_b = chunks[_ci_b]['width']
                        _inc_b = chunks[_ci_b]['inc']
                        if _scroll_group is not None:
                            present = False
                            for t in _scroll_group:
                                if t is _tile_b:
                                    present = True
                                    break
                            if not present:
                                _scroll_group.append(_tile_b)
                        _tile_b.x = _pos + _w_a
                elif len(chunks) == 1:
                    _tile_a = old_tile
                    _w_a = old_width
                    _inc_a = chunks[0]['inc']
                    _pos = DISPLAY_WIDTH
                    _tile_a.x = _pos
                    if _scroll_group is not None:
                        present = False
                        for t in _scroll_group:
                            if t is _tile_a:
                                present = True
                                break
                        if not present:
                            _scroll_group.append(_tile_a)
                    _ci_a = 0
                    _ci_b = 0
                else:
                    _tile_a = None
                    _w_a = 0
                    _inc_a = 0
                    _pos = DISPLAY_WIDTH
            else:
                _tile_a = next_tile
                _w_a = next_width
                _inc_a = next_inc
                if _tile_a:
                    _pos += old_width
                    _tile_a.x = _pos
                else:
                    _pos = DISPLAY_WIDTH
            if not _tile_a:
                break

        return _pos, _tile_a, _w_a, _inc_a, _tile_b, _w_b, _inc_b, _shown, _ci_a, _ci_b

    if adafruit_ticks:
        ticks_ms = adafruit_ticks.ticks_ms
        ticks_diff = adafruit_ticks.ticks_diff
        last_step = ticks_ms()

        while True:
            now = ticks_ms()
            if ticks_diff(now, last_step) >= step_ms:
                if tile_a:
                    pos -= step
                    tile_a.x = pos
                    if tile_b:
                        tile_b.x = pos + w_a
                last_step = now

                # Call wrap handler and unpack results
                pos, tile_a, w_a, inc_a, tile_b, w_b, inc_b, shown_count, ci_a, ci_b = _do_wrap()

            if (not pending_shutdown and len(combined) and shown_count >= len(combined)
                    and (time.monotonic() - start_seconds) >= fetch_interval):
                pending_shutdown = True
                allow_recycle = False
                # Drop tile_b inline
                if tile_b:
                    _remove_tile(tile_b)
                    tile_b = None
                    w_b = 0
                    inc_b = 0

            if pending_shutdown and tile_a is None and tile_b is None:
                if _scroll_group is not None:
                    while len(_scroll_group):
                        _scroll_group.pop()
                return

            time.sleep(0.001)
    else:
        step_interval = step_ms / 1000.0
        last_step = time.monotonic()

        while True:
            now = time.monotonic()
            if (now - last_step) >= step_interval:
                if tile_a:
                    pos -= step
                    tile_a.x = pos
                    if tile_b:
                        tile_b.x = pos + w_a
                last_step = now

                # Call wrap handler and unpack results
                pos, tile_a, w_a, inc_a, tile_b, w_b, inc_b, shown_count, ci_a, ci_b = _do_wrap()

            if (not pending_shutdown and len(combined) and shown_count >= len(combined)
                    and (time.monotonic() - start_seconds) >= fetch_interval):
                pending_shutdown = True
                allow_recycle = False
                # Drop tile_b inline
                if tile_b:
                    _remove_tile(tile_b)
                    tile_b = None
                    w_b = 0
                    inc_b = 0

            if pending_shutdown and tile_a is None and tile_b is None:
                if _scroll_group is not None:
                    while len(_scroll_group):
                        _scroll_group.pop()
                return

            time.sleep(0.001)


def _scroll_dual_lines_until_update(top_combined, bottom_combined, fetch_interval, step):
    if not _dual_line_font:
        return

    chunk_width = min(DISPLAY_WIDTH * CHUNK_WIDTH_MULTIPLIER, 4096)
    top_chunks, _, top_cycle_width = _build_all_chunks(
        top_combined,
        _dual_line_font,
        chunk_width,
        TOP_LINE_Y_POS,
        _top_scroll_group,
    )
    bottom_chunks, _, bottom_cycle_width = _build_all_chunks(
        bottom_combined,
        _dual_line_font,
        chunk_width,
        BOTTOM_LINE_Y_POS,
        _bottom_scroll_group,
    )
    if not top_chunks or not bottom_chunks:
        return

    if _root_group is not None:
        while len(_root_group) > 1:
            _root_group.pop()
        _root_group.append(_top_scroll_group)
        _root_group.append(_bottom_scroll_group)

    top_total = len(top_combined)
    bottom_total = len(bottom_combined)
    top_interval_ms = max(1, int(TOP_LINE_SCROLL_SPEED * 1000))
    bottom_interval_ms = max(1, int(BOTTOM_LINE_SCROLL_SPEED * 1000))

    def init_line(name, chunks, group, total_items, interval_ms, cycle_width):
        ci_a = 0
        ci_b = 1 % len(chunks) if len(chunks) > 1 else 0
        tile_a = chunks[ci_a]['tile']
        w_a = chunks[ci_a]['width']
        inc_a = chunks[ci_a]['inc']
        tile_b = chunks[ci_b]['tile'] if len(chunks) > 1 else None
        w_b = chunks[ci_b]['width'] if tile_b else 0
        inc_b = chunks[ci_b]['inc'] if tile_b else 0
        pos = DISPLAY_WIDTH
        if tile_a:
            tile_a.x = pos
        if tile_b:
            tile_b.x = pos + w_a
        return {
            'name': name,
            'chunks': chunks,
            'group': group,
            'ci_a': ci_a,
            'ci_b': ci_b,
            'tile_a': tile_a,
            'tile_b': tile_b,
            'w_a': w_a,
            'w_b': w_b,
            'inc_a': inc_a,
            'inc_b': inc_b,
            'pos': pos,
            'shown': 0,
            'total': total_items,
            'allow_recycle': True,
            'blank': False,
            'interval_ms': interval_ms,
            'interval_sec': interval_ms / 1000.0,
            'cycle_width': cycle_width if cycle_width > 0 else DISPLAY_WIDTH,
        }

    top_line = init_line('top', top_chunks, _top_scroll_group, top_total, top_interval_ms, top_cycle_width)
    bottom_line = init_line('bottom', bottom_chunks, _bottom_scroll_group, bottom_total, bottom_interval_ms, bottom_cycle_width)

    def remove_tile(line, tile):
        _safe_group_remove(line['group'], tile)

    def drop_tile_b(line):
        if line['tile_b']:
            remove_tile(line, line['tile_b'])
            line['tile_b'] = None
            line['w_b'] = 0
            line['inc_b'] = 0

    def queue_next_tile(line):
        if not line['allow_recycle'] or len(line['chunks']) <= 1:
            line['tile_b'] = None
            line['w_b'] = 0
            line['inc_b'] = 0
            return
        line['ci_a'] = (line['ci_a'] + 1) % len(line['chunks'])
        line['ci_b'] = (line['ci_b'] + 1) % len(line['chunks'])
        tile_b = line['chunks'][line['ci_b']]['tile']
        line['tile_b'] = tile_b
        line['w_b'] = line['chunks'][line['ci_b']]['width']
        line['inc_b'] = line['chunks'][line['ci_b']]['inc']
        if line['group'] is not None:
            present = False
            for t in line['group']:
                if t is tile_b:
                    present = True
                    break
            if not present:
                line['group'].append(tile_b)
        tile_b.x = line['pos'] + line['w_a']

    def handle_wrap(line):
        while line['tile_a'] and (line['pos'] + line['w_a']) < 0:
            if line['total']:
                line['shown'] = line['shown'] + line['inc_a']
            old_tile = line['tile_a']
            old_width = line['w_a']
            next_tile = line['tile_b']
            next_width = line['w_b']
            next_inc = line['inc_b']

            remove_tile(line, old_tile)
            line['tile_b'] = None
            line['w_b'] = 0
            line['inc_b'] = 0

            if line['allow_recycle']:
                if next_tile:
                    line['tile_a'] = next_tile
                    line['w_a'] = next_width
                    line['inc_a'] = next_inc
                    line['pos'] += old_width
                    line['tile_a'].x = line['pos']
                    line['blank'] = False
                    queue_next_tile(line)
                elif len(line['chunks']) == 1:
                    line['tile_a'] = old_tile
                    line['w_a'] = old_width
                    line['inc_a'] = line['chunks'][0]['inc']
                    line['pos'] = DISPLAY_WIDTH
                    line['tile_a'].x = line['pos']
                    if line['group'] is not None:
                        present = False
                        for t in line['group']:
                            if t is line['tile_a']:
                                present = True
                                break
                        if not present:
                            line['group'].append(line['tile_a'])
                    line['ci_a'] = 0
                    line['ci_b'] = 0
                    line['blank'] = False
                else:
                    line['tile_a'] = None
                    line['w_a'] = 0
                    line['inc_a'] = 0
                    line['pos'] = DISPLAY_WIDTH
                    line['blank'] = True
            else:
                line['tile_a'] = next_tile
                line['w_a'] = next_width
                line['inc_a'] = next_inc
                if line['tile_a']:
                    line['pos'] += old_width
                    line['tile_a'].x = line['pos']
                    line['blank'] = False
                else:
                    line['pos'] = DISPLAY_WIDTH
                    line['blank'] = True
            if not line['tile_a']:
                line['blank'] = True
                break

    def cycle_time(line):
        pixels = line['cycle_width']
        if pixels <= 0:
            pixels = DISPLAY_WIDTH
        return (pixels / max(1, step)) * (line['interval_ms'] / 1000.0)

    top_line['cycle_time'] = cycle_time(top_line)
    bottom_line['cycle_time'] = cycle_time(bottom_line)

    if top_line['cycle_time'] >= bottom_line['cycle_time']:
        longer_line = top_line
        shorter_line = bottom_line
    else:
        longer_line = bottom_line
        shorter_line = top_line

    pending_shutdown = False
    short_line_blocked = False
    long_line_blocked = False
    handoff_threshold = max(DISPLAY_WIDTH // 2, step * 64)
    start_seconds = time.monotonic()

    if adafruit_ticks:
        ticks_ms = adafruit_ticks.ticks_ms
        ticks_diff = adafruit_ticks.ticks_diff
        now_ticks = ticks_ms()
        top_line['last_step'] = now_ticks
        bottom_line['last_step'] = now_ticks

        def should_step(line):
            now_local = ticks_ms()
            if ticks_diff(now_local, line['last_step']) >= line['interval_ms']:
                line['last_step'] = now_local
                return True
            return False
    else:
        now_secs = time.monotonic()
        top_line['last_step'] = now_secs
        bottom_line['last_step'] = now_secs

        def should_step(line):
            now_local = time.monotonic()
            if (now_local - line['last_step']) >= line['interval_sec']:
                line['last_step'] = now_local
                return True
            return False

    while True:
        if should_step(top_line):
            if top_line['tile_a']:
                top_line['pos'] -= step
                top_line['tile_a'].x = top_line['pos']
                if top_line['tile_b']:
                    top_line['tile_b'].x = top_line['pos'] + top_line['w_a']
            handle_wrap(top_line)

        if should_step(bottom_line):
            if bottom_line['tile_a']:
                bottom_line['pos'] -= step
                bottom_line['tile_a'].x = bottom_line['pos']
                if bottom_line['tile_b']:
                    bottom_line['tile_b'].x = bottom_line['pos'] + bottom_line['w_a']
            handle_wrap(bottom_line)

        top_ready = (top_line['total'] == 0) or (top_line['shown'] >= top_line['total'])
        bottom_ready = (bottom_line['total'] == 0) or (bottom_line['shown'] >= bottom_line['total'])
        if (not pending_shutdown and top_ready and bottom_ready
                and (time.monotonic() - start_seconds) >= fetch_interval):
            pending_shutdown = True

        if pending_shutdown:
            if not short_line_blocked:
                long_remaining = 0
                if longer_line['tile_a']:
                    long_remaining = longer_line['pos'] + longer_line['w_a']
                if long_remaining <= handoff_threshold:
                    shorter_line['allow_recycle'] = False
                    drop_tile_b(shorter_line)
                    short_line_blocked = True
            if short_line_blocked and not long_line_blocked and shorter_line['blank']:
                longer_line['allow_recycle'] = False
                drop_tile_b(longer_line)
                long_line_blocked = True
            if shorter_line['blank'] and longer_line['blank']:
                if _top_scroll_group is not None:
                    while len(_top_scroll_group):
                        _top_scroll_group.pop()
                if _bottom_scroll_group is not None:
                    while len(_bottom_scroll_group):
                        _bottom_scroll_group.pop()
                return

        time.sleep(0.001)


# ---------------- Orphaned handling ----------------
def _handle_orphaned_state(api, device_key):
    if not device_key:
        device_key = "UNKNOWN"

    _show_message([
        ("DEVICE ORPHANED", COL_RED),
        (f"ID: {device_key}", COL_WHITE),
        ("CHECK APP", COL_WHITE),
    ], dwell_seconds=2)

    _show_message([
        ("RECOVERY", COL_WHITE),
        ("IN PROGRESS", COL_WHITE),
        ("PLEASE WAIT", COL_WHITE),
    ])

    if not api.recover_device():
        _show_message([
            ("RECOVERY FAILED", COL_RED),
            (f"ID: {device_key}", COL_WHITE),
            ("RETRYING...", COL_WHITE),
        ], dwell_seconds=30)
        return

    claim_code = api.get_last_claim_code()
    if claim_code:
        _show_message([
            ("CLAIM CODE", COL_GREEN),
            (str(claim_code), COL_WHITE),
            ("ENTER IN APP", COL_WHITE),
        ])
    else:
        _show_message([
            ("CHECK MOBILE APP", COL_WHITE),
            ("FOR CLAIM INSTRUCTIONS", COL_WHITE),
            (device_key, COL_WHITE),
        ])

    while True:
        time.sleep(15)
        try:
            test_raw = api.get_ticker_data() or {}
        except Exception as e:
            print("[MAIN] Error checking claim status:", e)
            continue
        if not test_raw.get('orphaned'):
            print("[MAIN] Device no longer orphaned - resuming normal operation")
            return


# ---------------- Main ----------------
def main():
    print("=" * 50)
    print("[MAIN] CODE VERSION: 2025-10-06-SCROLL")
    print("=" * 50)
    global _matrix, _rgb_core
    if boot_logo:
        try:
            boot_display, boot_rgb_core = boot_logo.show_boot_logo()
            _matrix = boot_display or _matrix
            _rgb_core = boot_rgb_core or _rgb_core
        except Exception as e:
            print("[BOOT] Boot logo failed:", e)

    def _has_wifi_file():
        try:
            with open("wifi.dat", "r") as f:
                return bool(f.read().strip())
        except Exception:
            return False

    def _has_hub_config():
        try:
            with open("device_config.json", "r") as f:
                cfg = json.loads(f.read() or "{}")
                return bool(cfg.get("hub_base_url"))
        except Exception:
            return False

    needs_provision = not (_has_wifi_file() and _has_hub_config())

    if _a1_switch_closed():
        needs_provision = True
        print("[MODE] A1 grounded: forcing provisioning")

    if needs_provision:
        print("[MODE] Starting provisioning portal (missing Wi-Fi or hub URL)…")
        try:
            import wifimgr
            wifimgr.start_provisioning()
        except Exception as e:
            print("[MODE] Provisioning launcher failed:", e)
        while True:
            time.sleep(1)

    if not connect_wifi():
        print("[MAIN] No Wi-Fi. Starting provisioning portal…")
        try:
            import wifimgr
            wifimgr.start_provisioning()
        except Exception as e:
            print("[MAIN] Provisioning failed:", e)
        return

    pool = socketpool.SocketPool(wifi.radio)  # type: ignore[attr-defined]
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    # Time sync before API calls
    try:
        from time_sync import sync_time, validate_time
        print("[MAIN] Synchronizing system time...")
        is_valid, timestamp, year = validate_time()
        print(f"[MAIN] Current time status - Valid: {is_valid}, Year: {year}")
        print("[MAIN] Forcing time synchronization...")
        if sync_time(pool, force_ntp=True):
            is_valid, timestamp, year = validate_time()
            print(f"[MAIN] After sync - Valid: {is_valid}, Year: {year}")
        else:
            print("[MAIN] Warning: Time synchronization failed, HMAC may fail")
    except Exception as e:
        print(f"[MAIN] Time sync error: {e}")

    # Ensure device_key/device_id exists
    cfg = _ensure_device_key()

    api = LocalHubAPI(session)
    if not ensure_credentials(api):
        print("[MAIN] Missing credentials/config; provision via A1 switch")
        return

    _init_matrix_once()

    hb_interval = 120  # seconds between heartbeats
    last_hb = 0
    settings_cache_interval = 300
    last_settings_fetch = 0
    cached_display_settings = None
    cached_device_config = None

    while True:
        now = time.monotonic()
        if now - last_hb > hb_interval:
            try:
                print("[API] Sending heartbeat...")
            except Exception:
                pass
            if api.send_heartbeat():
                try:
                    print("[API] Heartbeat OK")
                except Exception:
                    pass
                if getattr(api, "should_refresh_settings", False):
                    print("[API] Hub reports settings changed; will refresh now.")
                    cached_display_settings = None
                    last_settings_fetch = 0
            else:
                try:
                    print("[API] Heartbeat failed")
                except Exception:
                    pass
            last_hb = now

        _cleanup_scroll_groups()
        gc.collect()

        if (now - last_settings_fetch > settings_cache_interval) or cached_display_settings is None:
            print("[API] Refreshing settings cache...")
            cached_display_settings = api.get_display_settings() or {}
            cached_device_config = api.get_device_config() or {}
            last_settings_fetch = now

        display_settings = cached_display_settings or {}
        device_config = cached_device_config or {}

        try:
            _apply_brightness(display_settings.get('brightness'))
            _apply_display_mode(display_settings.get('display_mode'))
        except Exception:
            pass

        eff_interval = _effective_fetch_interval(display_settings)
        eff_speed = _effective_scroll_speed(display_settings)

        try:
            print(f"[API] Fetching prices (interval {eff_interval}s)...")
        except Exception:
            pass

        raw = api.get_ticker_data() or {}
        if raw.get('orphaned'):
            device_key = raw.get('device_key') or api.device_key
            _handle_orphaned_state(api, device_key)
            continue

        stocks, crypto, forex = api.parse_ticker_data(raw)
        try:
            print(f"[API] Tickers -> stocks:{len(stocks)} crypto:{len(crypto)} forex:{len(forex)}")
        except Exception:
            pass
        if not stocks and not crypto and not forex:
            _show_message([
                ("NO DATA", COL_WHITE),
                ("CHECK APP", COL_WHITE),
            ], dwell_seconds=10)
            continue

        scroll_mode = (display_settings.get('scroll_mode') or 'single').lower()
        if scroll_mode == 'dual':
            top_sources = display_settings.get('top_sources') or ['stocks']
            bottom_sources = display_settings.get('bottom_sources') or ['crypto', 'forex']
            top_combined = _filter_ticker_data_by_source(stocks, crypto, forex, top_sources)
            bottom_combined = _filter_ticker_data_by_source(stocks, crypto, forex, bottom_sources)
            if not top_combined or not bottom_combined:
                _show_message([
                    ("INSUFFICIENT DATA", COL_RED),
                    ("FOR DUAL MODE", COL_WHITE),
                ], dwell_seconds=8)
                continue
            _scroll_dual_lines_until_update(top_combined, bottom_combined, eff_interval, SCROLL_STEP)
        else:
            combined = _combine_ticker_data(stocks, crypto, forex)
            if not combined:
                _show_message([
                    ("NO DATA", COL_WHITE),
                    ("CHECK SOURCES", COL_WHITE),
                ], dwell_seconds=8)
                continue
            _scroll_single_line_until_update(combined, fetch_interval=eff_interval, speed=eff_speed, step=SCROLL_STEP)


if __name__ == "__main__":
    main()
