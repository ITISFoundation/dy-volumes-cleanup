# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import os
import traceback
from pathlib import Path

import pytest
from aiodocker.volumes import DockerVolume
from click.testing import Result
from pytest_mock.plugin import MockerFixture
from typer.testing import CliRunner

from dy_volumes_cleanup._s3 import S3Provider
from dy_volumes_cleanup.cli import app


def _format_cli_error(result: Result) -> str:
    assert result.exception
    tb_message = "\n".join(traceback.format_tb(result.exception.__traceback__))
    return f"Below exception was raised by the cli:\n{tb_message}"


@pytest.fixture
async def mock_volumes_folders(
    mocker: MockerFixture,
    unused_volume: DockerVolume,
    used_volume: DockerVolume,
    unused_volume_path: Path,
    used_volume_path: Path,
) -> None:
    # overwrite to test locally not against volume
    # root permissions are required to access this
    # only returning the volumes which are interesting

    unused_volume_path.mkdir(parents=True, exist_ok=True)
    used_volume_path.mkdir(parents=True, exist_ok=True)

    unused_volume_data = await unused_volume.show()
    unused_volume_data["Mountpoint"] = f"{unused_volume_path}"
    used_volume_data = await used_volume.show()
    used_volume_data["Mountpoint"] = f"{used_volume_path}"

    volumes_inspect = [unused_volume_data, used_volume_data]

    # patch the function here
    mocker.patch(
        "aiodocker.volumes.DockerVolumes.list",
        return_value={"Volumes": volumes_inspect},
    )


@pytest.fixture
async def used_volume_name(used_volume: DockerVolume) -> str:
    return (await used_volume.show())["Name"]


@pytest.fixture
async def unused_volume_name(unused_volume: DockerVolume) -> str:
    return (await unused_volume.show())["Name"]


def test_workflow(
    mock_volumes_folders: None,
    minio: dict,
    bucket: str,
    used_volume_name: str,
    unused_volume_name: str,
):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            minio["endpoint"],
            minio["access_key"],
            minio["secret_key"],
            bucket,
            S3Provider.MINIO,
        ],
    )
    assert result.exit_code == os.EX_OK, _format_cli_error(result)
    assert f"Removed docker volume: '{unused_volume_name}'" in result.stdout
    assert f"Skipped in use docker volume: '{used_volume_name}'" in result.stdout
