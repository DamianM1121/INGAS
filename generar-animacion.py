#!/usr/bin/env python3
"""
Animacion del logo INCAS para encabezado web.
- Separa el logo en capas (letras I/N/C/S, fuego azul marino = "A", llamas cian, subtitulo)
- Limpia el halo claro de 1px (artefacto de recorte) -> bordes limpios sobre cualquier fondo
- Genera: intro (letras aparecen + ignicion del fuego) y loop de fuego vivo, con alfa real
"""
import os, math
import numpy as np
from PIL import Image, ImageFilter

SRC   = 'image.png'          # el PNG original, en esta misma carpeta
OUT   = '.'                  # los archivos se escriben en esta carpeta
W, H  = 640, 240
FPS   = 25

T_LOOP   = 2.0                      # periodo del loop de fuego
N_LOOP   = int(round(T_LOOP * FPS)) # 50
IGNITE_T = 0.48                     # cuando arranca la ignicion
T_INTRO  = IGNITE_T + T_LOOP        # 2.48 s  (termina en fase 0 del loop -> empalme perfecto)
N_INTRO  = int(round(T_INTRO * FPS))

NAVY    = np.array([6, 64, 112],  np.float32) / 255.0
CYAN    = np.array([3, 190, 221], np.float32) / 255.0
SUBC    = np.array([27, 27, 27],  np.float32) / 255.0
CYAN_HI = np.array([168, 240, 252], np.float32) / 255.0
NAVY_HI = np.array([90, 170, 235], np.float32) / 255.0
GLOW_C  = np.array([70, 205, 240], np.float32) / 255.0

Y_BASE = 186.0   # base del fuego (anclaje: ahi no hay movimiento)
Y_TOP  = 0.0
CX_FIRE = 435.0  # centro horizontal del grupo de fuego

PAD = 26         # padding de las capas para que las transformaciones no recorten

os.makedirs(OUT, exist_ok=True)
os.makedirs('tmp/prev', exist_ok=True)


# ---------------------------------------------------------------- utilidades
def ease_out_cubic(p):
    return 1.0 - (1.0 - p) ** 3

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)

def blend(dst, src, ox, oy):
    """compone src (RGBA float) sobre dst en la posicion (ox, oy)"""
    sh, sw = src.shape[:2]
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(W, ox + sw), min(H, oy + sh)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    d = dst[y0:y1, x0:x1]
    sa = s[..., 3:4]
    da = d[..., 3:4]
    oa = sa + da * (1.0 - sa)
    safe = np.maximum(oa, 1e-6)
    d[..., :3] = (s[..., :3] * sa + d[..., :3] * da * (1.0 - sa)) / safe
    d[..., 3:4] = oa

def affine_mask(mask, s, tx, ty, cx, cy):
    """escala s y traslada (tx,ty) alrededor de (cx,cy) en coords de la capa"""
    im = Image.fromarray(np.clip(mask * 255.0, 0, 255).astype(np.uint8), 'L')
    a = 1.0 / s
    c = (-(1.0 - s) * cx - tx) / s
    f = (-(1.0 - s) * cy - ty) / s
    im2 = im.transform(im.size, Image.AFFINE, (a, 0, c, 0, a, f), resample=Image.BICUBIC)
    return np.asarray(im2, np.float32) / 255.0

def warp_mask(mask, dx, dy):
    """muestrea mask con desplazamiento (dx,dy) por pixel (bilineal)"""
    h, w = mask.shape
    ys, xs = np.meshgrid(np.arange(h, dtype=np.float32),
                         np.arange(w, dtype=np.float32), indexing='ij')
    sy = np.clip(ys + dy, 0, h - 1.001)
    sx = np.clip(xs + dx, 0, w - 1.001)
    y0 = np.floor(sy).astype(np.int32); x0 = np.floor(sx).astype(np.int32)
    fy = (sy - y0); fx = (sx - x0)
    m = mask
    v = (m[y0, x0] * (1 - fy) * (1 - fx) + m[y0, x0 + 1] * (1 - fy) * fx +
         m[y0 + 1, x0] * fy * (1 - fx) + m[y0 + 1, x0 + 1] * fy * fx)
    return v

