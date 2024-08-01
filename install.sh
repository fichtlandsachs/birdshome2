#!/bin/bash
INSTALL_USER='pi'
INST_USER_PWD=''
APP_USER=$(jq -r ".system.application_user" birdshome.json)
APP_USER_PWD=''
SMB_USER=$(jq -r ".system.samba_user" birdshome.json)
SMB_USER_PWD=''
LEGACY_ENABLED=true

REQUIRED_PACKAGES=("samba" "gunicorn" "nginx" "sqlite3" "build-essential" "libssl-dev" "libffi-dev"\
 "libgstreamer1.0-dev" "gstreamer1.0-plugins-base" "gstreamer1.0-plugins-good" "ffmpeg"\
  "libilmbase-dev" "libopenexr-dev" "libopencv-dev" "libhdf5-dev" "libjasper-dev" "libatlas-base-dev"\
  "portaudio19-dev" "software-properties-common" "ufw"  "libopenblas-dev" "jq")

FLD_BIRDSHOME_ROOT=$(jq -r ".system.application_root_folder" birdshome.json)
FLD_BIRDSHOME=$FLD_BIRDSHOME_ROOT+$(jq -r ".system.application_folder" birdshome.json)
FLD_BIRDSHOME_MEDIA=$FLD_BIRDSHOME_ROOT+$(jq -r ".system.application_media_folder" birdshome.json)
FLD_BIRDSHOME_SERV=$(jq -r ".system.application_startup_service" birdshome.json)
SMB_CONF=$(jq -r ".system.samba_config_file" birdshome.json)
SMB_CONF_TMP=$SMB_CONF'.tmp'
SECRET_KEY=$(tr -dc 'a-zA-Z0-9!§$%&/<>' < /dev/random | head -c 32)
LEGACY_ENABLED=false
SYSTEM_UPDATE=true
RUN_CLEANUP=false



