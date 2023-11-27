#!/bin/bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

python mdh.py -s

# if you use cloudflare tunnel
# sudo cloudflared service install <your tokens>