def make_field(n_frames, shape, gh, gw, tsigma, seed):
    """campo de ruido suave, periodico en el tiempo (loop perfecto)"""
    rng = np.random.default_rng(seed)
    h, w = shape
    frames = []
    for _ in range(n_frames):
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        frames.append(np.asarray(im, np.float32) / 255.0)
    F = np.stack(frames)
    F -= F.mean()
    F /= (F.std() + 1e-6)
    k = max(1, int(round(tsigma * 2.5)))
    xs = np.arange(-k, k + 1)
    ker = np.exp(-(xs ** 2) / (2 * tsigma ** 2)); ker /= ker.sum()
    Fp = np.concatenate([F[-k:], F, F[:k]], 0)
    out = np.empty_like(F)
    for i in range(n_frames):
        out[i] = (Fp[i:i + 2 * k + 1] * ker[:, None, None]).sum(0)
    out /= (out.std() + 1e-6)
    return out


# ---------------------------------------------------------------- 1. cargar + limpiar halo
arr = np.asarray(Image.open(SRC).convert('RGBA'), np.float32) / 255.0
rgb, al = arr[..., :3], arr[..., 3]

def unmatte(arr):
    """quita el matte claro: c = t*s + (1-t)*blanco  ->  (s, alpha*t)"""
    rgb, al = arr[..., :3], arr[..., 3]
    white = np.ones(3, np.float32)
    cands = [NAVY, CYAN, SUBC]
    best_err = np.full(rgb.shape[:2], 1e9, np.float32)
    best_col = np.zeros_like(rgb)
    best_t = np.zeros(rgb.shape[:2], np.float32)
    for s in cands:
        v = white - s
        t = np.clip(((white - rgb) * v).sum(-1) / (v * v).sum(), 0, 1)
        rec = white[None, None, :] - t[..., None] * v[None, None, :]
        err = np.linalg.norm(rgb - rec, axis=-1)
        m = err < best_err
        best_err = np.where(m, err, best_err)
        best_col = np.where(m[..., None], s[None, None, :], best_col)
        best_t = np.where(m, t, best_t)
    out = arr.copy()
    fix = (al > 0) & (best_err < 0.06) & (best_t < 0.97) & (best_t > 0.0)
    out[..., :3] = np.where(fix[..., None], best_col, rgb)
    out[..., 3] = np.where(fix, al * best_t, al)
    return out

clean = unmatte(arr)
rgb, al = clean[..., :3], clean[..., 3]

# ---------------------------------------------------------------- 2. mascaras
d_navy = np.linalg.norm(rgb - NAVY, axis=-1)
d_cyan = np.linalg.norm(rgb - CYAN, axis=-1)
w_cyan = np.clip(0.5 + (d_navy - d_cyan) * 6.0, 0.0, 1.0)      # 0 navy .. 1 cyan
w_cyan[al < 0.02] = 0.0

# gota interna: el unico componente claramente cian que no es la llama grande
from collections import deque
def label_solid(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32); cur = 0
    for y0 in range(h):
        for x0 in range(w):
            if mask[y0, x0] and lab[y0, x0] == 0:
                cur += 1
                q = deque([(y0, x0)]); lab[y0, x0] = cur
                while q:
                    y, x = q.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and lab[ny, nx] == 0:
                                lab[ny, nx] = cur; q.append((ny, nx))
    return lab, cur

lab, ncomp = label_solid(al > 0.16)
cand = []
for i in range(1, ncomp + 1):
    m = lab == i
    n = int(m.sum())
    if n < 40:
        continue
    if float(w_cyan[m].mean()) > 0.5:
        cand.append((n, i))
tear = (lab == min(cand)[1]).astype(np.float32) if cand else np.zeros_like(w_cyan)
print('gota interna: %d px' % int(tear.sum()))
tear = np.asarray(Image.fromarray((tear * 255).astype(np.uint8)).filter(
    ImageFilter.MaxFilter(3)), np.float32) / 255.0

fire_region = np.zeros((H, W), np.float32)
fire_region[0:201, 352:520] = 1.0
sub_region = np.zeros((H, W), np.float32)
sub_region[201:240, :] = 1.0

m_cyan_big = al * w_cyan * (1.0 - tear) * fire_region
m_tear     = al * w_cyan * tear * fire_region
m_firenavy = al * (1.0 - w_cyan) * fire_region

LETTERS = [('I', 0, 47), ('N', 48, 201), ('C', 202, 351), ('S', 520, 640)]
letter_masks = {}
for name, x0, x1 in LETTERS:
    m = np.zeros((H, W), np.float32)
    m[0:201, x0:x1] = al[0:201, x0:x1]
    letter_masks[name] = m
