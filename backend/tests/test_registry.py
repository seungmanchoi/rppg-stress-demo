from app.models.registry import ALGORITHMS, all_ids, get_meta


def test_registry_has_eight():
    assert len(ALGORITHMS) == 8


def test_registry_ids():
    assert set(all_ids()) == {
        "POS", "CHROM", "OMIT",
        "TS-CAN", "EfficientPhys", "PhysFormer", "RhythmFormer", "BigSmall",
    }


def test_unsupervised_have_no_weights():
    for aid in ("POS", "CHROM", "OMIT"):
        m = get_meta(aid)
        assert m.type == "unsupervised"
        assert m.weight_url is None
        assert m.weight_filename is None


def test_supervised_have_weights():
    for aid in ("TS-CAN", "EfficientPhys", "PhysFormer", "RhythmFormer", "BigSmall"):
        m = get_meta(aid)
        assert m.type == "supervised"
        assert m.weight_url and m.weight_filename
        assert m.pretrained_on
