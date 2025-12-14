"""
Single Matrix Display — Matrix Portal S3 (64x32)

Shows one asset at a time (stocks, crypto, forex) on a single 64×32 panel
and cycles through them with a hard cut (minimal flicker) using a 4‑color
palette (black, white, green, red). Reuses provisioning, Wi‑Fi, and API client
from the scrolling build.

User options (local constants below):
- ITEM_DWELL_SEC: seconds per asset (later can come from API item_dwell)
- ASSET_ORDER: sequence for asset categories
- CRYPTO_COMPACT_LABELS: use 1.2k/1.2M abbreviations when needed
"""

import time
import gc
import ssl
import os
import json
import supervisor
import random
import random

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

# ---- Panel configuration (single 64x32) ----
PANEL_WIDTH = 64
PANEL_HEIGHT = 32
NUM_PANELS = 1
DISPLAY_WIDTH = PANEL_WIDTH * NUM_PANELS
DISPLAY_HEIGHT = PANEL_HEIGHT

# ---- Behavior ----
FETCH_INTERVAL_DEFAULT = 300  # seconds between data refreshes
ITEM_DWELL_SEC_DEFAULT = 2.5  # seconds to show each asset
ITEM_DWELL_RANGE = (1.0, 30.0)

# Asset order (local override until API provides asset_order)
ASSET_ORDER = ['stocks', 'crypto', 'forex']
CRYPTO_COMPACT_LABELS = True

# ---- Fonts & layout ----
FONT_PATH = "fonts/6x10.bdf"  # Smaller font for 3-line layout
TOP_Y = 2          # Ticker symbol line (shifted down 1px)
MIDDLE_Y = 12      # Price line (shifted down 1px)
BOTTOM_Y = 22      # Change line
CHAR_SPACING = 1   # Tighter spacing for smaller font
LINE_VOFF = 1      # Small baseline shift

# Palette indices
COL_BLACK = 0
COL_WHITE = 1
COL_GREEN = 2
COL_RED = 3

# Globals
_matrix = None
_root_group = None
_rgb_core = None  # underlying RGBMatrix for brightness control when available
_font8 = None
_refresh_ok = 0
_refresh_errs = 0
_bg_palette = None  # palette for background layer (to switch dark/lite)
_display_mode = 'dark'


# ---------------- Wi‑Fi & Credentials ----------------
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
        mac = None
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
        print("[WIFI] No stored Wi‑Fi; use provisioning (A1 to GND)")
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
        v = pin.value
        pin.deinit()
        return not v
    except Exception:
        return False


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

    if _a1_switch_closed():
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        rand = "".join(random.choice(alphabet) for _ in range(8))
        device_id = f"PROV-{rand}"
        cfg["device_key"] = device_id
        cfg.setdefault("device_type", "matrix_portal_single")
        try:
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)
            print("[HUB] Generated device_key (provisioning):", device_id)
        except Exception as e:
            print("[HUB] Could not persist device_key during provisioning:", e)
    else:
        print("[HUB] No device_key found; run provisioning (A1 to GND) to create one.")

    return cfg


def ensure_credentials(api: LocalHubAPI, prov_key=None) -> bool:
    # Local hub requires no credentials
    return True


# ---------------- Display helpers ----------------
def _init_matrix_once():
    global _matrix, _root_group, _font8, _bg_palette, _rgb_core
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
        _root_group = displayio.Group()
        # Background
        try:
            bm = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
            pal = displayio.Palette(1)
            pal[0] = 0x000000
            _bg_palette = pal
            _root_group.append(displayio.TileGrid(bm, pixel_shader=pal))
        except Exception:
            pass

        # Load font once
        try:
            _font8 = bitmap_font.load_font(FONT_PATH)
            print("[MATRIX] Loaded font:", FONT_PATH)
        except Exception as e:
            print("[MATRIX] Failed to load font:", e)
            _font8 = None

        _matrix.root_group = _root_group
        print("[MATRIX] Initialized display {}x{} ({} panel)".format(DISPLAY_WIDTH, DISPLAY_HEIGHT, NUM_PANELS))
    except Exception as e:
        print("[MATRIX] Init error:", e)


