# pylint: disable=missing-module-docstring,missing-function-docstring,too-many-arguments,
# pylint: disable=redefined-outer-name,unused-argument

from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import aioboto3
import aiodocker
import pytest
import tenacity
from aiodocker.volumes import DockerVolume

pytestmark = pytest.mark.asyncio


@pytest.fixture
def swarm_stack_name() -> str:
    return "test-simcore"


@pytest.fixture
def study_id() -> str:
    return f"{uuid4()}"


@pytest.fixture
def node_uuid() -> str:
    return f"{uuid4()}"


@pytest.fixture
def run_id() -> str:
    return f"{uuid4()}"


@pytest.fixture
def bucket() -> str:
    return f"test-bucket-{uuid4()}"


@pytest.fixture
def used_volume_path(tmp_path: Path) -> Path:
    return tmp_path / "used_volume"


@pytest.fixture
def unused_volume_path(tmp_path: Path) -> Path:
    return tmp_path / "unused_volume"


def _get_source(run_id: str, node_uuid: str, volume_path: Path) -> str:
    reversed_path = f"{volume_path}"[::-1].replace("/", "_")
    return f"dyv_{run_id}_{node_uuid}_{reversed_path}"


@pytest.fixture
async def unused_volume(
    swarm_stack_name: str,
    study_id: str,
    node_uuid: str,
    run_id: str,
    unused_volume_path: Path,
) -> AsyncIterator[DockerVolume]:

    async with aiodocker.Docker() as docker_client:
        source = _get_source(run_id, node_uuid, unused_volume_path)
        volume = await docker_client.volumes.create(
            {
                "Name": source,
                "Labels": {
                    "node_uuid": node_uuid,
                    "run_id": run_id,
                    "source": source,
                    "study_id": study_id,
                    "swarm_stack_name": swarm_stack_name,
                    "user_id": "1",
                },
            }
        )

        # attach to volume and create some files!!!

        yield volume

        try:
            await volume.delete()
        except aiodocker.DockerError:
            pass


@pytest.fixture
async def used_volume(
    swarm_stack_name: str,
    study_id: str,
    node_uuid: str,
    run_id: str,
    used_volume_path: Path,
) -> AsyncIterator[DockerVolume]:
    async with aiodocker.Docker() as docker_client:
        source = _get_source(run_id, node_uuid, used_volume_path)
        volume = await docker_client.volumes.create(
            {
                "Name": source,
                "Labels": {
                    "node_uuid": node_uuid,
                    "run_id": run_id,
                    "source": source,
                    "study_id": study_id,
                    "swarm_stack_name": swarm_stack_name,
                    "user_id": "1",
                },
            }
        )

        container = await docker_client.containers.run(
            config={
                "Cmd": ["/bin/ash", "-c", "sleep 10000"],
                "Image": "alpine:latest",
                "HostConfig": {"Binds": [f"{volume.name}:{used_volume_path}"]},
            },
            name=f"using_volume_{volume.name}",
        )
        await container.start()

        yield volume

        await container.delete(force=True)
        await volume.delete()


@pytest.fixture
def minio_port() -> int:
    return 19000


@tenacity.retry(
    stop=tenacity.stop.stop_after_attempt(5), wait=tenacity.wait.wait_fixed(1)
)
async def _is_minio_responsive(endpoint: str, access_key: str, secret_key: str) -> None:
    session = aioboto3.Session(
        aws_access_key_id=access_key, aws_secret_access_key=secret_key
    )
    async with session.resource("s3", endpoint_url=endpoint, use_ssl=False) as s_3:
        bucket = await s_3.create_bucket(Bucket=f"test-bucket{uuid4()}")
        await bucket.delete()


@pytest.fixture
def minio_container_name() -> str:
    return "test_container_minio"


@pytest.fixture
async def remove_container(minio_container_name: str) -> AsyncIterator[None]:
    yield

    async with aiodocker.Docker() as docker_client:
        try:
            container = await docker_client.containers.get(minio_container_name)
            await container.stop()
            await container.delete(force=True)
        except aiodocker.DockerError:
            pass


@pytest.fixture
async def minio(
    remove_container: None, minio_port: int, minio_container_name: str
) -> AsyncIterator[dict]:
    access_key = f"{uuid4()}"
    secret_key = f"{uuid4()}"
    async with aiodocker.Docker() as docker_client:
        container = await docker_client.containers.run(
            config={
                "Cmd": ["server", "/data"],
                "Env": [
                    f"MINIO_ACCESS_KEY={access_key}",
                    f"MINIO_SECRET_KEY={secret_key}",
                ],
                "Image": "minio/minio:RELEASE.2020-05-16T01-33-21Z",
                "HostConfig": {
                    "PortBindings": {
                        "9000/tcp": [{"HostPort": f"{minio_port}", "HostIp": "0.0.0.0"}]
                    },
                },
            },
            name=minio_container_name,
        )
        await container.start()

        s3_access = {
            "endpoint": f"http://127.0.0.1:{minio_port}",
            "access_key": access_key,
            "secret_key": secret_key,
        }

        await _is_minio_responsive(
            endpoint=s3_access["endpoint"],
            access_key=s3_access["access_key"],
            secret_key=s3_access["secret_key"],
        )

        yield s3_access

        await container.stop()
        await container.delete(force=True)
