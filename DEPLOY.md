# Deployment

The site is served by nginx from a single Azure VM. Pages are static HTML built
through `site/layout.html`, which installs GTM once for every current and future
page. Public assets live in `public/`.

## Infrastructure

| | |
|---|---|
| Subscription | `Azure subscription 1` (id via `az account show --query id -o tsv`) |
| Resource group | `alma-landing-rg` |
| Region | `eastus` |
| VM | `alma-landing-vm` — `Standard_B1ls` (1 vCPU / 512 MB), Ubuntu 24.04 LTS |
| Disk | 30 GB StandardSSD_LRS |
| Public IP | **`168.61.34.144`** — Standard SKU, **static** (`alma-landing-ip`) |
| Open ports | 22, 80, 443 (NSG `alma-landing-vmNSG`) |
| SSH | `ssh azureuser@168.61.34.144` (key: `~/.ssh/id_rsa`) |

### Paths on the VM

| | |
|---|---|
| Webroot | `/var/www/alma` (owned by `www-data`) |
| nginx vhost | `/etc/nginx/sites-available/alma` → symlinked into `sites-enabled/` |
| Certs | `/etc/letsencrypt/live/alma.inc/` |

A copy of the live vhost is checked in at [`deploy/nginx-alma.conf`](deploy/nginx-alma.conf).
It is a *snapshot*, not the source of truth — the blocks marked `# managed by
Certbot` were rewritten in place during issuance, and certbot may rewrite them
again on renewal. Re-snapshot after any certbot run that touches the config:

```sh
ssh azureuser@168.61.34.144 'sudo cat /etc/nginx/sites-available/alma' > deploy/nginx-alma.conf
```

## DNS

Registrar is **Porkbun**. Both records are plain `A` records at the static IP:

```
A    alma.inc        168.61.34.144
A    www.alma.inc    168.61.34.144
```

No CAA records are set, so any CA may issue.

## TLS

Let's Encrypt via certbot 2.9.0, issued 2026-07-20 for `alma.inc` + `www.alma.inc`
(single cert, both names in the SAN). `--redirect` is enabled, so HTTP 301s to
HTTPS.

Renewal is handled by the `certbot.timer` systemd unit (enabled and active).
`certbot renew --dry-run` passes, so the renewal path is verified — not just
scheduled.

Verify current state:

```sh
ssh azureuser@168.61.34.144 'sudo certbot certificates'
echo | openssl s_client -servername alma.inc -connect alma.inc:443 2>/dev/null \
  | openssl x509 -noout -dates
```

ACME account email is `thegreataffan@gmail.com` — it receives expiry warnings.
Change with `sudo certbot update_account --email <addr>`.

## Deploying content changes

```sh
./deploy.sh            # deploy the current working tree
./deploy.sh --pull     # git pull --ff-only first, then deploy
```

The script builds the site into a temporary directory, syncs only that generated
output, then verifies every file over HTTPS by comparing checksums. It exits
non-zero if any file fails to match, so a silent partial deploy is not possible.

No nginx reload is needed for content-only changes — nginx reads from disk per
request.

Three things the script handles that manual `scp` did not:

- **HTML comes only from `site/pages/`.** Each page is wrapped by the shared
  layout and receives both GTM snippets. Assets come only from `public/`.
- **`.well-known` is protected from `--delete`.** It is not in the repo, so an
  unguarded `rsync --delete` would remove it and break certificate renewal.
- **Repo docs and tooling are excluded by construction.** Only generated pages
  and `public/` are staged, so `DEPLOY.md`, backend code, scripts, and templates
  cannot accidentally be served.

  Note this repo is **public**: keep credentials and the Azure subscription id
  out of it. Real secrets live only in `/etc/alma-backend.env` on the VM.

## Waitlist backend (Django + unfold)

The waitlist form POSTs to `/waitlist`, served by a Django app; the admin panel
(django-unfold) lives at `/admin/`. Code is in [`backend/`](backend/) — tracked
in the repo but excluded from the static deploy.

