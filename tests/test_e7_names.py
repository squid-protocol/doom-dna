import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))
from e7_names import key_counts, matched, name_key, name_key_n2, shared_names, survival_names, wilson_lower  # noqa: E402


def test_key_rules():
    assert name_key("P_SpawnMobj") == name_key("p_spawn_mobj") == "pspawnmobj"
    assert name_key("Foo::bar") == name_key("Foo.bar") == "bar"
    assert name_key("~Foo") is None and name_key("Foo::~Foo") is None
    assert name_key("operator==") is None and name_key("Foo::operator[]") is None
    assert name_key("") is None and name_key(None) is None and name_key("ab") is None and name_key("<lambda>") == "lambda"


def test_n2_prefix_only_with_long_stem():
    assert name_key_n2("P_SpawnMobj") == "spawnmobj"
    assert name_key_n2("get_x") == "getx"  # 'get' is not a DOOM prefix
    assert name_key_n2("R_Draw") == "rdraw"  # stem 'draw' < 6: not stripped


def test_survival_is_one_to_one_and_bounded():
    q = key_counts(["alpha_fn", "alpha_fn", "beta_fn", "main"])
    t = key_counts(["alpha_fn", "beta_fn", "beta_fn"])
    assert matched(q, t) == 2  # alpha once, beta once
    assert survival_names(q, t) <= 1.0


def test_self_to_self_is_one():
    q = key_counts(["alpha_fn", "beta_fn", "gamma_fn", "alpha_fn"])
    assert survival_names(q, q) == 1.0
    assert shared_names(q, q) > 0.3  # Wilson lower bound of 1.0 on n=4


def test_wilson_monotone_in_n():
    assert wilson_lower(50, 50) > wilson_lower(5, 5) > 0
    assert wilson_lower(0, 10) == 0.0


def test_empty():
    e = collections.Counter()
    assert survival_names(e, e) == 0.0 and shared_names(e, e) == 0.0