installation_dialog(){
  CHOICE=$(whiptail --title "Install Setup" --menu "Choose options" 10 60 4  \
            "INST_SETUP" "Installation setup" \
            "APP_SETUP" "Application setup" \
            "SMB_SETUP" "Samba setup" \
            "RUN" "Start Installation process" \
              3>&1 1>&2 2>&3)
STATUS=$?
if [ $STATUS -eq 1 ]; then
	whiptail --title "Installation setup" --yesno "Do you want to exit the installation process?" 10 60
	if [ $? -eq 0 ]; then
		exit
	fi
else
    case "$CHOICE" in
    "INST_SETUP")
	    while true; do
      CHOICE_INST=$(whiptail --title "Install Setup" --menu "Choose options" 20 60 8 \
                    "1" "enable legacy camera support" \
                    "2" "Setup Installation user"\
                    "3" "Required applications"\
					"4" "Update system"\
                    "5" "Delete previous installation including data "\
                    3>&1 1>&2 2>&3)
				STATUS=$?
    if [ $STATUS -eq 1 ]; then
      break
    fi
		case "$CHOICE_INST" in
			"1")
				whiptail --title "Installation setup" --yesno "Legacy camera will be enabled" 10 60
				if [ $? -eq 0 ]; then
				  LEGACY_ENABLED=true
				else
				  LEGACY_ENABLED=false
				fi
			  ;;
			"2")
				# ask for user ID and validate if the user is in Group sudo
				  while true; do
					INSTALL_USER=$(whiptail --title "Installation user" --inputbox "Installation User ID:"\
					 10 60 "$INSTALL_USER" 3>&1 1>&2 2>&3)
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
					INST_USER_PWD=$(whiptail --title "Installation user" --passwordbox "Installation password:" 10 60 	"$INST_USER_PWD"  \
					3>&1 1>&2 2>&3)
					if [ $? -eq 0 ] && [ -z "$INST_USER_PWD" ]; then
					   whiptail --title "Installation user" --msgbox "Please provide a password" 10 60
					else
					  INSTALL_USER=""
					  break
					fi
				  done
				;;
			"3")
				for PACKAGE in "${REQUIRED_PACKAGES[@]}"; do
					CHECKLIST_ITEMS+=("$PACKAGE" "" "on")
				done
				whiptail --title "Application setup" --checklist "The following applications are installed \
				while running the setup process. \n\n " 30 60 15 "${CHECKLIST_ITEMS[@]}" 3>&1 1>&2 2>&3
			  ;;
			"4")
			  whiptail --title "Installation setup" --yesno "The system will be updated to the latest version.\n \
			   " 10 60
			  if [ $? -eq 0 ]; then
				SYSTEM_UPDATE=true
			  else
				SYSTEM_UPDATE=false
			  fi
			;;
			"5")
			  whiptail --title "Installation setup" --yesno "The prevoius installation of birdshome will be deleted.\n \
			  All data are lost.\n " 10 60
			  if [ $? -eq 0 ]; then
				RUN_CLEANUP=true
			  else
				RUN_CLEANUP=false
			  fi
			;;
			"6")
				break
			;;
		esac
		done
		;;
    "APP_SETUP")
      while true; do
        CHOICE_APP=$(whiptail --title "Install Setup" --menu "Choose options" 20 60 5 \
                        "1" "setup application user" \
                        "2" "Setup root folder"\
                        3>&1 1>&2 2>&3)
		if [ $STATUS -eq 1 ]; then
			break
		fi
        case $CHOICE_APP in
        # ask for user ID and will be created later on
            1)
            while true; do
            APP_USER=$(whiptail --title "Application user" --inputbox "Application User ID:" 10 60 "$APP_USER" \
            3>&1 1>&2 2>&3)
			# check return value and ask for password
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
			APP_USER_PWD=$(whiptail --title "Application user" --passwordbox "Application user password:" 10 60 ""\
			3>&1 1>&2 2>&3)
			if [ $? -eq 0 ] && [ -z "$APP_USER_PWD" ]; then
			   whiptail --title "Application user" --msgbox "Please provide a password" 10 60
			else
			  break
			fi
			done
			;;
			2)
			APP_ROOT=$(whiptail --title "Application root" --inputbox "Root path for the application:" 10 60 \
			"$FLD_BIRDSHOME_ROOT" 3>&1 1>&2 2>&3)
			  if [ $? -eq 0 ] && [ -z $APP_ROOT ]; then
				FLD_BIRDSHOME_ROOT=$APP_ROOT
				FLD_BIRDSHOME=$FLD_BIRDSHOME_ROOT+$(jq -r ".system.application_folder" birdshome.json)
				FLD_BIRDSHOME_MEDIA=$FLD_BIRDSHOME_ROOT+$(jq -r ".system.application_media_folder" birdshome.json)
			  fi
            ;;
          esac
        done
      ;;
		"SMB_SETUP")
		# ask for user ID and will be created later on
		  while true; do
			SMB_USER=$(whiptail --title "Samba user" --inputbox "Samba User ID:" 10 60 "" 3>&1 1>&2 2>&3)
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
			SMB_USER_PWD=$(whiptail --title "Samba user" --passwordbox "Samba user password:" 10 60 "$SMB_USER_PWD"\
			 3>&1 1>&2 2>&3)
			if [ $? -eq 0 ] && [ -z "$SMB_USER_PWD" ]; then
			   whiptail --title "Samba user" --msgbox "Please provide a password" 10 60
			else
			  break
			fi
		  done
		;;
		"RUN")
		  whiptail --title "Installation setup" --yesno "Do you want to start the installation?" 10 60
		  if [ $? -eq 0 ]; then
			  return
		  fi
		  ;;
		*)
		  echo "Unsupported item $CHOICE!" >&2
		  exit 1
		  ;;
		esac
fi
}
if [ -z $INSTALL_USER ]; then
  exit
fi
if [ -z "$APP_USER" ]; then
  whiptail --title "Application Setup" -msgbox "Will use the $INSTALL_USER as application user as well!" 0 60 3>&1 1>&2 2>&3
  APP_USER=$INSTALL_USER
  APP_USER_PWD=$INST_USER_PWD
fi
if [ -z "$SMB_USER" ]; then
  whiptail --title "Setup" -msgbox "Will use the $INSTALL_USER as samba user as well!" 0 60 3>&1 1>&2 2>&3
  SMB_USER=$INSTALL_USER
  SMB_USER_PWD=$INST_USER_PWD
fi

