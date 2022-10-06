# pylint: disable=missing-module-docstring,missing-function-docstring,too-many-arguments,missing-class-docstring

import asyncio
import logging
from enum import Enum
from pathlib import Path

from tenacity import TryAgain
from tenacity._asyncio import AsyncRetrying
from tenacity.before_sleep import before_sleep_log
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random_exponential

logger = logging.getLogger(__name__)

R_CLONE_CONFIG = """
[dst]
type = s3
provider = {destination_provider}
access_key_id = {destination_access_key}
secret_access_key = {destination_secret_key}
endpoint = {destination_endpoint}
region = {destination_region}
acl = private
"""


class S3Provider(str, Enum):
    AWS = "AWS"
    CEPH = "CEPH"
    MINIO = "Minio"


def get_config_file_path(
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_region: str,
    s3_provider: S3Provider,
) -> Path:
    config_content = R_CLONE_CONFIG.format(
        destination_provider=s3_provider,
        destination_access_key=s3_access_key,
        destination_secret_key=s3_secret_key,
        destination_endpoint=s3_endpoint,
        destination_region=s3_region,
    )
    conf_path = Path("/tmp/rclone_config.ini")  # nosec
    conf_path.write_text(config_content)  # pylint:disable=unspecified-encoding
    return conf_path


def _get_s3_path(s3_bucket: str, labels: dict[str, str]) -> Path:
    joint_key = "/".join(
        (
            s3_bucket,
            labels["swarm_stack_name"],
            labels["study_id"],
            labels["node_uuid"],
            labels["run_id"],
        )
    )
    return Path(f"/{joint_key}")


async def store_to_s3(
    dyv_volume: dict,
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
    s3_region: str,
    s3_provider: S3Provider,
) -> None:
    config_file_path = get_config_file_path(
        s3_endpoint=s3_endpoint,
        s3_access_key=s3_access_key,
        s3_secret_key=s3_secret_key,
        s3_region=s3_region,
        s3_provider=s3_provider,
    )

    source_dir = dyv_volume["Mountpoint"]
    s3_path = _get_s3_path(s3_bucket, dyv_volume["Labels"])

    r_clone_command = [
        "rclone",
        "--config",
        f"{config_file_path}",
        "--low-level-retries",
        "3",
        "--retries",
        "3",
        "--transfers",
        "5",
        "sync",
        f"{source_dir}",
        f"dst:{s3_path}",
        "-P",
        # ignore files
        "--exclude",
        ".hidden_do_not_remove",
        "--exclude",
        "key_values.json",
    ]
    str_r_clone_command = " ".join(r_clone_command)
    print(r_clone_command)

    async for attempt in AsyncRetrying(
        wait=wait_random_exponential(),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    ):
        with attempt:
            process = await asyncio.create_subprocess_shell(
                str_r_clone_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await process.communicate()

            if process.returncode != 0:
                logger.warning(
                    "Could not finish\n%s\n%s", str_r_clone_command, stdout.decode()
                )
                raise TryAgain()
