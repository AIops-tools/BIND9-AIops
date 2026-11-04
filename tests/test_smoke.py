"""Release-shape invariants for BIND 9 AIops."""

import asyncio
import tomllib
from pathlib import Path

from typer.testing import CliRunner


def test_version_matches_project_metadata():
    import bind9_aiops

    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert bind9_aiops.__version__ == pyproject["project"]["version"]


def test_cli_builds_and_mcp_tools_are_governed():
    from bind9_aiops.cli import app
    from bind9_aiops.mcp_server.server import mcp

    assert CliRunner().invoke(app, ["--help"]).exit_code == 0
    listed = asyncio.run(mcp.list_tools())
    assert len(listed) == 23
    for name, tool in mcp._tool_manager._tools.items():
        assert tool.fn._is_governed_tool, name
        doc = (tool.fn.__doc__ or "").lstrip()
        assert doc.startswith(("[READ]", "[WRITE]")), name
        assert doc.startswith("[READ]") == (tool.fn._risk_level == "low"), name
