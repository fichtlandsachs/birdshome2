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


CHOICES=$(whiptail --separate-output --checklist "Choose options" 10 35 5 \
  "1" "Set Installation User" ON \
  "2" "Set Application User" ON \
  "3" "Set Samba User" ON \
  "4" "The fourth option" OFF 3>&1 1>&2 2>&3)

if [ -z "$CHOICES" ]; then
  echo "No option was selected (user hit Cancel or unselected all options)"
else
  for CHOICE in $CHOICES; do
    case "$CHOICE" in
    "1")
    # ask for user ID and validate if the user is in Group sudo
      while true; do
        INSTALL_USER=$(whiptail --title "Installation user" --inputbox "Installation User ID:" 10 60 3>&1 1>&2 2>&3)
          if [ $? -eq 0 ]; then
            if [ -z "$INSTALL_USER" ]; then
              whiptail --title "Installation user" --msgbox "Please provide a valid user" 10 60
            else
              if ! getent group sudo | awk -F: '{print $4}' | grep -qw "$INSTALL_USER"; then
                whiptail --title "Installation user" --msgbox "Users permissions not sufficient" 10 60
              else
                break
              fi
            fi
          fi
      done
    # request the user password for installation reasons
      while true; do
        password_inst=$(whiptail --title "Installation user" --passwordbox "Installation password:" 10 60 \
        3>&1 1>&2 2>&3)
        if [ $? -eq 0 ] && [ -z "$password_inst" ]; then
           whiptail --title "Installation user" --msgbox "Please provide a password" 10 60
        else
          break
        fi
      done
    ;;
    "2")
    # ask for user ID and will be created later on
      while true; do
        APP_USER=$(whiptail --title "Application user" --inputbox "Application User ID:" 10 60 3>&1 1>&2 2>&3)
        if [ $? -eq 0 ]; then
          if [ -z "$APP_USER" ]; then
            whiptail --title "Application user" --msgbox "Please provide a valid user" 10 60
          else
           break
          fi
        fi
      done
    # request the user password for installation reasons
      while true; do
        password_app=$(whiptail --title "Application user" --passwordbox "Application user password:" 10 60 \
        3>&1 1>&2 2>&3)
        if [ $? -eq 0 ] && [ -z "$password_app" ]; then
           whiptail --title "Application user" --msgbox "Please provide a password" 10 60
        else
          break
        fi
      done
    ;;
    "3")
    # ask for user ID and will be created later on
      while true; do
        SMB_USER=$(whiptail --title "Samba user" --inputbox "Samba User ID:" 10 60 3>&1 1>&2 2>&3)
          if [ $? -eq 0 ]; then
            if [ -z "$SMB_USER" ]; then
              whiptail --title "Samba user" --msgbox "Please provide a valid user" 10 60
            else
              break
            fi
          fi
      done
    # request the user password for installation reasons
      while true; do
        password_smb=$(whiptail --title "Samba user" --passwordbox "Samba user password:" 10 60 \
        3>&1 1>&2 2>&3)
        if [ $? -eq 0 ] && [ -z "$password_smb" ]; then
           whiptail --title "Samba user" --msgbox "Please provide a password" 10 60
        else
          break
        fi
      done
    ;;
    "4")
      echo "Option 4 was selected"
      ;;
    *)
      echo "Unsupported item $CHOICE!" >&2
      exit 1
      ;;
    esac
  done
fi

if [ -z $INSTALL_USER ]; then
  exit
fi
if [ -z "$APP_USER" ]; then
  whiptail --title "Application Setup" -msgbox "Will use the $INSTALL_USER as application user as well!" 0 60 3>&1 1>&2 2>&3
fi
if [ -z "$SMB_USER" ]; then
  whiptail --title "Setup" -msgbox "Will use the $INSTALL_USER as samba user as well!" 0 60 3>&1 1>&2 2>&3