def _apply_brightness(brightness_percent):
    """Apply brightness to display, best-effort across environments."""
    try:
        if brightness_percent is None:
            return
        bp = int(brightness_percent)
        if bp < 1:
            bp = 1
        if bp > 100:
            bp = 100
    except Exception:
        return

    # Preferred: normalized float on display or core
    try:
        if _matrix and hasattr(_matrix, 'brightness'):
            _matrix.brightness = bp / 100.0
            print(f"[DISPLAY] Brightness applied via display: {bp}%")
            return
    except Exception:
        pass
    try:
        if _rgb_core and hasattr(_rgb_core, 'brightness'):
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
    """Set background and text palette mapping for dark/lite modes."""
    global _display_mode
    m = (mode or 'dark').lower()
    if m not in ('dark', 'lite', 'light'):
        m = 'dark'
    _display_mode = 'lite' if m in ('lite', 'light') else 'dark'
    try:
        if _bg_palette is not None:
            _bg_palette[0] = 0xFFFFFF if _display_mode == 'lite' else 0x000000
    except Exception:
        pass


def _effective_fetch_interval(cfg):
    try:
        v = int((cfg or {}).get("update_interval"))
        if v < 15:
            v = 15
        if v > 900:
            v = 900
        return v
    except Exception:
        return FETCH_INTERVAL_DEFAULT


def _effective_item_dwell(display_settings):
    try:
        raw = display_settings.get('dwell_seconds')
        if raw is None:
            raise ValueError
        v = float(raw)
        lo, hi = ITEM_DWELL_RANGE
        if v < lo:
            v = lo
        if v > hi:
            v = hi
        return v
    except Exception:
        return ITEM_DWELL_SEC_DEFAULT


def _effective_asset_order(display_settings):
    try:
        ao = display_settings.get('asset_order')
        if not ao:
            return ASSET_ORDER
        if isinstance(ao, str):
            lst = [s.strip() for s in ao.split(',') if s.strip()]
            return lst or ASSET_ORDER
        if isinstance(ao, list):
            lst = [str(s).strip() for s in ao if str(s).strip()]
            return lst or ASSET_ORDER
        return ASSET_ORDER
    except Exception:
        return ASSET_ORDER


def _measure_text(font, text):
    if not font or not text:
        return 0
    w = 0
    for ch in text:
        g = font.get_glyph(ord(ch))
        if g:
            w += g.width + CHAR_SPACING
    if w > 0:
        w -= CHAR_SPACING
    return w


def _draw_text(bm, font, text, x, y, color_idx):
    if not font or not text:
        return x
    px = x
    for ch in text:
        g = font.get_glyph(ord(ch))
        if not g:
            px += CHAR_SPACING
            continue
        gw = g.width
        gh = g.height
        dy = getattr(g, 'dy', 0)
        # Baseline adjustment: small positive offset for centering
        base = y + LINE_VOFF
        for yy in range(gh):
            by = base + yy + dy
            if 0 <= by < bm.height:
                for xx in range(gw):
                    if g.bitmap[xx, yy]:
                        bx = px + xx
                        if 0 <= bx < bm.width:
                            bm[bx, by] = color_idx
        px += gw + CHAR_SPACING
    return px


def _format_price_stock(val, max_width, font):
    # Try with $ and 2 decimals
    s = "$" + ("{:.2f}".format(val))
    if _measure_text(font, s) <= max_width:
        return s
    # Drop $ if too wide
    s = "{:.2f}".format(val)
    if _measure_text(font, s) <= max_width:
        return s
    # Drop decimals
    s = str(int(val))
    if _measure_text(font, s) <= max_width:
        return s
    # Abbreviate
    if val >= 1_000_000:
        s = "{:.1f}M".format(val / 1_000_000.0)
    elif val >= 1_000:
        s = "{:.1f}k".format(val / 1_000.0)
    else:
        s = str(int(val))
    return s


