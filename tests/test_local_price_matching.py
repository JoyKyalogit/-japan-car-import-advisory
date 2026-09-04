from src.services.analysis import base_model_key, models_compatible


def test_base_model_ignores_grade_noise():
    assert base_model_key("X5 X Drive 35D M Sport Airsus") == "x5"
    assert base_model_key("X5 M50D") == "x5"
    assert base_model_key("X5") == "x5"
    assert base_model_key("Hiace Van Dx") == "hiace"
    assert base_model_key("Ad Van Nv150 Ve") == "advan"
    assert base_model_key("Regiusace Van Long Dx Gl Package") == "hiace"


def test_models_compatible_bmw_x5_variants():
    japan = "X5 X Drive 35D M Sport Airsus"
    assert models_compatible(japan, "X5")
    assert models_compatible(japan, "X5 M50D")
    assert models_compatible(japan, "X5 Xdrive35D Awd")
    assert not models_compatible(japan, "X3")
    assert not models_compatible(japan, "X6")


def test_models_compatible_aliases_and_trims():
    assert models_compatible("Ad Van Ve", "Advan")
    assert models_compatible("Hiace Van Dx", "Hiace")
    assert models_compatible("Probox Van Hybrid Dx Comfort", "Probox")
    assert models_compatible("Swift Hybrid Mx", "Swift")
    assert models_compatible("Fit E:Hev Home", "Fit")
