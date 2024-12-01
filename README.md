# grok-dns
A script that updates Cloudflare DNS entries, wrapped in a Nix flake. Used for my blog, grok.zone and gentmantan.com

## Description
For machines connected to residental or mobile network connections, the public facing IP address is probably not static. Therefore, it is essential to have something constantly monitor and update the DNS records to point to the correct IP address, lest services will be inaccessable via domain name.
This script takes a Cloudflare API key and changes A and AAAA records to match the public IPv4 and IPv6 addresses of the machine it is running on. It is meant to be run on the same machine that is facing the internet.
The script is meant to be run on a NixOS machine using `nix`, to ensure that python runs in the right environment. Frankly, using poetry for dependency management seems overkill for just a small script... but flakes are cool, and using this follows the reproducable and pure spirit of Nix.

## Usage
1. Clone the repo
2. Run `nix run <path to flake directory> -- <arguments>`
It's best to create a systemd service that will run the script periodically

## Alternatives
You can also choose to run the script by itself in a docker/podman container, with the correct [dependencies](./pyproject.toml) installed.

## Credits
[The Nix python template](https://github.com/NixOS/templates)
