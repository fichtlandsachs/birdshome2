#!/bin/bash
INSTALL_USER='pi'
APP_USER='birdie'
SMB_USER='birdiesmb'
FLD_BIRDSHOME_ROOT='/etc/birdshome'
FLD_BIRDSHOME='/etc/birdshome/application'
FLD_BIRDSHOME_MEDIA='/etc/birdshome/application/static/media'
FLD_BIRDSHOME_SERV='/etc/systemd/system/birdshome.service'
SMB_CONF='/etc/samba/smb.conf'
SMB_CONF_TMP='/etc/samba/smb.conf.tmp'

echo "Installation User ID:"
read INSTALL_USER
echo "Please enter the password for the installation user";
stty -echo
read password_inst;
stty echo

echo "Application User ID:"
read APP_USER

echo "Please enter the password for the application user";
stty -echo
read password_app;
stty echo

echo $password_inst | su - "$INSTALL_USER" -c "sudo apt update && sudo apt -y upgrade"
# Install all required packages
echo $password_inst | su - "$INSTALL_USER" -c "sudo apt install -y samba gunicorn nginx build-essential libssl-dev libffi-dev libgstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good ffmpeg libilmbase-dev libopenexr-dev libopencv-dev libhdf5-dev libjasper-dev sqlite3  libatlas-base-dev portaudio19-dev python-all-dev software-properties-common ufw git"
echo $password_inst | su - "$INSTALL_USER" -c "sudo apt install -y python3-virtualenv python3-dev python3-pip python3-setuptools python3-venv python3-numpy"
#create the user for teh application
if id -u $APP_USER >/dev/null 2>&1; then
  echo "user $APP_USER exists"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo useradd -g users -G pi -m $APP_USER"
  echo $password_inst | su - "$INSTALL_USER" -c "sudo passwd $APP_USER"
  echo "user $APP_USER created"
fi
# switch to user context and create the virtual environment
echo $password_app | su - "$APP_USER" -c "cd ~ &"
echo $password_app | su - "$APP_USER" -c "virtualenv birdshome &"
echo $password_app | su - "$APP_USER" -c "source birdshome/bin/activate &"
echo $password_app | su - "$APP_USER" -c "git clone https://github.com/fichtlandsachs/birdshome2.git &"
echo $password_inst | su - "$INSTALL_USER" -c "sudo mv /home/birdie/birdshome2/* /etc/birdshome/ &"

# install required packages
#pip3 install flask werkzeug flask_RESTful flask-SQLAlchemy mpld3 pandas pyaudio
echo $password_app | su - "$APP_USER" -c "pip3 uninstall -y numpy &"
folder=$FLD_BIRDSHOME_ROOT'/requirements.txt'
echo $password_app | su - "$APP_USER" -c "pip3 install -r $folder &"
PID=$!
wait $PID
if [ $? -eq 0 ]; then
    echo "Python packages successfully installed"
fi

# create samba user
if id -u $SMB_USER >/dev/null 2>&1; then
  echo "user $SMB_USER exists"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo useradd -s /bin/false $SMB_USER"
  echo $password_inst | su - "$INSTALL_USER" -c "sudo smbpasswd -a $SMB_USER"
  echo "user $SMB_USER created"
fi

if [ ! -d "/etc/birdshome" ]; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo mkdir /etc/birdshome"
fi
echo $password_inst | su - "$INSTALL_USER" -c "sudo chown -R $APP_USER:$APP_USER $FLD_BIRDSHOME_ROOT"


# Überprüfen, ob die Datei existiert
if [ ! -f $SMB_CONF ]; then
    echo "Konfigurationsdatei $SMB_CONF nicht gefunden!"
    exit 1
fi

echo 'start to configure samba share'
echo $password_inst | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF.original"
echo 'samba.conf saved to smd.conf.original'
echo $password_inst | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF_TMP"
echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i 's/workgroup = .*$/workgroup = smb/' $SMB_CONF_TMP"
echo 'changed workgroup to smb'
echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i 's/security = .*$/security = user/' $SMB_CONF_TMP"
echo 'changed security to user'
echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i 's/map to guest = .*$/map to guest = never/' $SMB_CONF_TMP"
echo 'changed map to guest to never'

