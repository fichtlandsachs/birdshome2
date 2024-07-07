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
secret_key=$(tr -dc 'a-zA-Z0-9!§$%&/<>' < /dev/random | head -c 32)

wiptail --title "Nutzersetup"
INSTALL_USER=$(whiptail "Installation User ID:" 10 30 3>&1 1>&2 2>&3)

# request user for the installation process
echo "Installation User ID: \c"
read -r INSTALL_USER
echo "Please enter the password for the installation user: \c"
stty -echo
read -r password_inst
stty echo
if ! getent group sudo | awk -F: '{print $4}' | grep -qw "$INSTALL_USER"; then
  echo "\n\nInstalluser is not assigned to group sudoer"
  echo "\nInstallation aborted"
  exit
fi
# request the new application user
echo "\nApplication User ID: \c"
read -r APP_USER
echo "Please enter the password for the application user: \c"
stty -echo
read -r password_app;
stty echo

# last but not least request the user to set up the samba share
echo "\nSamba User ID: \c"
read -r SMB_USER
echo "Please enter the password for the samba user: \c"
stty -echo
read -r password_smb;
stty echo
stty -echo
# start updateing the system using the install user
echo $password_inst | su -l "$INSTALL_USER"
stty echo
cd ~

sudo apt update && sudo apt -y upgrade
# Install all required packages
sudo apt install -y samba gunicorn nginx build-essential libssl-dev libffi-dev libgstreamer1.0-dev \
 gstreamer1.0-plugins-base gstreamer1.0-plugins-good ffmpeg libilmbase-dev libopenexr-dev libopencv-dev \
 libhdf5-dev libjasper-dev sqlite3  libatlas-base-dev portaudio19-dev python-all-dev software-properties-common ufw \
 libopenblas-dev
sudo apt install -y python3-virtualenv python3-dev python3-pip python3-setuptools python3-venv python3-numpy \
  python3-opencv
#create the user for teh application
if id -u $APP_USER >/dev/null 2>&1; then
  echo "user $APP_USER exists"
else
  sudo useradd -g users -G pi -m $APP_USER
  echo $password_app |   sudo passwd $APP_USER
  echo "user $APP_USER created"
fi

if getent group "$APP_USER" >/dev/null; then
    echo "Group $APP_USER exists"
else
    sudo groupadd $APP_USER
    echo "Group $APP_USER created"
fi

sudo adduser $APP_USER dialout
sudo adduser $APP_USER users

if [ ! -d "/etc/birdshome" ]; then
  sudo mkdir $FLD_BIRDSHOME_ROOT
  echo "Folder $FLD_BIRDSHOME_ROOT created!"
fi

