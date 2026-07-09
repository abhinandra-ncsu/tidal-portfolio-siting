# East Coast input domain

What's actually in `tide_data_east.dbf` and how it relates to the bbox + buffer config the VP/ORPC pipelines apply.

**TL;DR**: pipeline config is correct as-is. The 0.15° bbox buffer correctly captures the East Coast; the ~317k dropped points are Gulf Coast and should be excluded. Note that the FL bbox includes peninsular Florida's Gulf side by design.

## 1. Distance offshore

n = 1,308,923 East Coast points (raw bboxes, no buffer; see §2 for buffered count).

| stat   | km   |
| ------ | ---: |
| min    | 0.0  |
| median | 4.0  |
| mean   | 5.5  |
| max    | 38.7 |

Heavy right skew, mode at 0–1 km, IQR ~1–8 km. The 39 km cutoff is **bbox-bounded, not physics-bounded** — it's how far the state east-boundaries extend, not where the shelf ends. If we ever want to characterize the *shelf*, the bboxes need widening.

![Distance offshore](distance_offshore.png)

## 2. `BBOX_BUFFER_DEG = 0.15` is correct

Both pipelines (`optimization/vp/config/config.py:135`, `optimization/orpc/config/config.py:174`) pad each state bbox by 0.15° on all sides. The buffer absorbs ~26k near-edge ROMS points (1,308,923 → 1,334,846). Without it, those show up as a thin red sliver along bbox edges — coastal points just barely outside the raw bbox.

With the buffer applied, no East Coast points remain dropped. No change needed.

## 3. The DBF includes the entire Gulf of Mexico

`tide_data_east.dbf` spans **lon −97.7 to −64.4, lat 17.6 to 45.2**. The "east" in the name is misleading: it covers Texas, Louisiana, Mississippi, Alabama, the Florida panhandle west of −86°, and reaches south into the Caribbean.

Of 1,652,176 total records, **317,330 (~19%)** fall outside any East Coast bbox even at 0.15° buffer. These are dominated by the Northern Gulf Coast (LA / MS / AL / FL panhandle). The bbox filter correctly excludes them.

![Bbox coverage](bbox_coverage.png)

## 4. The Florida bbox includes peninsular FL's Gulf coast

Florida's bbox is large: −87.58 to −79.01°W, 24.54 to 30.82°N. It wraps the entire peninsula, so points along Tampa, Naples, and the Keys' western side are *inside* the East Coast set. This is by design — flag if the scope ever gets challenged on "you said East Coast but you have Tampa." Framing: peninsular Florida is included; only the Gulf coast *west* of the FL bbox is excluded.
