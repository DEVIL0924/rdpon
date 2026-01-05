#!/bin/bash

############################################################
# CHROME REMOTE DESKTOP + XFCE AUTO SETUP
# FULL BLACK SCREEN + SOUND + FIREFOX FIX
############################################################

set -e

echo "🔥 Updating system..."
sudo apt update && sudo apt upgrade -y

echo "🖥️ Installing XFCE desktop..."
sudo apt install -y task-xfce-desktop xfce4 xfce4-goodies

echo "🧹 Removing GNOME (black screen fix)..."
sudo apt remove -y gnome-session gdm3 || true

echo "📦 Installing DBUS packages..."
sudo apt install -y dbus-x11 dbus-user-session
sudo systemctl enable dbus
sudo systemctl start dbus

echo "📡 Installing Chrome Remote Desktop..."
wget -q https://dl.google.com/linux/direct/chrome-remote-desktop_current_amd64.deb
sudo apt install -y ./chrome-remote-desktop_current_amd64.deb

echo "🧠 Fixing Chrome RDP session..."
cat <<EOF > ~/.chrome-remote-desktop-session
#!/bin/bash
unset DBUS_SESSION_BUS_ADDRESS
unset XDG_RUNTIME_DIR
exec /usr/bin/xfce4-session
EOF

chmod +x ~/.chrome-remote-desktop-session

echo "🔄 Restarting Chrome Remote Desktop service..."
sudo systemctl restart chrome-remote-desktop

############################################################
# 🔊 SOUND FIX
############################################################
echo "🔊 Installing sound support..."
sudo apt install -y pulseaudio pavucontrol
pulseaudio --start || true

############################################################
# 🌐 FIREFOX INSTALL (NO SNAP)
############################################################
echo "🌐 Installing Firefox..."
wget -q https://ftp.mozilla.org/pub/firefox/releases/128.0/linux-x86_64/en-US/firefox-128.0.tar.bz2
tar -xjf firefox-128.0.tar.bz2
sudo mv firefox /opt/firefox || true
sudo ln -sf /opt/firefox/firefox /usr/bin/firefox

############################################################
# FIREFOX DESKTOP ENTRY
############################################################
sudo tee /usr/share/applications/firefox.desktop > /dev/null <<EOF
[Desktop Entry]
Name=Firefox
Exec=/opt/firefox/firefox --no-remote
Icon=/opt/firefox/browser/chrome/icons/default/default128.png
Type=Application
Categories=Network;WebBrowser;
EOF

############################################################
# FIREFOX LOW RAM OPTIMIZATION
############################################################
echo 'export MOZ_USE_XINPUT2=1' >> ~/.bashrc
echo 'export MOZ_DISABLE_RDD_SANDBOX=1' >> ~/.bashrc

echo "✅ SETUP COMPLETE!"
echo "➡️ Now register Chrome Remote Desktop using the command below:"
echo ""
echo "DISPLAY= /opt/google/chrome-remote-desktop/start-host --code="4/0ATX87lPMghAyoeTUaXFSxOVHXcOuEXu1TA13ECmplGCrAk3uJIH5P5BX_0uHe4wEnuwTZg" --redirect-url="https://remotedesktop.google.com/_/oauthredirect" --name=$(hostname)



//command 
chmod +x rdp.sh
./rdp.sh


DISPLAY= /opt/google/chrome-remote-desktop/start-host --code="4/0ATX87lPAcdy6O58hAXNhxC9mj5OcT2cbQR7kN4TAnBozAGg4QGMuhuW08E5NlZ0rNZ9EuA" --redirect-url="https://remotedesktop.google.com/_/oauthredirect" --name=$(hostname)