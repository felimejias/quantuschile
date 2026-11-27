# Preator routing repair — deployed 2026-11-27

GET /preator/da/login returned 404 on the physical gateway while Oracle and Azure returned 200. All three cloudflared replicas were receiving traffic. The physical gateway lacked Preator locations, including its static assets.

Applied with operator authorization:

1. Changed only the www.quantuschile.cl tunnel origin from http://100.93.88.89:80 to http://127.0.0.1:80; preserved the www Host override and other ingress entries. All three connectors acknowledged configuration version 5.
2. Backed up and disabled quantus-tunnel-hotstandby.service on Oracle, then Azure; removed the artificial 100.93.88.89/32 loopback alias. This restores replies to the physical gateway over Tailscale. No Tailscale authentication, firewall policy or application credentials changed.
3. Added gateway-preator.conf locations to the www server of /opt/quantus/nginx/quantus.conf, copied from the working Oracle configuration. Preserved the single-file Docker mount inode. nginx -t and graceful reload passed.

Candidate was syntax-checked as a complete configuration and exercised through an isolated Nginx listener at 127.0.0.1:18086 within the existing container network. Login, CSS, logo and icon returned 200 before production reload. The temporary test process was stopped afterward.

After deployment, Oracle, Azure and gateway return 200 for login, CSS and logo, with identical content hashes. Public login and trailing-slash redirect, CSS, logo and icons pass. Home and /app respond 200 on all three nodes. These are HTTP/rendering checks; no customer login or transaction was performed. Confirmation from the originally affected networks remains a user-side check.

Gateway backup: /opt/quantus/nginx/quantus.conf.bak_preator_20261127T1815Z.
Before SHA256: 7e3efc472b5789b036654a9c3dcd6e432365468c2cf33e1aab72b97e3d2b913f.
After SHA256: 595c5427f0cbec94f7fbeebab4f92173c064123ed014c8ba6887849a266e9df2.
Cloud unit backups: /etc/systemd/system/quantus-tunnel-hotstandby.service.bak_preator_20261127.

Rollback gateway only after comparing the deployed hash: restore backup bytes into the existing inode, nginx -t, then graceful reload. This reintroduces the original missing routes. Do not restore the obsolete tunnel destination without coordinated aliases; do not recreate aliases under the corrected ingress because they intercept real gateway return traffic.
