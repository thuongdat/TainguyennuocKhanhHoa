# -*- coding: utf-8 -*-
"""
Sua duong dan co so du lieu PROJ truoc khi nap GeoPandas / pyproj.

Vi sao can: tren nhieu may da cai san PostGIS hoac nhieu moi truong conda,
bien moi truong PROJ_LIB hoac PROJ_DATA van tro den thu muc proj cua mot ban
cai khac. Khi do pyproj trong moi truong hien tai doc nham proj.db cu va bao
loi kieu:

    proj.db contains DATABASE.LAYOUT.VERSION.MINOR = 6 whereas a number >= 7
    is expected. It comes from another PROJ installation.

Cach xu ly: tro hai bien do ve dung thu muc proj cua chinh moi truong Python
dang chay. Phai goi TRUOC khi import geopandas, pyproj hoac pyogrio.

Cach dung:
    from moi_truong_proj import sua_duong_dan_proj
    sua_duong_dan_proj()
    import geopandas as gpd
"""

import os
import sys


def sua_duong_dan_proj(in_thong_bao=True):
    """Tro PROJ_DATA va PROJ_LIB ve thu muc proj cua moi truong dang chay."""
    cac_ung_vien = [
        os.path.join(sys.prefix, "Library", "share", "proj"),  # Windows, conda
        os.path.join(sys.prefix, "share", "proj"),             # Linux, macOS
    ]

    for duong_dan in cac_ung_vien:
        if os.path.isfile(os.path.join(duong_dan, "proj.db")):
            cu = os.environ.get("PROJ_DATA") or os.environ.get("PROJ_LIB")
            os.environ["PROJ_DATA"] = duong_dan
            os.environ["PROJ_LIB"] = duong_dan
            if in_thong_bao and cu and os.path.normpath(cu) != os.path.normpath(duong_dan):
                print("Da sua duong dan PROJ:")
                print("  truoc : {}".format(cu))
                print("  sau   : {}".format(duong_dan))
            return duong_dan

    if in_thong_bao:
        print("Canh bao: khong tim thay proj.db trong moi truong hien tai.")
    return None