fi
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo apt update && sudo apt -y upgrade"
# Install all required packages
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo apt install -y samba gunicorn nginx build-essential \
libssl-dev libffi-dev libgstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good ffmpeg libilmbase-dev \
libopenexr-dev libopencv-dev libhdf5-dev libjasper-dev sqlite3  libatlas-base-dev portaudio19-dev python-all-dev \
software-properties-common ufw  libopenblas-dev"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo apt install -y python3-virtualenv python3-dev python3-pip \
python3-setuptools python3-venv python3-numpy python3-opencv"
#create the user for teh application
if id -u "$APP_USER" >/dev/null 2>&1; then
  echo "user $APP_USER exists"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo useradd -g users -G pi -m $APP_USER"
  echo "$password_inst" | su - "$INSTALL_USER" -c "echo '$APP_USER:$password_app' | sudo chpasswd"
fi

if getent group "$APP_USER" >/dev/null; then
    echo "Group $APP_USER exists"
else
    echo "$password_inst" | su - "$INSTALL_USER" -c "sudo groupadd $APP_USER"
    echo "Group $APP_USER created"
fi

echo "$password_inst" | su - "$INSTALL_USER" -c "sudo adduser $APP_USER dialout && sudo adduser $APP_USER users"

if [ ! -d "/etc/birdshome" ]; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo mkdir $FLD_BIRDSHOME_ROOT"
  echo "Folder $FLD_BIRDSHOME_ROOT created!"
