import anycastd


def test_version_displayed_correctly(anycastd_cli):
    """The version is displayed correctly."""
    expected = "anycastd {}\n".format(anycastd.__version__)

    result = anycastd_cli("--version")

    assert result.exit_code == 0
    assert result.stdout == expected
