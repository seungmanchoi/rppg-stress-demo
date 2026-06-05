from app.models.registry import ALGORITHMS, all_ids, get_meta

UNSUPERVISED = ("POS", "CHROM", "OMIT", "GREEN", "ICA")
SUPERVISED = (
    "TS-CAN", "EfficientPhys", "PhysFormer", "RhythmFormer", "BigSmall",
    "PhysNet", "DeepPhys",
)


def test_registry_has_twelve():
    assert len(ALGORITHMS) == 12


def test_registry_ids():
    assert set(all_ids()) == set(UNSUPERVISED) | set(SUPERVISED)


def test_unsupervised_have_no_weights():
    for aid in UNSUPERVISED:
        m = get_meta(aid)
        assert m.type == "unsupervised"
        assert m.weight_url is None
        assert m.weight_filename is None


def test_supervised_have_weights():
    for aid in SUPERVISED:
        m = get_meta(aid)
        assert m.type == "supervised"
        assert m.weight_url and m.weight_filename
        assert m.pretrained_on
