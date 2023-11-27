#!/bin/bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared.deb

# if you use cloudflare tunnel
# cloudflared service install <your tokens>

python mdh.py -s