def _format_price_crypto(val, max_width, font):
    if CRYPTO_COMPACT_LABELS and val >= 1000:
        if val >= 1_000_000:
            s = "{:.1f}M".format(val / 1_000_000.0)
        else:
            s = "{:.1f}k".format(val / 1_000.0)
        if _measure_text(font, s) <= max_width:
            return s
    # Otherwise try $ with 2 decimals
    s = "$" + ("{:.2f}".format(val))
    if _measure_text(font, s) <= max_width:
        return s
    # Try without $ then fewer decimals
    s = "{:.2f}".format(val)
    if _measure_text(font, s) <= max_width:
        return s
    s = "{:.1f}".format(val)
    if _measure_text(font, s) <= max_width:
        return s
    return str(int(val))


def _format_change_abs(val):
    try:
        return ("↑" if val >= 0 else "↓"), ("{:+.2f}".format(val))
    except Exception:
        return "", ""


def _format_change_pct(val):
    try:
        return ("↑" if val >= 0 else "↓"), ("{:+.2f}%".format(val))
    except Exception:
        return "", ""


def _create_orphaned_card(device_key):
    """Create a card showing the device is orphaned."""
    # Extract last part of device key (e.g., "4EX7" from "MTX-5ITN-4EX7")
    short_key = device_key.split('-')[-1] if '-' in device_key else device_key[-4:]
    return _create_message_card("ORPHANED", f"ID:{short_key}", "USE APP", COL_RED)

def _create_recovery_card():
    """Create a card showing recovery is in progress."""
    return _create_message_card("RECOVERY", "WAIT...", "", COL_WHITE)

def _create_recovery_success_card():
    """Create a card showing recovery was successful."""
    return _create_message_card("SUCCESS", "READY", "", COL_GREEN)

def _create_recovery_failed_card(device_key):
    """Create a card showing recovery failed with device info."""
    short_key = device_key.split('-')[-1] if '-' in device_key else device_key[-4:]
    return _create_message_card("FAILED", f"ID:{short_key}", "USE APP", COL_RED)

def _create_claim_instruction_card(device_key):
    """Create a card showing claim instructions."""
    short_key = device_key.split('-')[-1] if '-' in device_key else device_key[-4:]
    return _create_message_card("LINK ME", f"ID:{short_key}", "USE APP", COL_GREEN)

def _create_claim_code_card(claim_code):
    """Create a card showing the claim code."""
    print(f"[CARD] Creating claim code card with: '{claim_code}'")
    # Truncate claim code if too long (show first 6 characters)
    short_code = claim_code[:6] if len(claim_code) > 6 else claim_code
    print(f"[CARD] Short code: '{short_code}'")

    card = _create_message_card("CLAIM", f"{short_code}", "USE APP", COL_GREEN)
    print(f"[CARD] Claim code card created: {card}")
    return card