m_sub = al * sub_region

# ---------------------------------------------------------------- 3. capas con padding
def crop_layer(mask, box):
    x0, y0, x1, y1 = box
    out = np.zeros((y1 - y0 + 2 * PAD, x1 - x0 + 2 * PAD), np.float32)
    src = mask[max(0, y0):y1, max(0, x0):x1]
    out[PAD + max(0, -y0):PAD + max(0, -y0) + src.shape[0],
        PAD + max(0, -x0):PAD + max(0, -x0) + src.shape[1]] = src
    return out, (x0 - PAD, y0 - PAD)

fire_box = (352, 0, 520, 201)
L_cy, off_cy = crop_layer(m_cyan_big, fire_box)
L_te, _      = crop_layer(m_tear, fire_box)
L_fn, _      = crop_layer(m_firenavy, fire_box)
FBH, FBW = L_cy.shape
L_le = {}
for name, x0, x1 in LETTERS:
    L_le[name], _ = crop_layer(letter_masks[name], (x0, 0, x1, 201))
L_sb, off_sb = crop_layer(m_sub, (0, 200, W, 240))

# coords del anclaje dentro de las capas con padding
ybase_l = Y_BASE - off_cy[1]
ytop_l  = Y_TOP - off_cy[1]
cx_l    = CX_FIRE - off_cy[0]

# altura normalizada dentro de la capa de fuego (1 arriba, 0 en la base)
ys = np.arange(FBH, dtype=np.float32)[:, None]
hh = np.clip((ybase_l - ys) / (ybase_l - ytop_l), 0, 1) ** 1.35
hh = np.broadcast_to(hh, (FBH, FBW))

# mascara suave del azul marino para pegar la llama cian a la "A"
navy_soft = np.asarray(Image.fromarray((np.clip(L_fn, 0, 1) * 255).astype(np.uint8), 'L')
                       .filter(ImageFilter.GaussianBlur(5)), np.float32) / 255.0
w_extra = np.clip(1.0 - navy_soft * 1.8, 0.0, 1.0)

# ---------------------------------------------------------------- 4. campos de ruido
F_dx = make_field(N_LOOP, (FBH, FBW), gh=7, gw=6, tsigma=1.6, seed=11)
F_dy = make_field(N_LOOP, (FBH, FBW), gh=6, gw=5, tsigma=1.9, seed=29)
F_br = make_field(N_LOOP, (1, 1), gh=2, gw=2, tsigma=2.2, seed=7)[:, 0, 0]
F_sy = make_field(N_LOOP, (1, 1), gh=2, gw=2, tsigma=2.6, seed=41)[:, 0, 0]


def fire_layers(i, amp=1.0):
    """devuelve (m_cian, m_gota, m_navy) deformadas para la fase i"""
    dx = (F_dx[i] * 4.6 * amp) * hh
    dy = (F_dy[i] * 3.1 * amp) * hh
    breath = 1.0 + 0.022 * F_sy[i]
    # respiracion vertical anclada en la base (estirar hacia arriba)
    dy = dy + (ys - ybase_l) * (1.0 / breath - 1.0)
    # la punta no puede salir por arriba del lienzo: se anula el desplazamiento
    # hacia arriba en las primeras filas (la punta igual ondula en horizontal)
    taper = smoothstep(0.0, 20.0, ys)
    dy = np.where(dy > 0, dy * taper, dy)
    wc = warp_mask(L_cy, dx, dy)
    wt = warp_mask(L_te, dx, dy)
    wn = warp_mask(L_fn, dx * 0.42, dy * 0.42)
    return wc, wt, wn


