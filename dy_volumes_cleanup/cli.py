import asyncio
import logging

import typer

from ._docker import delete_volume, docker_client, get_dyv_volumes, is_volume_used
from ._s3 import S3Provider, store_to_s3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FILES_TO_EXCLUDE: list[str] = [
    ".hidden_do_not_remove",
    "key_values.json",
]


async def async_entrypoint(
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
    s3_region: str,
    s3_provider: S3Provider,
    s3_retries: int,
    s3_parallelism: int,
    exclude_files: list[str],
) -> None:
    async with docker_client() as client:
        dyv_volumes: list[dict] = await get_dyv_volumes(client)

        if len(dyv_volumes) == 0:
            return

        typer.echo(
            f"The dy-sidecar volume cleanup detected {len(dyv_volumes)} "
            "zombie volumes on the current machine."
        )
        typer.echo("Beginning cleanup.")
        for dyv_volume in dyv_volumes:
            volume_name = dyv_volume["Name"]

            if await is_volume_used(client, volume_name):
                typer.echo(f"Skipped in use docker volume: '{volume_name}'")
                continue

            await store_to_s3(
                dyv_volume=dyv_volume,
                s3_endpoint=s3_endpoint,
                s3_access_key=s3_access_key,
                s3_secret_key=s3_secret_key,
                s3_bucket=s3_bucket,
                s3_region=s3_region,
                s3_provider=s3_provider,
                s3_retries=s3_retries,
                s3_parallelism=s3_parallelism,
                exclude_files=exclude_files,
            )
            typer.echo(
                "Succesfully pushed data to S3 for zombie dynamic sidecar "
                f"docker volume: '{volume_name}'"
            )

            await delete_volume(client, volume_name)
            typer.echo(f"Removed docker volume: '{volume_name}'")


app = typer.Typer()


@app.command()
def main(
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
    s3_provider: S3Provider,
    s3_region: str = "us-east-1",
    s3_retries: int = typer.Option(3, help="upload retries in case of error"),
    s3_parallelism: int = typer.Option(5, help="parallel transfers to s3"),
    exclude_files: list[str] = typer.Option(
        FILES_TO_EXCLUDE, help="Files to ignore when syncing to s3"
    ),
):
    asyncio.get_event_loop().run_until_complete(
        async_entrypoint(
            s3_endpoint=s3_endpoint,
            s3_access_key=s3_access_key,
            s3_secret_key=s3_secret_key,
            s3_bucket=s3_bucket,
            s3_provider=s3_provider,
            s3_region=s3_region,
            s3_retries=s3_retries,
            s3_parallelism=s3_parallelism,
            exclude_files=exclude_files,
        )
    )