def _create_message_card(line1, line2, line3, color):
    """Create a generic 3-line message card."""
    print(f"[CARD] Creating message card: '{line1}', '{line2}', '{line3}', color={color}")

    if not displayio or not _matrix or not _font8:
        print("[CARD] Missing display components - displayio, matrix, or font")
        return None

    try:
        # Create bitmap and palette
        bm = displayio.Bitmap(64, 32, 4)
        print(f"[CARD] Bitmap created: {bm}")

        # Always create a fresh palette to avoid issues
        pal = displayio.Palette(4)
        pal[COL_BLACK] = 0x000000
        pal[COL_WHITE] = 0xFFFFFF
        pal[COL_GREEN] = 0x00FF00
        pal[COL_RED] = 0xFF0000
        print(f"[CARD] Palette created: {pal}")

        # Clear background
        for y in range(32):
            for x in range(64):
                bm[x, y] = COL_BLACK

        # Draw lines (centered, with bounds checking)
        if line1 and line1.strip():
            # Truncate text if it's too long for display
            max_chars = 10  # Approximate max characters for 6px font on 64px width
            display_line1 = line1[:max_chars] if len(line1) > max_chars else line1
            w1 = _measure_text(_font8, display_line1)
            x1 = max(0, min(64 - w1, 32 - (w1 // 2)))  # Ensure it fits within bounds
            _draw_text(bm, _font8, display_line1, x1, TOP_Y, color)

        if line2 and line2.strip():
            max_chars = 10
            display_line2 = line2[:max_chars] if len(line2) > max_chars else line2
            w2 = _measure_text(_font8, display_line2)
            x2 = max(0, min(64 - w2, 32 - (w2 // 2)))
            _draw_text(bm, _font8, display_line2, x2, MIDDLE_Y, color)

        if line3 and line3.strip():
            max_chars = 10
            display_line3 = line3[:max_chars] if len(line3) > max_chars else line3
            w3 = _measure_text(_font8, display_line3)
            x3 = max(0, min(64 - w3, 32 - (w3 // 2)))
            _draw_text(bm, _font8, display_line3, x3, BOTTOM_Y, color)

        tile_grid = displayio.TileGrid(bm, pixel_shader=pal, x=0, y=0)
        print(f"[CARD] Message card TileGrid created successfully: {tile_grid}")
        return tile_grid
    except Exception as e:
        print(f"[CARD] Message card error: {e}")
        import traceback
        traceback.print_exc()
        return None

def _render_card(item):
    """Render a 64×32 card with 3 lines: Ticker, Price, Change. Returns a TileGrid or None."""
    if not displayio or not _matrix or not _font8:
        return None
    try:
        bm = displayio.Bitmap(64, 32, 4)
        pal = displayio.Palette(4)
        # Index 0 is the card background; align with display mode
        if _display_mode == 'lite':
            pal[COL_BLACK] = 0xFFFFFF  # background white
            pal[COL_WHITE] = 0x000000  # text black
        else:
            pal[COL_BLACK] = 0x000000  # background black
            pal[COL_WHITE] = 0xFFFFFF  # text white
        pal[COL_GREEN] = 0x00CC00 if _display_mode == 'lite' else 0x00FF00
        pal[COL_RED] = 0xCC0000 if _display_mode == 'lite' else 0xFF0000

        # Extract item data
        symbol = item.get('symbol', '')
        typ = item.get('type', '')
        price_val = item.get('price_val')  # float for stocks/crypto
        price_str = item.get('price_str')  # string for forex
        change_val = item.get('change_val')
        change_pct = item.get('change_pct')
        is_pos = item.get('is_pos', True)

        # Line 1: Ticker symbol (centered)
        symbol_w = _measure_text(_font8, symbol)
        symbol_x = 0 if symbol_w >= 64 else (32 - (symbol_w // 2))
        _draw_text(bm, _font8, symbol, symbol_x, TOP_Y, COL_WHITE)

        # Line 2: Price (centered)
        maxw = 64
        if typ == 'stock':
            price_text = _format_price_stock(price_val or 0.0, maxw, _font8)
        elif typ == 'crypto':
            price_text = _format_price_crypto(price_val or 0.0, maxw, _font8)
        else:  # forex
            price_text = price_str or "0.0000"

        price_w = _measure_text(_font8, price_text)
        price_x = 0 if price_w >= 64 else (32 - (price_w // 2))
        _draw_text(bm, _font8, price_text, price_x, MIDDLE_Y, COL_WHITE)

        # Line 3: Change with colored arrow (centered)
        change_text = ""
        change_color = COL_GREEN if is_pos else COL_RED
        
        if typ == 'stock' and change_val is not None:
            arrow, text = _format_change_abs(change_val)
            change_text = arrow + " " + text if text else arrow
        elif typ == 'crypto' and change_pct is not None:
            arrow, text = _format_change_pct(change_pct)
            change_text = arrow + " " + text if text else arrow
        elif typ == 'forex':
            change_text = ""  # No change data for forex typically
        
        if change_text:
            change_w = _measure_text(_font8, change_text)
            change_x = 0 if change_w >= 64 else (32 - (change_w // 2))
            _draw_text(bm, _font8, change_text, change_x, BOTTOM_Y, change_color)

        return displayio.TileGrid(bm, pixel_shader=pal, x=0, y=0)
    except Exception as e:
        print("[CARD] Render error:", e)
        return None


def _show_card(tile):
    print(f"[DISPLAY] _show_card called with tile: {tile}")
    print(f"[DISPLAY] _root_group exists: {_root_group is not None}")
    print(f"[DISPLAY] _matrix exists: {_matrix is not None}")

    if not _root_group or not tile:
        print("[DISPLAY] Cannot show card - missing root_group or tile")
        return

    try:
        print(f"[DISPLAY] Current root_group length: {len(_root_group)}")

        # Append new card above background
        _root_group.append(tile)
        print(f"[DISPLAY] Added tile to root_group, new length: {len(_root_group)}")

        # Remove any previous card (keep bottom-most background + newest card)
        while len(_root_group) > 2:
            _root_group.pop(1)
            print(f"[DISPLAY] Removed old card, current length: {len(_root_group)}")

        try:
            print("[DISPLAY] Calling matrix.refresh()...")
            _matrix.refresh()
            print("[DISPLAY] Matrix refresh successful")
        except Exception as refresh_e:
            print(f"[DISPLAY] Matrix refresh failed: {refresh_e}")

    except Exception as e:
        print(f"[DISPLAY] Show card error: {e}")
        import traceback
        traceback.print_exc()


def _cleanup_display():
    if not _root_group:
        return
    try:
        while len(_root_group) > 1:
            _root_group.pop()
    except Exception:
        pass


def _build_items(stocks, crypto, forex, order):
    out = []
    try:
        for kind in order:
            if kind == 'stocks':
                for it in (stocks or []):
                    sym = it.get('ticker', '')
                    val = float(it.get('tngoLast', 0) or 0)
                    chg = float(it.get('prcChange', 0) or 0)
                    out.append({
                        'type': 'stock', 'symbol': sym, 'price_val': val,
                        'change_val': chg, 'change_pct': None, 'is_pos': (chg >= 0)
                    })
            elif kind == 'crypto':
                for it in (crypto or []):
                    sym = (it.get('ticker') or '').upper()
                    val = float(it.get('lastPrice', 0) or 0)
                    pct = float(it.get('prcChangePct', 0) or 0)
                    out.append({
                        'type': 'crypto', 'symbol': sym, 'price_val': val,
                        'change_val': None, 'change_pct': pct, 'is_pos': (pct >= 0)
                    })
            elif kind == 'forex':
                for it in (forex or []):
                    sym = (it.get('ticker') or '').upper()
                    mid = it.get('mid_price') or '0.0000'
                    out.append({
                        'type': 'forex', 'symbol': sym, 'price_val': None,
                        'price_str': str(mid), 'change_val': None, 'change_pct': None, 'is_pos': True
                    })
    except Exception as e:
        print("[DATA] Build items error:", e)
    return out


def _refresh_display():
    global _refresh_ok, _refresh_errs
    if not _matrix:
        return False
    try:
        _matrix.refresh(minimum_frames_per_second=0, target_frames_per_second=60)
        _refresh_ok += 1
        return True
    except Exception:
        try:
            _matrix.refresh()
            _refresh_ok += 1
            return True
        except Exception:
            _refresh_errs += 1
            return False


def main():
    global _matrix, _rgb_core

    if boot_logo:
        try:
            boot_display, boot_rgb_core = boot_logo.show_boot_logo()
            _matrix = boot_display or _matrix
            _rgb_core = boot_rgb_core or _rgb_core
        except Exception as e:
            print("[BOOT] Boot logo failed:", e)

    # Provisioning gate
    if _a1_switch_closed():
        has_wifi = False
        has_config = False
        try:
            with open("wifi.dat", "r") as f:
                if f.read().strip():
                    has_wifi = True
        except Exception:
            pass
        try:
            with open("device_config.json", "r") as f:
                if f.read().strip():
                    has_config = True
        except Exception:
            pass
        if not (has_wifi and has_config):
            print("[MODE] A1 grounded: starting provisioning portal…")
            try:
                import wifimgr
                wifimgr.start_provisioning()
            except Exception as e:
                print("[MODE] Provisioning launcher failed:", e)
            while True:
                time.sleep(1)
        else:
            print("[MODE] A1 grounded but already configured — continuing normal run")

    connected = connect_wifi()
    if not connected:
        if _a1_switch_closed():
            print("[MAIN] No Wi‑Fi; switch closed — starting provisioning portal")
            try:
                import wifimgr
                wifimgr.start_provisioning()
            except Exception as e:
                print("[MAIN] Provisioning failed:", e)
            return
        else:
            print("[MAIN] No Wi‑Fi and switch open. To (re)provision: close A1 to GND and reset.")
            return

    pool = socketpool.SocketPool(wifi.radio)  # type: ignore[attr-defined]
    session = adafruit_requests.Session(pool, ssl.create_default_context())
    
    # Synchronize time before API calls
    try:
        from time_sync import sync_time, validate_time
        print("[MAIN] Synchronizing system time...")
        
        # Check current time status
        is_valid, timestamp, year = validate_time()
        print(f"[MAIN] Current time status - Valid: {is_valid}, Year: {year}")
        
        # Always force time sync on startup to ensure accuracy
        print("[MAIN] Forcing time synchronization...")
        if sync_time(pool, force_ntp=True):
            is_valid, timestamp, year = validate_time()
            print(f"[MAIN] After sync - Valid: {is_valid}, Year: {year}")
        else:
            print("[MAIN] Warning: Time synchronization failed")
            
    except Exception as e:
        print(f"[MAIN] Time sync error: {e}")
    
    # Ensure device key exists (provisioning writes it when A1 grounded)
    _ensure_device_key()

    api = LocalHubAPI(session)
    if not ensure_credentials(api):
        print("[MAIN] Missing credentials/config; provision via A1 switch")
        return

    _init_matrix_once()

    # Steady-state loop
    hb_interval = 120
    last_hb = 0
    while True:
        now = time.monotonic()
        if now - last_hb > hb_interval:
            print("[API] Sending heartbeat...")
            if api.send_heartbeat():
                print("[API] Heartbeat OK")
            last_hb = now

        # Free display state before fetch
        _cleanup_display()
        gc.collect()

        display_settings = api.get_display_settings() or {}
        # Apply brightness and color mode as soon as settings are fetched
        try:
            _apply_brightness(display_settings.get('brightness'))
            _apply_display_mode(display_settings.get('display_mode'))
        except Exception as _:
            pass
        # Prefer update_interval from display settings if provided by server
        interval_from_ds = None
        try:
            if 'update_interval' in display_settings and display_settings.get('update_interval') is not None:
                interval_from_ds = int(display_settings.get('update_interval'))
        except Exception:
            interval_from_ds = None
        if interval_from_ds and interval_from_ds > 0:
            eff_interval = max(15, min(900, interval_from_ds))
        else:
            cfg = api.get_device_config() or {}
            eff_interval = _effective_fetch_interval(cfg)
        eff_dwell = _effective_item_dwell(display_settings)
        asset_order = _effective_asset_order(display_settings)
        print("[API] interval=", eff_interval, "dwell=", eff_dwell, "order=", asset_order, "mode=", _display_mode)

        raw = api.get_ticker_data() or {}
        print(f"[MAIN] API response: {raw}")

        # Check if device is orphaned
        if raw.get('orphaned'):
            print("[MAIN] Device is orphaned - attempting recovery")
            device_key = raw.get('device_key', 'UNKNOWN')

            # Show orphaned message
            orphaned_card = _create_orphaned_card(device_key)
            _show_card(orphaned_card)
            time.sleep(2)  # Show orphaned message briefly

            # Attempt recovery
            recovery_card = _create_recovery_card()
            _show_card(recovery_card)

            if api.recover_device():
                # Recovery provided instructions - show claim info to user
                claim_code = api.get_last_claim_code()
                print(f"[MAIN] Claim code retrieved: {claim_code}")

                if claim_code:
                    print(f"[MAIN] Creating claim code card with: {claim_code}")
                    # Show claim code if generated
                    claim_card = _create_claim_code_card(claim_code)
                    print(f"[MAIN] Claim card object: {claim_card}")

                    if claim_card:
                        print("[MAIN] Showing claim code card...")
                        _show_card(claim_card)
                        print("[MAIN] Claim code card shown")
                    else:
                        print("[MAIN] ERROR: Claim card creation failed!")

                else:
                    print(f"[MAIN] No claim code, showing general instructions")
                    # Show general instructions
                    instruction_card = _create_claim_instruction_card(device_key)
                    print(f"[MAIN] Instruction card object: {instruction_card}")

                    if instruction_card:
                        print("[MAIN] Showing instruction card...")
                        _show_card(instruction_card)
                        print("[MAIN] Instruction card shown")
                    else:
                        print("[MAIN] ERROR: Instruction card creation failed!")

                # Keep showing claim code until device gets claimed
                print("[MAIN] Entering claim code display loop - showing indefinitely")
                while True:
                    # Keep the claim code displayed
                    time.sleep(5)  # Check every 5 seconds

                    # Periodically check if device is still orphaned
                    try:
                        test_raw = api.get_ticker_data() or {}
                        if not test_raw.get('orphaned'):
                            print("[MAIN] Device no longer orphaned - returning to normal operation")
                            break  # Device was claimed, exit claim display loop
                    except Exception as e:
                        print(f"[MAIN] Error checking claim status: {e}")
                        # Continue showing claim code even if API check fails
                        pass
            else:
                # Recovery failed - show instructions
                failed_card = _create_recovery_failed_card(device_key)
                _show_card(failed_card)

                # Wait longer before retrying
                t0 = time.monotonic()
                while time.monotonic() - t0 < 30:  # Wait 30 seconds
                    time.sleep(0.1)
                continue

        stocks, crypto, forex = api.parse_ticker_data(raw)
        items = _build_items(stocks, crypto, forex, asset_order)

        if not items:
            # Render a simple No Data card
            dummy = {'type': 'stock', 'symbol': 'NO DATA', 'price_val': None, 'price_str': '', 'is_pos': True}
            tile = _render_card(dummy)
            _show_card(tile)
            # Wait a bit and retry
            t0 = time.monotonic()
            while time.monotonic() - t0 < 10:
                time.sleep(0.1)
            continue

        # Cycle through items until refresh interval elapses
        t_start = time.monotonic()
        idx = 0
        n = len(items)
        while time.monotonic() - t_start < eff_interval:
            item = items[idx]
            tile = _render_card(item)
            if tile:
                _show_card(tile)
            # Dwell timing using adafruit_ticks if available
            if adafruit_ticks:
                last = adafruit_ticks.ticks_ms()
                step = int(max(1, eff_dwell * 1000))
                while adafruit_ticks.ticks_diff(adafruit_ticks.ticks_ms(), last) < step:
                    time.sleep(0)
            else:
                time.sleep(eff_dwell)
            idx = (idx + 1) % n


if __name__ == "__main__":
    main()