def frame(t, fire_idx, fire_t):
    """t = tiempo global; fire_t = segundos desde la ignicion (puede ser <0)"""
    cv = np.zeros((H, W, 4), np.float32)

    # --- estado del fuego (ignicion) ---
    if fire_t < 0:
        op, sy, sx, flash = 0.0, 0.0, 1.0, 0.0
    else:
        p = min(1.0, fire_t / 0.75)
        e = ease_out_cubic(p)
        op = min(1.0, fire_t / 0.10)
        sy = e * (1.0 + 0.10 * math.sin(math.pi * p) * (1.0 - p))
        sx = 0.72 + 0.28 * e
        flash = math.exp(-max(fire_t, 0.0) / 0.17)

    if op > 0.001:
        wc, wt, wn = fire_layers(fire_idx, amp=min(1.0, 0.35 + 0.65 * op))

        # respiracion/estirón de todo el grupo anclado en la base
        def ign(m):
            if abs(sy - 1.0) < 1e-4 and abs(sx - 1.0) < 1e-4:
                return m
            im = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8), 'L')
            a = 1.0 / sx
            f = 1.0 / sy
            c = cx_l - cx_l / sx
            f2 = ybase_l - ybase_l / sy
            im = im.transform(im.size, Image.AFFINE, (a, 0, c, 0, f, f2),
                              resample=Image.BICUBIC)
            return np.asarray(im, np.float32) / 255.0
        wc, wt, wn = ign(wc), ign(wt), ign(wn)

        # --- glow (detras de todo) ---
        gp = 0.5 + 0.5 * F_br[fire_idx]
        g_in = np.asarray(Image.fromarray((np.clip(wc + wt, 0, 1) * 255).astype(np.uint8), 'L')
                          .filter(ImageFilter.GaussianBlur(9)), np.float32) / 255.0
        g_out = np.asarray(Image.fromarray((np.clip(wc + wt, 0, 1) * 255).astype(np.uint8), 'L')
                           .filter(ImageFilter.GaussianBlur(22)), np.float32) / 255.0
        fade_top = np.clip(np.arange(FBH, dtype=np.float32)[:, None] / 7.0, 0, 1)
        glow = (g_in * (0.16 + 0.16 * gp) + g_out * (0.07 + 0.07 * gp)) * fade_top * op
        glow *= (1.0 + 1.5 * flash)
        gc = GLOW_C * (1 - flash) + np.array([1, 1, 1], np.float32) * flash
        gl = np.zeros(glow.shape + (4,), np.float32)
        gl[..., :3] = np.clip(gc, 0, 1); gl[..., 3] = np.clip(glow, 0, 0.85)
        blend(cv, gl, off_cy[0], off_cy[1])

        # --- llama cian grande: brillo pulsante + lengua de luz que sube ---
        pulse = (1.0 + 0.11 * math.sin(2 * math.pi * fire_idx / N_LOOP * 2 + 0.7)
                 + 0.055 * math.sin(2 * math.pi * fire_idx / N_LOOP * 3 + 2.1)
                 + 0.09 * F_br[fire_idx])
        band_y = ybase_l - (ybase_l - ytop_l) * ((fire_idx / N_LOOP * 1.0 + 0.15) % 1.0)
        band = 0.27 * np.exp(-((ys - band_y) / 30.0) ** 2) * (0.6 + 0.4 * gp)
        ccol = CYAN[None, None, :] * pulse + (CYAN_HI - CYAN)[None, None, :] * np.clip(band, 0, 1)[..., None]
        ccol = ccol * (1 - flash) + CYAN_HI[None, None, :] * flash * 0.85
        ccol = np.clip(ccol, 0, 1)
        tmp = np.zeros(wc.shape + (4,), np.float32)
        tmp[..., :3] = ccol; tmp[..., 3] = wc * op
        blend(cv, tmp, off_cy[0], off_cy[1])

        # --- gota interna: escala propia ---
        ts = 1.0 + 0.055 * math.sin(2 * math.pi * fire_idx / N_LOOP * 2 + 1.3)
        wt2 = affine_mask(wt, ts, 0, 0, cx_l, ybase_l - 60)
        tcol = CYAN * (0.92 + 0.16 * (0.5 + 0.5 * F_br[fire_idx]))
        tcol = tcol * (1 - flash) + CYAN_HI * flash
        tmp = np.zeros(wt2.shape + (4,), np.float32)
        tmp[..., :3] = np.clip(tcol, 0, 1); tmp[..., 3] = wt2 * op
        blend(cv, tmp, off_cy[0], off_cy[1])

        # --- llama azul marino (la "A") ---
        ncol = NAVY * (1.0 + 0.05 * F_br[fire_idx])
        ncol = ncol * (1 - flash * 0.75) + NAVY_HI * flash * 0.75
        tmp = np.zeros(wn.shape + (4,), np.float32)
        tmp[..., :3] = np.clip(ncol, 0, 1); tmp[..., 3] = wn * op
        blend(cv, tmp, off_cy[0], off_cy[1])

    # --- letras I, N, C, S ---
    times = {'I': 0.08, 'N': 0.21, 'C': 0.34, 'S': 0.72}
    for name, x0, x1 in LETTERS:
        p = np.clip((t - times[name]) / 0.45, 0, 1)
        if p <= 0:
            continue
        e = ease_out_cubic(p)
        lm = L_le[name]
        ty = 15.0 * (1 - e)
        s = 0.965 + 0.035 * e
        lw, lh = lm.shape
        cxl = (x0 + x1) / 2.0 - (x0 - PAD)
        cyl = 150.0 - (0 - PAD)
        m = affine_mask(lm, s, 0, ty, cxl, cyl)
        tmp = np.zeros(m.shape + (4,), np.float32)
        tmp[..., :3] = NAVY; tmp[..., 3] = m * e
        blend(cv, tmp, x0 - PAD, 0 - PAD)

    # --- subtitulo ---
    p = np.clip((t - 1.30) / 0.55, 0, 1)
    if p > 0:
        e = ease_out_cubic(p)
        m = affine_mask(L_sb, 1.0, 0, 9.0 * (1 - e), 0, 0)
        tmp = np.zeros(m.shape + (4,), np.float32)
        tmp[..., :3] = SUBC; tmp[..., 3] = m * e
        blend(cv, tmp, off_sb[0], off_sb[1])

    return np.clip(cv, 0, 1)


