import ipytone
from ipytone._frontend import module_name, module_version


def test_frontend():
    assert module_name == "ipytone"
    assert module_version == f"^{ipytone.__version__}"
