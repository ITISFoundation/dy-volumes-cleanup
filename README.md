# dy-volumes-cleanup

Tool for backing up and removing docker volumes starting with `dyv_`.

### Usage

```bash
docker run --rm \
    --volume /var/lib/docker/volumes/:/var/lib/docker/volumes/ \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    itisfoundation/dy-volumes-cleanup dyvc ${S3_ENDPOINT} ${S3_ACCESS_KEY} ${S3_SECRET_KEY} ${S3_BUCKET} ${S3_PROVIDER} --s3-region ${S3_REGION}
```


### For more details details run 

```bash
docker run --rm itisfoundation/dy-volumes-cleanup dyvc --help
```

```bash
dyvc --help

 Usage: dyvc [OPTIONS] S3_ENDPOINT S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET
             S3_PROVIDER:{AWS|CEPH|Minio}

╭─ Arguments ──────────────────────────────────────────────────────────────────────────╮
│ *    s3_endpoint        TEXT                          [default: None] [required]     │
│ *    s3_access_key      TEXT                          [default: None] [required]     │
│ *    s3_secret_key      TEXT                          [default: None] [required]     │
│ *    s3_bucket          TEXT                          [default: None] [required]     │
│ *    s3_provider        S3_PROVIDER:{AWS|CEPH|Minio}  [default: None] [required]     │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────╮
│ --s3-region                 TEXT  [default: us-east-1]                               │
│ --install-completion              Install completion for the current shell.          │
│ --show-completion                 Show completion for the current shell, to copy it  │
│                                   or customize the installation.                     │
│ --help                            Show this message and exit.                        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```