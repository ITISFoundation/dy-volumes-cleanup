# dy-volumes-cleanup

Tool for backing up and removing docker volumes starting with `dyv_`.

### Usage

```bash
docker run --rm --pull always \
    --volume /var/lib/docker/volumes/:/var/lib/docker/volumes/ \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    itisfoundation/osparc-ops-dy-volumes-cleanup dyvc ${S3_ENDPOINT} ${S3_ACCESS_KEY} ${S3_SECRET_KEY} ${S3_BUCKET} ${S3_PROVIDER} --s3-region ${S3_REGION}
```

#### About volume mounts:

The `docker.sock` is required

The `/var/lib/docker/volumes/` refers to where the docker volumes data is currently stored. And the same path
should be mounted inside the container.
If the docker data is in `/docker` the mount will change to `--volume /docker/volumes/:/docker/volumes/`.


### For more details details run 

```bash
dyvc --help

 Usage: dyvc [OPTIONS] S3_ENDPOINT S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET
             S3_PROVIDER:{AWS|CEPH|Minio}

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────╮
│ *    s3_endpoint        TEXT                          [default: None] [required]               │
│ *    s3_access_key      TEXT                          [default: None] [required]               │
│ *    s3_secret_key      TEXT                          [default: None] [required]               │
│ *    s3_bucket          TEXT                          [default: None] [required]               │
│ *    s3_provider        S3_PROVIDER:{AWS|CEPH|Minio}  [default: None] [required]               │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────╮
│ --s3-region                 TEXT     [default: us-east-1]                                      │
│ --s3-retries                INTEGER  upload retries in case of error [default: 3]              │
│ --s3-parallelism            INTEGER  parallel transfers to s3 [default: 5]                     │
│ --exclude-files             TEXT     Files to ignore when syncing to s3                        │
│                                      [default: .hidden_do_not_remove, key_values.json]         │
│ --install-completion                 Install completion for the current shell.                 │
│ --show-completion                    Show completion for the current shell, to copy it or      │
│                                      customize the installation.                               │
│ --help                               Show this message and exit.                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
```