sudo rm /etc/systemd/system/birdshome.service
sudo mv /home/$INSTALL_USER/birdshome2/* /etc/birdshome/

sleep 2s
# create samba user
if id -u $SMB_USER >/dev/null 2>&1; then
  echo "user $SMB_USER exists"
else
  sudo useradd -s /bin/false $SMB_USER
  echo $password_smb | sudo passwd $SMB_USER
  echo "user $SMB_USER created"
fi
sudo chown -R $APP_USER:$APP_USER $FLD_BIRDSHOME_ROOT
stty -echo
echo "Change User context to $APP_USER"
echo $password_app | su - "$APP_USER"
# switch to user context and create the virtual environment
echo $password_app | su - "$APP_USER" -c "cd ~/"
echo $password_app | su - "$APP_USER" -c "virtualenv ~/birdshome"
sleep 5s
echo $password_app | su - "$APP_USER" -c "source ~/birdshome/bin/activate"
# install required packages
#pip3 install flask werkzeug flask_RESTful flask-SQLAlchemy mpld3 pandas pyaudio
echo $password_app | su - "$APP_USER" -c "pip3 uninstall -y numpy"
folder=$FLD_BIRDSHOME_ROOT'/requirements.txt'
echo $password_app | su - "$APP_USER" -c "pip3 install -r $folder"
sleep 10s
echo "Leaving App User Context"


echo $password_inst | su - "$INSTALL_USER"
# Überprüfen, ob die Datei existiert
if [ ! -f $SMB_CONF ]; then
    echo "Configuration $SMB_CONF not found!"
    exit 1
fi
stty echo
echo 'start to configure samba share'
sudo cp $SMB_CONF $SMB_CONF.original
echo 'samba.conf saved to smd.conf.original'
sudo cp $SMB_CONF $SMB_CONF_TMP
sudo sed -i 's/workgroup = .*$/workgroup = workgroup/' $SMB_CONF_TMP
echo 'changed workgroup to workgroup'
sudo sed -i 's/security = .*$/security = user/' $SMB_CONF_TMP
echo 'changed security to user'
sudo sed -i 's/map to guest = .*$/map to guest = never/' $SMB_CONF_TMP
echo 'changed map to guest to never'

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"path"'/' | grep -q "path"; then
  sudo sed -i '/^\[bird_media\]/a path='$FLD_BIRDSHOME_MEDIA $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s path= .*$/path ='$FLD_BIRDSHOME_MEDIA $SMB_CONF_TMP
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"public"'/' | grep -q "public"; then
  sudo sed -i '/^\[bird_media\]/a public = yes' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s public = .*$/public = yes' $SMB_CONF_TMP
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"writable"'/' | grep -q "writable"; then
  sudo sed -i '/^\[bird_media\]/a writable = yes' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s writable = .*$/writable = yes' $SMB_CONF_TMP
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"comment"'/' | grep -q "comment"; then
  sudo sed -i '/^\[bird_media\]/a comment = video share' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s comment = .*$/comment = video share' $SMB_CONF_TMP
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"printable"'/' | grep -q "printable"; then
  sudo sed -i '/^\[bird_media\]/a printable = no' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s printable = .*$/printable = no' $SMB_CONF_TMP
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"guest ok"'/' | grep -q "guest ok"; then
  sudo sed -i '/^\[bird_media\]/a guest ok = no' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s guest ok = .*$/guest ok = no' $SMB_CONF_TMP
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"valid users"'/' | grep -q "valid users"; then
  sudo sed -i '/^\[bird_media\]/a valid users = $SMB_USER, @$SMB_USER' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s valid users = .*$/valid users = ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"write list"'/' | grep -q "write list"; then
  sudo sed -i '/^\[bird_media\]/a write list = $SMB_USER, @$SMB_USER' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s write list = .*$/write list = ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"create mask"'/' | grep -q "create mask"; then
  sudo sed -i '/^\[bird_media\]/a create mask = 0600' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s create mask = .*$/create mask = 0600' $SMB_CONF_TMP
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"directory mask "'/' | grep -q "directory mask "; then
  sudo sed -i '/^\[bird_media\]/a directory mask = 0700' $SMB_CONF_TMP
else
  sudo sed -i '/^\[bird_media\]/s directory mask = .*$/directory mask  = 0700' $SMB_CONF_TMP
fi
if ! grep -q '[bird_media]' $SMB_CONF_TMP; then
  sudo tee -a $SMB_CONF_TMP << EOF
[bird_media]
   path=$FLD_BIRDSHOME_MEDIA
   public = yes
   writable = yes
   comment = video share
   printable = no
   guest ok = no
   valid users = $SMB_USER, @$SMB_USER
EOF
fi


sudo mv $SMB_CONF_TMP $SMB_CONF
echo "configuration $SMB_CONF updated"
sudo rm $SMB_CONF_TMP

sudo touch  $FLD_BIRDSHOME_SERV
PID=$!
wait $PID
if [ $? -eq 0 ]; then
    echo "File $FLD_BIRDSHOME_SERV created"
fi
if [ -f $FLD_BIRDSHOME_SERV ]; then
    echo "Konfigurationsdatei $FLD_BIRDSHOME_SERV angelegt!"
fi

sudo tee -a $FLD_BIRDSHOME_SERV << EOF
[Unit]
Description=birdhome Service
After=network.target'

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$FLD_BIRDSHOME_ROOT
Restart=always
ExecStart=sh $FLD_BIRDSHOME_ROOT/birds_dev.sh

[Install]
WantedBy=multi-user.target
EOF

echo 'service birdshome created'
sudo systemctl daemon-reload
sudo systemctl start birdshome.service
sudo systemctl enable birdshome.service

if [ ! -f '/etc/nginx/sites-enabled/default' ]; then
    echo "Konfigurationsdatei /etc/nginx/sites-enabled/default gefunden!"
else
  unlink /etc/nginx/sites-enabled/default
fi

sudo touch /etc/nginx/sites-available/reverse-proxy.conf
sudo tee -a /etc/nginx/sites-available/reverse-proxy.conf << EOF
server {
        listen 80;
        listen [::]:80;

        access_log /var/log/nginx/reverse-access.log;
        error_log /var/log/nginx/reverse-error.log;

        location / {
                    proxy_pass http://127.0.0.1:5000;
  }
EOF

sudo tee -a $FLD_BIRDSHOME_ROOT/birds_dev.sh << EOF
#source env/bin/activate
/bin/bash -c  "source /home/$APP_USER/birdshome/bin/activate; exec /bin/bash -i"
gunicorn3 --bind 0.0.0.0:5000 --threads 5 -w 1 --timeout 120 app:app
deactivate
EOF
sudo chmod +x $FLD_BIRDSHOME_ROOT/birds_dev.sh

sudo nginx -s reload

echo "Set up minimum firewall ports"
sudo ufw allow 22/tcp
sudo ufw allow 80
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp
sudo ufw limit https
sudo ufw limit samba
sudo ufw reload
sudo ufw --force enable
echo "Firewall setup and enabled"
sudo systemctl restart smbd.service
sudo systemctl restart nmbd.service
sudo systemctl start birdshome
cd ~
rm -R -f /home/$INSTALL_USER/birdshome2
