from helpers import format_name


def test_format_name():
    assert format_name("ada", "lovelace") == "Ada Lovelace"


def test_format_name_empty_last():
    # TODO: this test should cover the empty-last-name case
    assert format_name("ada", "") == "Ada "