def to_img(cv):
    return Image.fromarray((cv * 255 + 0.5).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- 5. render
intro, loop = [], []
for k in range(N_INTRO):
    t = k / FPS
    ft = t - IGNITE_T
    fi = (k - int(round(IGNITE_T * FPS))) % N_LOOP
    intro.append(to_img(frame(t, fi, ft)))
for k in range(N_LOOP):
    loop.append(to_img(frame(99.0, k, 99.0)))

print('frames listos:', len(intro), len(loop))

# previews para revision
for k in [0, 6, 12, 18, 26, 34, 45, 61]:
    for bgname, bg in (('dark', (8, 34, 56)), ('light', (255, 255, 255))):
        im = Image.new('RGBA', (W, H), bg + (255,))
        im.alpha_composite(intro[k])
        im.convert('RGB').save('tmp/prev/i%02d_%s.png' % (k, bgname))

# ---------------------------------------------------------------- 6. fotogramas + codificacion
import subprocess, shutil

ALPHA_BITS = 6        # alfa de 6 bits: visualmente identico, ~30% menos de peso
QFINAL = 78

def save_frames(ims, d):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    n = (1 << ALPHA_BITS) - 1
    for k, im in enumerate(ims):
        a = np.asarray(im).copy()
        v = np.round(a[..., 3].astype(np.float32) / 255.0 * n)
        a[..., 3] = np.clip(v / n * 255, 0, 255).astype(np.uint8)
        Image.fromarray(a, 'RGBA').save('%s/%03d.png' % (d, k))

save_frames(intro, 'tmp/fi6')
save_frames(loop, 'tmp/fl6')

def encode(src, dst, loop_count):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                    '-i', src, '-c:v', 'libwebp_anim', '-lossless', '0',
                    '-q:v', str(QFINAL), '-compression_level', '6',
                    '-loop', str(loop_count), '-pix_fmt', 'yuva420p', dst], check=True)
    print('  %-36s %6.0f KB' % (os.path.basename(dst), os.path.getsize(dst) / 1024))

print('codificando:')
encode('tmp/fi6/%03d.png', f'{OUT}/incas-logo-intro.webp', 1)       # se reproduce una vez
encode('tmp/fl6/%03d.png', f'{OUT}/incas-logo-fuego-loop.webp', 0)  # fuego en bucle infinito
allf = 'tmp/fall'
shutil.rmtree(allf, ignore_errors=True); os.makedirs(allf, exist_ok=True)
for k in range(N_INTRO):
    shutil.copy('tmp/fi6/%03d.png' % k, '%s/%03d.png' % (allf, k))
for k in range(N_LOOP):
    shutil.copy('tmp/fl6/%03d.png' % k, '%s/%03d.png' % (allf, N_INTRO + k))
encode('tmp/fall/%03d.png', f'{OUT}/incas-logo.webp', 0)            # todo en uno, en bucle

to_img(frame(99.0, 0, 99.0)).save(f'{OUT}/incas-logo-estatico.png')
print('listo')