if ! grep -q '[bird_media]' $SMB_CONF_TMP; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i -e '$a\' -e '[bird_media]' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"path"'/' | grep -q "path"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a path='$FLD_BIRDSHOME_MEDIA $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s path= .*$/path ='$FLD_BIRDSHOME_MEDIA $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"public"'/' | grep -q "public"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a public = yes' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s public = .*$/public = yes' $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"writable"'/' | grep -q "writable"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a writable = yes' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s writable = .*$/writable = yes' $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"comment"'/' | grep -q "comment"; then
echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a comment = video share' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s comment = .*$/comment = video share' $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"printable"'/' | grep -q "printable"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a printable = no' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s printable = .*$/printable = no' $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"guest ok"'/' | grep -q "guest ok"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a guest ok = no' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s guest ok = .*$/guest ok = no' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"valid users"'/' | grep -q "valid users"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a valid users = '$SMB_USER', @'$SMB_USER $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s valid users = .*$/valid users = ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"write list"'/' | grep -q "write list"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a write list = '$SMB_USER', @'$SMB_USER $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s write list = .*$/write list = ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"create mask"'/' | grep -q "create mask"; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a create mask = 0600' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s create mask = .*$/create mask = 0600' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"directory mask "'/' | grep -q "directory mask "; then
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a directory mask = 0700' $SMB_CONF_TMP"
else
  echo $password_inst | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s directory mask = .*$/directory mask  = 0700' $SMB_CONF_TMP"
fi



mv $SMB_CONF_TMP $SMB_CONF
echo "configuration $SMB_CONF updated"
rm $SMB_CONF_TMP

echo $password_inst | su - "$INSTALL_USER" -c "touch  $FLD_BIRDSHOME_SERV"
PID=$!
wait $PID
if [ $? -eq 0 ]; then
    echo "File $FLD_BIRDSHOME_SERV created"
fi
if [ -f $FLD_BIRDSHOME_SERV ]; then
    echo "Konfigurationsdatei $FLD_BIRDSHOME_SERV angelegt!"
fi

echo $password_inst | su - "$INSTALL_USER" -c "echo [UNIT] >> /etc/systemd/system/birdshome.service &"
sed -i '/^\[Unit\]/a Description=birdhome Service' $FLD_BIRDSHOME_SERV
sed -i '/^\[Unit\]/a After=network.target' $FLD_BIRDSHOME_SERV
sed -i -e '$a\' -e '[Service]' $FLD_BIRDSHOME_SERV
sed -i '/^\[Service\]/a Type=simple' $FLD_BIRDSHOME_SERV
sed -i '/^\[Service\]/a User='$APP_USER $FLD_BIRDSHOME_SERV
sed -i '/^\[Service\]/a WorkingDirectory='$FLD_BIRDSHOME $FLD_BIRDSHOME_SERV
sed -i '/^\[Service\]/a Restart=always' $FLD_BIRDSHOME_SERV
sed -i '/^\[Service\]/a ExecStart=sh '$FLD_BIRDSHOME'/birds_dev.sh' $FLD_BIRDSHOME_SERV

sed -i -e '$a\' -e '[Install]' $FLD_BIRDSHOME_SERV
sed -i '/^\[Unit\]/a WantedBy=multi-user.target' $FLD_BIRDSHOME_SERV

echo 'service birdshome created'
systemctl daemon-reload
systemctl start birdshome.service
systemctl enable birdshome.service

if [ ! -f '/etc/nginx/sites-enabled/default' ]; then
    echo "Konfigurationsdatei /etc/nginx/sites-enabled/default gefunden!"
else
  unlink /etc/nginx/sites-enabled/default
fi

touch /etc/nginx/sites-available/reverse-proxy.conf
sed -i -e '$a\' -e 'server { \
        listen 80; \
        listen [::]:80; \
\
        access_log /var/log/nginx/reverse-access.log; \
        error_log /var/log/nginx/reverse-error.log; \
\
        location / {\
                    proxy_pass http://127.0.0.1:5000; \
  }' /etc/nginx/sites-available/reverse-proxy.conf
nginx -s reload

ufw allow 22/tcp
ufw allow 80
ufw allow 443/tcp
ufw allow 8443/tcp
ufw limit https
ufw reload
ufw enable
sudo systemctl restart smbd.service
systemctl start birdshome
