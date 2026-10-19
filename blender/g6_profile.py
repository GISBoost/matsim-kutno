"""G6: profil czasu klatki: apply() (Python), ewaluacja depsgraph (GN), render. blender -b --factory-startup --python blender/g6_profile.py -- --data output/g6_blender_r3 --res 1280 720 --net-radius 1e9"""
import runpy, time, bpy
from pathlib import Path
G = runpy.run_path(str(Path(__file__).with_name("g6_story5.py")), run_name="g6s")
sc, apply = G["sc"], G["apply"]; mod = G["mod"]
sc.render.filepath = "//prof.png"
def T(f, *a):
    t = time.perf_counter(); f(*a); return time.perf_counter() - t
for o in (100, 700, 1700, 2300):
    ts = []
    for rep in range(2):
        tp = T(apply, o)
        tg = T(bpy.context.view_layer.update)          # GN + reszta depsgraph
        tr = T(bpy.ops.render.render)                  # render (GN juz policzone -> glownie Eevee)
        ts.append((tp, tg, tr))
    print(f"PROF o={o} apply={ts[1][0]:.3f}s depsgraph(GN)={ts[1][1]:.3f}s render={ts[1][2]:.3f}s")
mod.show_render = False
for o in (700, 2300):
    apply(o); bpy.context.view_layer.update(); print(f"PROF o={o} bez GN render={T(bpy.ops.render.render):.3f}s")

sc.render.image_settings.file_format = "PNG"; sc.render.filepath = str(Path(bpy.app.tempdir) / "p_")
def anim(label, a=700, n=15):
    sc.frame_start, sc.frame_end = a, a + n - 1
    t = time.perf_counter(); bpy.ops.render.render(animation=True); print(f"PROF anim {label}: {(time.perf_counter()-t)/n:.3f} s/klatke")
anim("baza")
sc.eevee.use_shadows = False; anim("bez cieni")
sc.eevee.use_volume_custom_range = False
try: sc.render.use_persistent_data = True; anim("persistent_data")
except Exception as e: print("PROF persistent err", e)
sc.eevee.use_fast_gi = False if hasattr(sc.eevee, "use_fast_gi") else None; anim("po fast_gi")
sc.render.engine = "BLENDER_WORKBENCH"; anim("WORKBENCH (tylko do porownania narzutu)")
