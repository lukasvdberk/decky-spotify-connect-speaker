# we support images for building with a vanilla SteamOS base,
# or versions with ootb support for rust or go
# developers can also customize these images via this Dockerfile
#FROM ghcr.io/steamdeckhomebrew/holo-toolchain-rust:latest
#FROM ghcr.io/steamdeckhomebrew/holo-toolchain-go:latest
FROM ghcr.io/steamdeckhomebrew/holo-base:latest

# Install zstd for extracting Arch packages
RUN pacman -Sy --noconfirm zstd curl

# entrypoint.sh should always be located in the backend folder
ENTRYPOINT [ "/backend/entrypoint.sh" ]