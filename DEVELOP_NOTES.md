# Deployment
Press f1 in vs code and search "Run task", select it and you will the shell scripts from the VSCode appear.

First run make sure you have plugin_name.zip in the *out* folder, you can can create a local build using the build.sh script (or the vs code build commands)
Then you can deploy using the deploy.sh script you can deploy to your own steamdeck, make sure to configure the `settings.json` for the local SSH (and make sure SSH is running on the steam deck)

# Setup
Setup librespot library https://github.com/librespot-org/librespot

arch pacakges 
```bash
sudo pacman -S base-devel alsa-lib
```