basic_setup(){
  #update the system to the latest patchset
  if $SYSTEM_UPDATE; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo apt update && sudo apt -y upgrade"
  fi
  # Install all required packages
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo apt install -y samba gunicorn nginx sqlite3 build-essential \
  libssl-dev libffi-dev libgstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good ffmpeg libilmbase-dev \
  libopenexr-dev libopencv-dev libhdf5-dev libjasper-dev   libatlas-base-dev portaudio19-dev  \
  software-properties-common ufw  libopenblas-dev jq"

}
user_setup(){
   #create the user for teh application
  if id -u "$APP_USER" >/dev/null 2>&1; then
    echo "user $APP_USER exists"
  else
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo useradd -g users -G pi -m $APP_USER"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo '$APP_USER:$APP_USER_PWD' | sudo chpasswd"
  fi

  if getent group "$APP_USER" >/dev/null; then
      echo "Group $APP_USER exists"
  else
      echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo groupadd $APP_USER"
      echo "Group $APP_USER created"
  fi
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo adduser $APP_USER dialout && sudo adduser $APP_USER users"
# create samba user
  if id -u $SMB_USER >/dev/null 2>&1; then
    echo "user $SMB_USER exists"
  else
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo useradd -s /bin/false $SMB_USER"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo '$APP_USER:$APP_USER_PWD' | sudo chpasswd"
    echo "user $SMB_USER created"
  fi
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo '$SMB_USER:$SMB_USER_PWD' | sudo smbpasswd"

}
prepare_system(){
  if [ -f "/etc/systemd/system/birdshome.service" ]; then
   echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo rm /etc/systemd/system/birdshome.service"
  fi
}
create_folder_structure(){
  if [ ! -d "$FLD_BIRDSHOME_ROOT" ]; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $FLD_BIRDSHOME_ROOT"
    echo "Folder $FLD_BIRDSHOME_ROOT created!"
  fi
  if [ ! -d "$FLD_BIRDSHOME" ]; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $FLD_BIRDSHOME"
    echo "Folder $FLD_BIRDSHOME created!"
  fi

}
copy_application(){
  source_folder="/home/$INSTALL_USER/birdshome2"
  file_arr=("$source_folder"'/*')

  for entry in ${file_arr[@]}; do
    copy_folder="$entry"
    file=$(basename $entry)
    target_folder="$FLD_BIRDSHOME_ROOT/$file"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "cp $copy_folder $target_folder"
  done
  source_folder="/home/$INSTALL_USER/birdshome2/application"
  folder_structure+=("/forms" "/handler" "/templates")

  # shellcheck disable=SC2068
  for entry in ${folder_structure[@]}; do
	copy_folder="$source_folder$entry/*"
	file_arr=("$copy_folder")
    for file_entry in ${file_arr[@]}; do
      file=$(basename $file_entry)
      target_folder="$FLD_BIRDSHOME/$entry/$file"
      echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "cp $file_entry $target_folder"
    done
  done
}
python_setup(){
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo apt install -y python3-virtualenv python3-dev python3-pip \
  python3-setuptools python3-venv python3-numpy python3-opencv python3-picamera2 libcamera-apps python-all-dev"
  echo "Change User context to $APP_USER"
  # switch to user context and create the virtual environment
  echo "$APP_USER_PWD" | su - "$APP_USER" -c "cd ~/"
  echo "$APP_USER_PWD" | su - "$APP_USER" -c "virtualenv ~/birdshome"
  sleep 5s
  echo "$APP_USER_PWD" | su - "$APP_USER" -c "source ~/birdshome/bin/activate"
  # install required packages
  #pip3 install flask werkzeug flask_RESTful flask-SQLAlchemy mpld3 pandas pyaudio
  echo "$APP_USER_PWD" | su - "$APP_USER" -c "pip3 uninstall -y numpy"
  folder=$FLD_BIRDSHOME_ROOT'/requirements.txt'
  echo "$APP_USER_PWD" | su - "$APP_USER" -c "pip3 install -r $folder"
  sleep 10s
  echo "Leaving App User Context"
}
samba_setup(){
  if [ ! -f $SMB_CONF ]; then
    echo "Configuration $SMB_CONF not found!"
    exit 1
fi
stty echo
echo 'start to configure samba share'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF.original"
echo 'samba.conf saved to smd.conf.original'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF_TMP"
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/workgroup = .*$/workgroup = workgroup/' $SMB_CONF_TMP"
echo 'changed workgroup to workgroup'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/security = .*$/security = user/' $SMB_CONF_TMP"
echo 'changed security to user'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/map to guest = .*$/map to guest = never/' $SMB_CONF_TMP"
echo 'changed map to guest to never'

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"path"'/' | grep -q "path"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a path='$FLD_BIRDSHOME_MEDIA $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s path= .*$/path ='$FLD_BIRDSHOME_MEDIA \
  $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"public"'/' | grep -q "public"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a public = yes' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s public = .*$/public = yes' $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"writable"'/' | grep -q "writable"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a writable = yes' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s writable = .*$/writable = yes' \
  $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"comment"'/' | grep -q "comment"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a comment = video share' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s comment = .*$/comment = video share' \
  $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"printable"'/' | grep -q "printable"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a printable = no' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s printable = .*$/printable = no' \
   $SMB_CONF_TMP"
fi

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"guest ok"'/' | grep -q "guest ok"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a guest ok = no' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s guest ok = .*$/guest ok = no' \
  $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"valid users"'/' | grep -q "valid users"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a valid users = $SMB_USER, @$SMB_USER' \
   $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s valid users = .*$/valid users = \
  ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"write list"'/' | grep -q "write list"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a write list = $SMB_USER, @$SMB_USER' \
  $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s write list = .*$/write list = \
  ${SMB_USER}, @${SMB_USER}' $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"create mask"'/' | grep -q "create mask"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a create mask = 0600' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s create mask = .*$/create mask = 0600' \
   $SMB_CONF_TMP"
fi
if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"directory mask "'/' | grep -q "directory mask "; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a directory mask = 0700' $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s directory mask = \
  .*$/directory mask  = 0700' $SMB_CONF_TMP"
fi
if ! grep -q '[bird_media]' $SMB_CONF_TMP; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a $SMB_CONF_TMP << EOF
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
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mv $SMB_CONF_TMP $SMB_CONF"
echo "configuration $SMB_CONF updated"
}
create_startup_service() {
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo touch  $FLD_BIRDSHOME_SERV"
if [ $? -eq 0 ]; then
    echo "File $FLD_BIRDSHOME_SERV created"
fi
if [ -f $FLD_BIRDSHOME_SERV ]; then
    echo "Konfigurationsdatei $FLD_BIRDSHOME_SERV angelegt!"
fi
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a $FLD_BIRDSHOME_SERV << EOF
[Unit]
Description=birdshome Service
After=network.target

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

echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a $FLD_BIRDSHOME_ROOT/birds_dev.sh << EOF
#source env/bin/activate
/bin/bash -c  'source /home/$APP_USER/birdshome/bin/activate'; exec /bin/bash -i
gunicorn3 --bind 0.0.0.0:5000 --threads 5 -w 1 --timeout 120 app:app
EOF"
echo $INST_USER_PWD | su - "$INSTALL_USER" -c "sudo chmod +x $FLD_BIRDSHOME_ROOT/birds_dev.sh"
}
update_nginx(){

if [ ! -f '/etc/nginx/sites-enabled/default' ]; then
    echo "Konfigurationsdatei /etc/nginx/sites-enabled/default gefunden!"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo unlink /etc/nginx/sites-enabled/default"
fi
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo touch /etc/nginx/sites-available/reverse-proxy.conf"
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a /etc/nginx/sites-available/reverse-proxy.conf << EOF
server {
        listen 80;
        listen [::]:80;

        access_log /var/log/nginx/reverse-access.log;
        error_log /var/log/nginx/reverse-error.log;

        location / {
                    proxy_pass http://127.0.0.1:5000;
  }
EOF"
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo nginx -s reload"
}
system_setup() {
  basic_setup
  user_setup
  prepare_system
  update_nginx
  samba_setup
  echo "Set up minimum firewall ports"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw allow 22/tcp"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw allow 80"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw allow 443/tcp"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw allow 8443/tcp"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw limit https"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw limit samba"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw reload"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo ufw --force enable"
  echo "Firewall setup and enabled"
}
start_system() {
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl daemon-reload"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl enable birdshome.service"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl start birdshome.service"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl restart smbd.service"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl restart nmbd.service"
  setup_raspberry
}
cleanup() {
  if [ $RUN_CLEANUP ]; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm -R -f /home/$INSTALL_USER/birdshome2"
    echo 'end'
  fi
}
cleanup_old_installation(){
  if [ -d "$FLD_BIRDSHOME_ROOT" ]; then
    echo 'existing installation found'
    echo "changed owner of folder '$FLD_BIRDSHOME_ROOT' to '$INSTALL_USER'"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chown -R $INSTALL_USER:$INSTALL_USER $FLD_BIRDSHOME_ROOT"

    for entry in $FLD_BIRDSHOME_ROOT'/*'; do
      if [ -f "$entry" ]; then
        echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $entry"
        echo "delete $entry"
      fi
    done
    for entry in $FLD_BIRDSHOME'/*'; do
      if [ -f "$entry" ]; then
        echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $entry"
      fi
    done
    for entry in $FLD_BIRDSHOME'/handler/*'; do
      if [ -f "$entry" ]; then
        echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $entry"
      fi
    done
    for entry in $FLD_BIRDSHOME'/forms/*'; do
      if [ -f "$entry" ]; then
        echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $entry"
      fi
    done
    for entry in $FLD_BIRDSHOME'/sensors/*'; do
      if [ -f "$entry" ]; then
        echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $entry"
      fi
    done
    for entry in $FLD_BIRDSHOME'/templates/*'; do
      if [ -f "$entry" ]; then
        echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $entry"
      fi
    done
  fi
}
setup_app_configuration() {
    echo 'start to configure application'
    existing_config="$FLD_BIRDSHOME_ROOT"/birdshome.json
    tmp_config="$FLD_BIRDSHOME_ROOT"/birdshome_tmp.json
    new_config="$FLD_BIRDSHOME_ROOT"/birdshome_new.json
    hostname=$(echo $HOSTNAME)
    echo "copy $existing_config to $new_config"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "cp $existing_config $new_config"
    #echo "adapt .system.application_user to $APP_USER in $new_config"
    command="jq '.system.application_user = \"$APP_USER\"' $new_config > $tmp_config && mv $tmp_config $new_config"
    #echo $command
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"
    #echo "adapt .system.secret_key to $SECRET_KEY in $new_config"
    command="jq '.system.secret_key = \"$SECRET_KEY\"' $new_config > $tmp_config && mv $tmp_config $new_config"
    #echo $command
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"
    #echo "adapt .video.video_prefix to $hostname in $new_config"
    command="jq '.video.video_prefix = \"$hostname'_'\"' $new_config > $tmp_config && mv $tmp_config $new_config"
    #echo $command
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "mv $new_config $existing_config"
    echo "/napp configuration adapted"
}
application_setup() {
    cleanup_old_installation
    create_folder_structure
    copy_application
    setup_app_configuration
    create_startup_service
    cleanup
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chown -R $APP_USER:$APP_USER $FLD_BIRDSHOME_ROOT"
}
setup_raspberry(){
  if $LEGACY_ENABLED; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/^#\?start_x=.*/start_x=1' /boot/config.txt"
    if [ $? -eq 0 ]; then
      echo 'failed to configure legacy camera'
      exit
    fi
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/^#\?gpu_mem=.*/gpu_mem=128' /boot/config.txt"
    if [ $? -eq 0 ]; then
      echo 'failed to configure legacy camera'
      exit
    fi
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sh -c 'echo \"overlay=vc4-fkms-v3d\" >> /boot/config.txt'"
    if [ $? -eq 0 ]; then
      echo 'failed to configure legacy camera'
      exit
    fi
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo reboot"
  fi
}

# first window with description of the installation dialog
#
# all steps have to be performed to make sure the the installation run successfully
# 1. Description
# 2. Installation user to be used
# 3. Application User to be setup
# 4. Information of packages to be installed
# 5. python packages to be installed based on requirements.txt
# 6. root folder to copy the files to
# 7. adapt the birdshome.json
# 8. create the samba folder and samba user for remote access
########################################################################################

while true; do

  whiptail --title "Installation Dialog" --yesno "The following dialog guides you through the installation of your birdhome.\
   The following steps will be performed: \n\n \
   1. provide the installation user used for running the installation\n (user with sudo privileges required) \n \
   2. Installation of all packages needed to run birdshome\n \
   3. Setup of the application user to run the application\n \
   4. Setup of the python environment based on the requirement.txt in\n	a virtual environment \n \
   5. creation of the folder structure \n \
   6. creation of the samba folder for file access including a samba user " 20 78
  STATUS=$?
    if [ $STATUS -eq 0 ]; then
      while true; do
        installation_dialog
      done
    else
      exit
    fi



done





#ask for user and required passwords to run the installation und setup user
installation_dialog
# setup the system user application etc
system_setup
application_setup
start_system