fi
if [ -f "/etc/systemd/system/birdshome.service" ]; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo rm /etc/systemd/system/birdshome.service"
fi
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo mv /home/$INSTALL_USER/birdshome2/* /etc/birdshome/"

sleep 2s
# create samba user
if id -u $SMB_USER >/dev/null 2>&1; then
  echo "user $SMB_USER exists"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo useradd -s /bin/false $SMB_USER"
  echo "$password_inst" | su - "$INSTALL_USER" -c "echo '$APP_USER:$password_app' | sudo chpasswd"
  echo "user $SMB_USER created"
fi
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo chown -R $APP_USER:$APP_USER $FLD_BIRDSHOME_ROOT"
stty -echo
echo "Change User context to $APP_USER"
# switch to user context and create the virtual environment
echo "$password_app" | su - "$APP_USER" -c "cd ~/"
echo "$password_app" | su - "$APP_USER" -c "virtualenv ~/birdshome"
sleep 5s
echo "$password_app" | su - "$APP_USER" -c "source ~/birdshome/bin/activate"
# install required packages
#pip3 install flask werkzeug flask_RESTful flask-SQLAlchemy mpld3 pandas pyaudio
echo "$password_app" | su - "$APP_USER" -c "pip3 uninstall -y numpy"
folder=$FLD_BIRDSHOME_ROOT'/requirements.txt'
echo "$password_app" | su - "$APP_USER" -c "pip3 install -r $folder"
sleep 10s
echo "Leaving App User Context"


echo "$password_inst" | su - "$INSTALL_USER"
# Überprüfen, ob die Datei existiert
if [ ! -f $SMB_CONF ]; then
    echo "Configuration $SMB_CONF not found!"
    exit 1
fi
stty echo
echo 'start to configure samba share'
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF.original"
echo 'samba.conf saved to smd.conf.original'
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF_TMP"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i 's/workgroup = .*$/workgroup = workgroup/' $SMB_CONF_TMP"
echo 'changed workgroup to workgroup'
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i 's/security = .*$/security = user/' $SMB_CONF_TMP"
echo 'changed security to user'
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i 's/map to guest = .*$/map to guest = never/' $SMB_CONF_TMP"
echo 'changed map to guest to never'

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"path"'/' | grep -q "path"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a path='$FLD_BIRDSHOME_MEDIA $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s path= .*$/path ='$FLD_BIRDSHOME_MEDIA \
  $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"public"'/' | grep -q "public"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a public = yes' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s public = .*$/public = yes' $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"writable"'/' | grep -q "writable"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a writable = yes' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s writable = .*$/writable = yes' \
  $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"comment"'/' | grep -q "comment"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a comment = video share' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s comment = .*$/comment = video share' \
  $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"printable"'/' | grep -q "printable"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a printable = no' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s printable = .*$/printable = no' \
   $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"guest ok"'/' | grep -q "guest ok"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a guest ok = no' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s guest ok = .*$/guest ok = no' \
  $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"valid users"'/' | grep -q "valid users"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a valid users = $SMB_USER, @$SMB_USER' \
   $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s valid users = .*$/valid users = \
  ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"write list"'/' | grep -q "write list"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a write list = $SMB_USER, @$SMB_USER' \
  $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s write list = .*$/write list = \
  ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"create mask"'/' | grep -q "create mask"; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a create mask = 0600' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s create mask = .*$/create mask = 0600' \
   $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"directory mask "'/' | grep -q "directory mask "; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a directory mask = 0700' $SMB_CONF_TMP"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s directory mask = \
  .*$/directory mask  = 0700' $SMB_CONF_TMP"
fi
if ! grep -q '[bird_media]' $SMB_CONF_TMP; then
  echo "$password_inst" | su - "$INSTALL_USER" -c "sudo tee -a $SMB_CONF_TMP << EOF
[bird_media]
   path=$FLD_BIRDSHOME_MEDIA
   public = yes
   writable = yes
   comment = video share
   printable = no
   guest ok = no
   valid users = $SMB_USER, @$SMB_USER
EOF"
fi


echo "$password_inst" | su - "$INSTALL_USER" -c "sudo mv $SMB_CONF_TMP $SMB_CONF"
echo "configuration $SMB_CONF updated"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo rm $SMB_CONF_TMP"

echo "$password_inst" | su - "$INSTALL_USER" -c "sudo touch  $FLD_BIRDSHOME_SERV"
PID=$!
wait $PID
if [ $? -eq 0 ]; then
    echo "File $FLD_BIRDSHOME_SERV created"
fi
if [ -f $FLD_BIRDSHOME_SERV ]; then
    echo "Konfigurationsdatei $FLD_BIRDSHOME_SERV angelegt!"
fi

echo "$password_inst" | su - "$INSTALL_USER" -c "sudo tee -a $FLD_BIRDSHOME_SERV << EOF
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
EOF"

echo 'service birdshome created'
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo systemctl daemon-reload"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo systemctl start birdshome.service"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo systemctl enable birdshome.service"

if [ ! -f '/etc/nginx/sites-enabled/default' ]; then
    echo "Konfigurationsdatei /etc/nginx/sites-enabled/default gefunden!"
else
  echo "$password_inst" | su - "$INSTALL_USER" -c "unlink /etc/nginx/sites-enabled/default"
fi

echo "$password_inst" | su - "$INSTALL_USER" -c "sudo touch /etc/nginx/sites-available/reverse-proxy.conf"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo tee -a /etc/nginx/sites-available/reverse-proxy.conf << EOF
server {
        listen 80;
        listen [::]:80;

        access_log /var/log/nginx/reverse-access.log;
        error_log /var/log/nginx/reverse-error.log;

        location / {
                    proxy_pass http://127.0.0.1:5000;
  }
EOF"

echo "$password_inst" | su - "$INSTALL_USER" -c "sudo tee -a $FLD_BIRDSHOME_ROOT/birds_dev.sh << EOF
#source env/bin/activate
/bin/bash -c  source /home/$APP_USER/birdshome/bin/activate; exec /bin/bash -i
gunicorn3 --bind 0.0.0.0:5000 --threads 5 -w 1 --timeout 120 app:app
deactivate
EOF"
echo $password_inst | su - "$INSTALL_USER" -c "sudo chmod +x $FLD_BIRDSHOME_ROOT/birds_dev.sh"

echo "$password_inst" | su - "$INSTALL_USER" -c "sudo nginx -s reload"

echo "Set up minimum firewall ports"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw allow 22/tcp"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw allow 80"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw allow 443/tcp"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw allow 8443/tcp"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw limit https"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw limit samba"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw reload"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo ufw --force enable"
echo "Firewall setup and enabled"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo systemctl restart smbd.service"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo systemctl restart nmbd.service"
echo "$password_inst" | su - "$INSTALL_USER" -c "sudo systemctl start birdshome"
echo "$password_inst" | su - "$INSTALL_USER" -c "cd ~"
echo "$password_inst" | su - "$INSTALL_USER" -c "rm -R -f /home/$INSTALL_USER/birdshome2"