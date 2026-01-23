from core.indices.environmental_indices import indice_wbgt, indice_pmv_ppd_simple


def test_indice_wbgt_returns_number():
    val = indice_wbgt(30.0, 50.0, radiacion=200.0, viento_kmh=5.0)
    assert isinstance(val, float) or isinstance(val, int)
    assert -50.0 < float(val) < 100.0


def test_indice_pmv_ppd_simple_structure():
    res = indice_pmv_ppd_simple(25.0, 50.0, viento_kmh=5.0)
    assert isinstance(res, dict)
    assert "pmv" in res and "ppd" in res
    pmv = float(res["pmv"])
    ppd = float(res["ppd"])
    assert -3.1 <= pmv <= 3.1
    assert 0.0 <= ppd <= 100.0
