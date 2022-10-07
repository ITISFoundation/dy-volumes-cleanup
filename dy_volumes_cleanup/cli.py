import asyncio
import logging

import typer

from ._docker import delete_volume, docker_client, get_dyv_volumes, is_volume_used
from ._s3 import S3Provider, store_to_s3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def async_entrypoint(
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
    s3_region: str,
    s3_provider: S3Provider,
) -> None:
    async with docker_client() as client:
        dyv_volumes: list[dict] = await get_dyv_volumes(client)

        for dyv_volume in dyv_volumes:
            volume_name = dyv_volume["Name"]

            if await is_volume_used(client, volume_name):
                typer.echo(f"Skipped in use volume: '{volume_name}'")
                continue

            await store_to_s3(
                dyv_volume=dyv_volume,
                s3_endpoint=s3_endpoint,
                s3_access_key=s3_access_key,
                s3_secret_key=s3_secret_key,
                s3_bucket=s3_bucket,
                s3_region=s3_region,
                s3_provider=s3_provider,
            )
            typer.echo(f"Backed up volume: '{volume_name}'")

            await delete_volume(client, volume_name)
            typer.echo(f"Removed volume: '{volume_name}'")


app = typer.Typer()


@app.command()
def main(
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
    s3_provider: S3Provider,
    s3_region: str = "us-east-1",
):
    asyncio.get_event_loop().run_until_complete(
        async_entrypoint(
            s3_endpoint=s3_endpoint,
            s3_access_key=s3_access_key,
            s3_secret_key=s3_secret_key,
            s3_bucket=s3_bucket,
            s3_provider=s3_provider,
            s3_region=s3_region,
        )
    )
