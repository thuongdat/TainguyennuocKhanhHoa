# -*- coding: utf-8 -*-
"""Chot cac lop do scripts/14_nap_bo_sung_mapinfo.py sinh ra.

- Lop co trong lop_co_san cua tinh.json <=> tep data/<lop>.geojson ton tai.
- Moi lop deu duoc khai bao trong CAU_HINH.lop cua config.js.
- Toa do nam trong khung_bao_nen (bat loi quen ep he 9217 hoac lon X/Y).
- Khong con ky tu TCVN3 sot trong thuoc tinh chu.
- WQI khong co gia tri 0 (0 la ky chua do).
- Khong dua ho ten nguoi dan cung cap thong tin vet lu ra du lieu cong khai.
"""

import json
import os

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAC_LOP = ["quan_trac_dia_phuong", "ao_ho_khong_san_lap", "luu_luong",
           "vet_lu", "sat_lo"]
# Ky tu cp1252 hay gap khi TCVN3 chua doi (vd "Kh¸nh Hßa", "S«ng")
# Chi gom ky tu KHONG co trong tieng Viet, de khong bat nham chu dung (a, o...)
KY_TU_TCVN3 = set("¸µ¶·¹¨¾»¼½Æ©ÇË®ÎÏÑ¬Ö«×ØÛß§¡¢¤¥¦åæçëîïñö÷øûü")


def _doc(*duong):
    with open(os.path.join(GOC, *duong), encoding="utf-8") as f:
        return json.load(f)


def _tep(lop):
    return os.path.join(GOC, "data", lop + ".geojson")


@pytest.mark.parametrize("lop", CAC_LOP)
def test_dang_ky_khop_voi_tep(lop):
    da_dang_ky = lop in _doc("tinh.json")["lop_co_san"]
    assert da_dang_ky == os.path.isfile(_tep(lop)), lop


@pytest.mark.parametrize("lop", CAC_LOP)
def test_config_js_khai_bao_lop(lop):
    with open(os.path.join(GOC, "assets", "js", "config.js"),
              encoding="utf-8") as f:
        chu = f.read()
    assert "\n    " + lop + ": {" in chu
    assert "'" + lop + ".geojson'" in chu


@pytest.mark.parametrize("lop", CAC_LOP)
def test_toa_do_va_chu_tieng_viet(lop):
    if not os.path.isfile(_tep(lop)):
        pytest.skip("chua sinh " + lop)
    x0, y0, x1, y1 = _doc("tinh.json")["khung_bao_nen"]
    tap = _doc("data", lop + ".geojson")
    assert tap["features"]
    ma = set()
    for d in tap["features"]:
        hh = d["geometry"]
        cac_diem = [hh["coordinates"]] if hh["type"] == "Point" else hh["coordinates"]
        for x, y in cac_diem:
            assert x0 <= x <= x1 and y0 <= y <= y1, (d["properties"]["ma"], x, y)
        for k, v in d["properties"].items():
            if isinstance(v, str) and k != "chuoi_wqi":
                assert not (set(v) & KY_TU_TCVN3), (k, v)
        assert d["properties"]["ma"] not in ma
        ma.add(d["properties"]["ma"])


def test_wqi_khong_co_gia_tri_0():
    if not os.path.isfile(_tep("quan_trac_dia_phuong")):
        pytest.skip("chua sinh")
    for d in _doc("data", "quan_trac_dia_phuong.geojson")["features"]:
        p = d["properties"]
        assert p["wqi"] is None or p["wqi"] > 0
        assert ": 0;" not in (p.get("chuoi_wqi") or "") + ";"


def test_vet_lu_khong_mang_ho_ten_nguoi_cung_cap():
    if not os.path.isfile(_tep("vet_lu")):
        pytest.skip("chua sinh")
    for d in _doc("data", "vet_lu.geojson")["features"]:
        assert "nguoi_cung_cap" not in d["properties"]