| | |
|---|---|
| Database | Azure PostgreSQL Flexible Server `alma-landing-db` (**centralus** — eastus/eastus2 were restricted), `Standard_B1ms`, Postgres 16 |
| DB host | `alma-landing-db.postgres.database.azure.com`, database `waitlist`, user `almaadmin` |
| DB firewall | allows only the VM's static IP `168.61.34.144`; TLS required (`sslmode=require`) |
| App on VM | `/opt/alma-backend` (venv inside), gunicorn on `127.0.0.1:8000` |
| Service | `alma-backend.service` (systemd, runs as `www-data`) — unit checked in at [`deploy/alma-backend.service`](deploy/alma-backend.service) |
| Secrets | `/etc/alma-backend.env` (root-only, 600): `DJANGO_SECRET_KEY`, `DB_PASSWORD`, `DB_HOST`, … |
| nginx | `snippets/alma-backend-locations.conf` included in the HTTPS server block proxies `/waitlist`, `/admin/`, `/static/`; `conf.d/alma-ratelimit.conf` rate-limits signups (10/min/IP) |

Deploy backend changes:

```sh
rsync -az --delete --exclude venv --exclude staticfiles --exclude '__pycache__' \
  backend/ azureuser@168.61.34.144:/opt/alma-backend/
ssh azureuser@168.61.34.144 'cd /opt/alma-backend \
  && ./venv/bin/pip -q install -r requirements.txt \
  && sudo -E ./venv/bin/python manage.py migrate --no-input \
  && ./venv/bin/python manage.py collectstatic --no-input \
  && sudo systemctl restart alma-backend'
```

(`manage.py` commands need the env file: `set -a; . /etc/alma-backend.env; set +a`
first when running by hand.)

Admin panel: `https://alma.inc/admin/` — Django auth, superuser `alma`.
Create/reset users with `manage.py createsuperuser` / `changepassword` on the VM.

## Gotchas

**Do not remove `/swapfile`.** `Standard_B1ls` has only ~394 MB usable RAM and no
swap by default. The original cloud-init run was SIGTERM'd partway through `apt`
because of this, and nginx/certbot never installed — while `cloud-init status`
still reported `done`, so the failure was silent. A 2 GB swapfile (in
`/etc/fstab`, `vm.swappiness=10`) fixes it. Certbot is Python and will OOM on
renewal without it. If you'd rather not depend on swap, `Standard_B1s` (1 GB) is
the next size up.

**Leave port 80 open.** Renewal uses the `--nginx` authenticator over HTTP-01 on
port 80. Closing it breaks renewal even though the site is HTTPS-only from a
visitor's perspective. The 301 redirect does not interfere — certbot serves the
challenge before the redirect applies.

**Don't retry certbot blindly on failure.** Let's Encrypt rate-limits to 5 failed
validations per hostname per hour. Use `--dry-run` (staging, not rate-limited) to
debug, then run for real once it passes.

**Check DNS before issuing.** The apex initially still pointed at Porkbun's
parking IPs (`207.207.210.x`) while only `www` had been updated. Issuing in that
state would have failed the `alma.inc` challenge and errored the whole request:

```sh
dig +short @8.8.8.8 alma.inc A      # both must return 168.61.34.144
dig +short @8.8.8.8 www.alma.inc A
```

## Rebuilding from scratch

```sh
az group create --name alma-landing-rg --location eastus
az network public-ip create --resource-group alma-landing-rg --name alma-landing-ip \
  --sku Standard --allocation-method Static --version IPv4
az vm create --resource-group alma-landing-rg --name alma-landing-vm \
  --image Ubuntu2404 --size Standard_B1ls --admin-username azureuser \
  --ssh-key-values ~/.ssh/id_rsa.pub --public-ip-address alma-landing-ip \
  --public-ip-sku Standard --os-disk-size-gb 30 --storage-sku StandardSSD_LRS \
  --nsg-rule SSH
az network nsg rule create --resource-group alma-landing-rg \
  --nsg-name alma-landing-vmNSG --name AllowHTTP --priority 1010 \
  --destination-port-ranges 80 --protocol Tcp --access Allow --direction Inbound
az network nsg rule create --resource-group alma-landing-rg \
  --nsg-name alma-landing-vmNSG --name AllowHTTPS --priority 1020 \
  --destination-port-ranges 443 --protocol Tcp --access Allow --direction Inbound
```

Then on the VM: add the swapfile *first*, then
`apt-get install -y nginx certbot python3-certbot-nginx`, drop in the vhost, copy
the files, and run
`certbot --nginx -d alma.inc -d www.alma.inc --redirect`.

A note on ordering: installing packages via cloud-init `packages:` is what failed
originally. Add swap before any `apt` work on this VM size.

## Teardown

```sh
az group delete --name alma-landing-rg --yes
```

This deletes the VM, disk, NIC, NSG, vnet, **and the static IP** — you would not
get `168.61.34.144` back.
