#!/bin/bash
INSTALL_USER='pi'
INST_USER_PWD=''
APP_USER=$(jq -r ".system.application_user" birds_home.json)
APP_USER_PWD=''
SMB_USER=$(jq -r ".system.samba_user" birds_home.json)
SMB_USER_PWD=''
LEGACY_ENABLED=true
START_INSTALL=false
install_steps=0

REQUIRED_PACKAGES=("samba" "gunicorn" "nginx" "sqlite3" "build-essential" "libssl-dev" "libffi-dev"\
 "libgstreamer1.0-dev" "gstreamer1.0-plugins-base" "gstreamer1.0-plugins-good" "ffmpeg"\
  "libopencv-dev" "libhdf5-dev" "libatlas-base-dev"\
  "portaudio19-dev" "software-properties-common" "ufw"  "libopenblas-dev")

FLD_BIRDS_HOME_ROOT=$(jq -r ".system.application_root_folder" birds_home.json)
FLD_BIRDS_HOME="$FLD_BIRDS_HOME_ROOT""$(jq -r '.system.application_folder' birds_home.json)"
FLD_BIRDS_HOME_MEDIA="$FLD_BIRDS_HOME_ROOT""$(jq -r '.system.application_media_folder' birds_home.json)"
FLD_BIRDS_HOME_SERV=$(jq -r ".system.application_startup_service" birds_home.json)
SMB_CONF=$(jq -r ".system.samba_config_file" birds_home.json)
SMB_CONF_TMP=$SMB_CONF'.tmp'
SECRET_KEY=$(tr -dc 'a-zA-Z0-9!§$%&/<>' < /dev/random | head -c 32)
LEGACY_ENABLED=false
SYSTEM_UPDATE=true
RUN_CLEANUP=false


validate_installation_dialog(){
  if [ -z "$INSTALL_USER" ]; then
    whiptail --title "Installation Setup" --msgbox "Install user is missing!" 0 60
    START_INSTALL=false
  else
	START_INSTALL=true
  fi
  if [ -z "$INST_USER_PWD" ]; then
    whiptail --title "Installation Setup" --msgbox "Install user password is missing!" 0 60
    START_INSTALL=false
  else
	START_INSTALL=true
  fi
  if [ -z "$APP_USER" ]; then
    if whiptail --title "Application Setup" --yesno  "Will use the $INSTALL_USER as application user as well!" 0 60; then
          APP_USER=$INSTALL_USER
          APP_USER_PWD=$INST_USER_PWD
		  START_INSTALL=true
    else
      START_INSTALL=false
    fi
  fi
  if [ -z "$APP_USER_PWD" ]; then
    whiptail --title "Application Setup" --yesno  "App user password is missing" 0 60
    START_INSTALL=false
  else
	START_INSTALL=true
  fi
  if [ -z "$SMB_USER" ]; then
    if whiptail --title "Samba Setup" --yesno  "Will use the $INSTALL_USER as samba user as well!" 0 60; then
        SMB_USER=$INSTALL_USER
        SMB_USER_PWD=$INST_USER_PWD
		START_INSTALL=true
    else
      START_INSTALL=false
    fi
  fi
  if [ -z "$SMB_USER_PWD" ]; then
    whiptail --title "Samba Setup" --msgbox "Samba user password is missing" 0 60
    START_INSTALL=false
  else
	START_INSTALL=true
  fi

}
installation_dialog(){
	CHOICE=$(whiptail --title "Install Setup" --menu "Choose options" 10 60 4  \
				"INST_SETUP" "Installation setup" \
				"APP_SETUP" "Application setup" \
				"SMB_SETUP" "Samba setup" \
				"RUN" "Start Installation process" \
				  3>&1 1>&2 2>&3)
	STATUS=$?
	if [ $STATUS -eq 1 ]; then
		return 6
	elif [ $STATUS -eq 0 ] && [ -z "$CHOICE" ]; then
		return 6
	else

    case "$CHOICE" in
    "INST_SETUP")
		while true; do
		  CHOICE_INST=$(whiptail --title "Install Setup" --menu "Choose options" 20 60 8 \
			  "1" "Setup Installation user"\
			  "2" "enable legacy camera support"\
			  "3" "Required applications"\
			  "4" "Update system"\
			  "5" "Delete previous installation including data "\
			  "6" "<< Back"\
			  3>&1 1>&2 2>&3)
			STATUS=$?
			if [ $STATUS -eq "1" ]; then
			  return 1
			elif [ "$CHOICE_INST" -eq "6" ]; then
			  return 1
			fi
			case "$CHOICE_INST" in
				"1")
					# ask for user ID and validate if the user is in Group sudo
					while true; do
						INSTALL_USER=$(whiptail --title "Installation user" --inputbox "Installation User ID:" 10 60 "$INSTALL_USER" 3>&1 1>&2 2>&3)
					  if [ -z "$INSTALL_USER" ]; then
						  whiptail --title "Installation user" --msgbox "Please provide a valid user" 10 60
					  else
						if ! getent group sudo | awk -F: '{print $4}' | grep -qw "$INSTALL_USER"; then
						  whiptail --title "Installation user" --msgbox "User is not in list of sudoer" 10 60
						else
						  break
						fi
					  fi
					done
					# request the user password for installation reasons
					while true; do
						INST_USER_PWD=$(whiptail --title "Installation user" --passwordbox "Installation password:" 10 60 3>&1 1>&2 2>&3)
						if [ -z "$INST_USER_PWD" ]; then
						   whiptail --title "Installation user" --msgbox "Please provide a password" 10 60
						else
						  break
						fi
					done
					;;
				"2")
					if whiptail --title "Installation setup" --yesno "Legacy camera will be enabled" 10 60; then
					  LEGACY_ENABLED=true
					else
					  LEGACY_ENABLED=false
					fi
					;;
				"3")
					for PACKAGE in "${REQUIRED_PACKAGES[@]}"; do
						CHECKLIST_ITEMS+=("$PACKAGE" "" "on")
					done
					whiptail --title "Application setup" --checklist "The following applications are installed \
					while running the setup process. \n\n " 30 60 15 "${CHECKLIST_ITEMS[@]}" 3>&1 1>&2 2>&3
					;;
				"4")
					if whiptail --title "Installation setup" --yesno "The system will be updated to the latest version." 10 60; then
					  SYSTEM_UPDATE=true
					else
					  SYSTEM_UPDATE=false
					fi
					;;
				"5")
					if whiptail --title "Installation setup" --yesno "The previous installation of birds_home will be deleted.\n \
					All data are lost.\n" 10 60; then
					  RUN_CLEANUP=true
					else
					  RUN_CLEANUP=false
					fi
					;;
				"6")

					;;
			esac
		done
		;;
    "APP_SETUP")
      while true; do
        CHOICE_APP=$(whiptail --title "Install Setup" --menu "Choose options" 20 60 5 \
                        "1" "setup application user" \
                        "2" "Setup root folder"\
                        "3" "<< Back"\
                        3>&1 1>&2 2>&3)
        STATUS=$?
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
          if [ -z "$APP_USER" ]; then
              whiptail --title "Application user" --msgbox "Please provide a valid user" 10 60
          else
             APP_USER_PWD=$(whiptail --title "Application user" --passwordbox "Application user password:" 10 60 ""\
              3>&1 1>&2 2>&3)
            if [ -z "$APP_USER_PWD" ]; then
            # request the user password for setup reasons
              whiptail --title "Application user" --msgbox "Please provide a password" 10 60
            else
              break
            fi
          fi
          done
        ;;
			  2)
			    APP_ROOT=$(whiptail --title "Application root" --inputbox "Root path for the application:" 10 60 \
			              "$FLD_BIRDS_HOME_ROOT" 3>&1 1>&2 2>&3)
            if [ -z "$APP_ROOT" ]; then
              FLD_BIRDS_HOME_ROOT=$APP_ROOT
              FLD_BIRDS_HOME=$FLD_BIRDS_HOME_ROOT+$(jq -r ".system.application_folder" birds_home.json)
              FLD_BIRDS_HOME_MEDIA=$FLD_BIRDS_HOME_ROOT+$(jq -r ".system.application_media_folder" birds_home.json)
            fi
            ;;
          3)
			return
			;;
          esac

		done
		;;
	"SMB_SETUP")
		# ask for user ID and will be created later on
		  while true; do
			SMB_USER=$(whiptail --title "Samba user" --inputbox "Samba User ID:" 10 60 "" 3>&1 1>&2 2>&3)
				if [ -z "$SMB_USER" ]; then
				  whiptail --title "Samba user" --msgbox "Please provide a valid user" 10 60
				else
				  break
			  fi
		  done
		# request the user password for installation reasons
		  while true; do
			SMB_USER_PWD=$(whiptail --title "Samba user" --passwordbox "Samba user password:" 10 60 "$SMB_USER_PWD"\
			 3>&1 1>&2 2>&3)
			if [ -z "$SMB_USER_PWD" ]; then
			   whiptail --title "Samba user" --msgbox "Please provide a password" 10 60
			else
			  break
			fi
		  done
		;;
	"RUN")
		if whiptail --title "Installation setup" --yesno "Do you want to start the installation?" 10 60; then
		validate_installation_dialog
		  if $START_INSTALL ; then
			return
		  fi
		fi
	  ;;
	*)
	  echo "Unsupported item $CHOICE!" >&2
	  exit 1
	  ;;
	esac
fi
}
basic_setup(){
  #update the system to the latest patchset
  if $SYSTEM_UPDATE; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo apt update && sudo apt -y upgrade"
    install_steps+=1
  fi
  # Install all required packages
	command="sudo apt install -y "

	for PACK in "${REQUIRED_PACKAGES[@]}"; do
			command+="$PACK "
	done
	command="${command% }"

  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo apt autoremove -y"
  install_steps+=1
}
user_setup(){
   #create the user for teh application
  if id -u "$APP_USER" >/dev/null 2>&1; then
    echo "user $APP_USER exists"
  else
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo useradd -g users -G pi -m $APP_USER"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo '$APP_USER:$APP_USER_PWD' | sudo chpasswd"
  fi
  install_steps+=1

  if getent group "$APP_USER" >/dev/null; then
      echo "Group $APP_USER exists"
  else
      echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo groupadd $APP_USER"
      echo "Group $APP_USER created"
  fi
  install_steps+=1
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo adduser $APP_USER dialout && sudo adduser $APP_USER users"
# create samba user
  if id -u "$SMB_USER" >/dev/null 2>&1; then
    echo "user $SMB_USER exists"
  else
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo useradd -s /bin/false $SMB_USER"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo '$APP_USER:$APP_USER_PWD' | sudo chpasswd"
    echo "user $SMB_USER created"
  fi
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo '$SMB_USER:$SMB_USER_PWD' | sudo smbpasswd"
install_steps+=1

}
prepare_system(){
  if [ -f "/etc/systemd/system/birds_home.service" ]; then
   echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo rm /etc/systemd/system/birds_home.service"
  fi
  install_steps+=1
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
create_folder_structure(){
  if [ ! -d "$FLD_BIRDS_HOME_ROOT" ]; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $FLD_BIRDS_HOME_ROOT"
    echo "Folder $FLD_BIRDS_HOME_ROOT created!"
  fi
install_steps+=1
  if [ ! -d "$FLD_BIRDS_HOME" ]; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $FLD_BIRDS_HOME"
    echo "Folder $FLD_BIRDS_HOME created!"
  fi
  folder_structure=$(jq -r ".folder_structure" birds_home.json)
echo
	path=$(jq -r ".folder_structure.output_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.database_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.media_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.replay_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.picture_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.video_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.screenshot_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.vid_analyser_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.picture_personas" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi
	path=$(jq -r ".folder_structure.log_file_folder" birds_home.json)
	target_folder="$FLD_BIRDS_HOME/$path"
	if [ ! -d target_folder ]; then
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo mkdir $target_folder"
		echo "Folder $target_folder created!"
	fi

install_steps+=1
}
copy_application(){
  source_folder="/home/$INSTALL_USER/birdshome2"
  target_folder="$FLD_BIRDS_HOME_ROOT"
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo 	cp -rv '$source_folder'/* '$target_folder'"
  install_steps+=1
}
python_setup(){
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo apt install -y python3-full python3-virtualenv python3-dev python3-pip \
  python3-setuptools python3-venv python3-numpy python3-opencv python3-picamera2 libcamera-apps "
  echo "Change User context to $APP_USER"
  venv_dir="/home/"$APP_USER"/birds_home/"
  command="sudo -u '$APP_USER' -i << EOF

  # Überprüfen, ob das Verzeichnis bereits existiert
  if [ -d $venv_dir ]; then
      echo 'Das virtuelle Umfeld existiert bereits.'
  else
      echo 'Erstelle das virtuelle Umfeld...'
      python3 -m venv $venv_dir
      echo 'Virtuelles Umfeld erstellt in \$venv_dir'
  fi

  # Aktivieren des virtuellen Umfelds
  source $venv_dir/bin/activate
  pip3 uninstall -y numpy
  pip install -r /etc/birds_home/requirements.txt
  echo 'Virtuelles Umfeld aktiviert. Sie befinden sich nun im virtuellen Umfeld.'
  EOF"

echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"

  install_steps+=1
  # switch to user context and create the virtual environment
  #echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "cd ~/"
  #echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo python3 -m venv /home/'$APP_USER'/birds_home"
  #echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chown -R  '$APP_USER':'$APP_USER' /home/'$APP_USER'/"
  #sleep 5s
  #echo "$APP_USER_PWD" | su - "$APP_USER" -c "source /home/"$APP_USER"/birds_home/bin/activate"
  install_steps+=1
  # install required packages
  ##pip3 install flask werkzeug flask_RESTful flask-SQLAlchemy mpld3 pandas pyaudio
  #echo "$APP_USER_PWD" | su - "$APP_USER" -c "pip3 uninstall -y numpy"
  #install_steps+=1
  #folder=$FLD_BIRDS_HOME_ROOT'/requirements.txt'
  #echo "$APP_USER_PWD" | su - "$APP_USER" -c "pip3 install -r $folder"
  install_steps+=1
  sleep 10s
  echo "Leaving App User Context"
}
samba_setup(){
  if [ ! -f "$SMB_CONF" ]; then
    echo "Configuration $SMB_CONF not found!"
    exit 1
fi
stty echo
echo 'start to configure samba share'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF.original"
install_steps+=1
echo 'samba.conf saved to smd.conf.original'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo cp $SMB_CONF $SMB_CONF_TMP"
install_steps+=1
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/workgroup = .*$/workgroup = workgroup/' $SMB_CONF_TMP"
install_steps+=1
echo 'changed workgroup to workgroup'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/security = .*$/security = user/' $SMB_CONF_TMP"
install_steps+=1
echo 'changed security to user'
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i 's/map to guest = .*$/map to guest = never/' $SMB_CONF_TMP"
install_steps+=1
echo 'changed map to guest to never'

if ! grep -A 100 "^\[bird_media\]" "$SMB_CONF_TMP" | awk '/^\[/{exit} /'"path"'/' | grep -q "path"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/a path='$FLD_BIRDS_HOME_MEDIA $SMB_CONF_TMP"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo sed -i '/^\[bird_media\]/s path= .*$/path ='$FLD_BIRDS_HOME_MEDIA \
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
if ! grep -q '[bird_media]' "$SMB_CONF_TMP"; then
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a $SMB_CONF_TMP << EOF
[bird_media]
   path=$FLD_BIRDS_HOME_MEDIA
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
install_steps+=1
}
create_startup_service() {
  result=$(echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo touch  $FLD_BIRDS_HOME_SERV")
  if [ -f $FLD_BIRDS_HOME_SERV ]; then
      echo "File $FLD_BIRDS_HOME_SERV created"
  fi
  install_steps+=1
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a $FLD_BIRDS_HOME_SERV << EOF
[Unit]
Description=birds_home Service
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$FLD_BIRDS_HOME_ROOT
Restart=always
ExecStart=sh $FLD_BIRDS_HOME_ROOT/birds_dev.sh

[Install]
WantedBy=multi-user.target
EOF"
echo 'service birds_home created'

echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo tee -a $FLD_BIRDS_HOME_ROOT/birds_dev.sh << EOF
#source env/bin/activate
/bin/bash -c  'source /home/$APP_USER/birds_home/bin/activate'; exec /bin/bash -i
gunicorn3 --bind 0.0.0.0:5000 --threads 5 -w 1 --timeout 120 app:app
EOF"
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chmod +x $FLD_BIRDS_HOME_ROOT/birds_dev.sh"
install_steps+=1
}
update_nginx(){

if [ ! -f '/etc/nginx/sites-enabled/default' ]; then
    echo "Konfigurationsdatei /etc/nginx/sites-enabled/default gefunden!"
else
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo unlink /etc/nginx/sites-enabled/default"
fi
install_steps+=1
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
install_steps+=1
echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo nginx -s reload"
install_steps+=1
}
system_setup() {
  basic_setup
  user_setup
  update_nginx
  samba_setup
  prepare_system
  install_steps+=1
}
start_system() {
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl daemon-reload"
  install_steps+=1
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl enable birds_home.service"
  install_steps+=1
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl start birds_home.service"
  install_steps+=1
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl restart smbd.service"
  install_steps+=1
  echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo systemctl restart nmbd.service"
  install_steps+=1
  setup_raspberry
}
cleanup() {
  if [ $RUN_CLEANUP ]; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm -R -f /home/$INSTALL_USER/birdshome2"
    echo 'end'
  fi
  install_steps+=1
}
cleanup_old_installation(){
  if [ -d "$FLD_BIRDS_HOME_ROOT" ]; then
    echo 'existing installation found'
    echo "changed owner of folder '$FLD_BIRDS_HOME_ROOT' to '$INSTALL_USER'"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chown -R $INSTALL_USER:$INSTALL_USER $FLD_BIRDS_HOME_ROOT"
	echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo rm -R $FLD_BIRDS_HOME_ROOT"
  fi
}
setup_app_configuration() {
    echo 'start to configure application'
    existing_config="$FLD_BIRDS_HOME_ROOT"/birds_home.json
    tmp_config="$FLD_BIRDS_HOME_ROOT"/birds_home_tmp.json
    new_config="$FLD_BIRDS_HOME_ROOT"/birds_home_new.json
    hostname=$HOSTNAME
	echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chown -R $INSTALL_USER:$INSTALL_USER $FLD_BIRDS_HOME_ROOT"
    result=$(echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "cp $existing_config $new_config")

    command="jq '.system.application_user = \"$INSTALL_USER\"' $new_config > $tmp_config && cp $tmp_config $new_config"

    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"

    command="jq '.system.secret_key = \"$SECRET_KEY\"' $new_config > $tmp_config && cp $tmp_config $new_config"

    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"

    command="jq '.video.video_prefix = \"$hostname'_'\"' $new_config > $tmp_config && cp $tmp_config $new_config"

    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "$command"
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "mv $new_config $existing_config"

    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "rm $tmp_config"
    echo "/napp configuration adapted"

}
application_setup() {
    cleanup_old_installation
    create_folder_structure
    copy_application
    setup_app_configuration
    python_setup
    create_startup_service
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo chown -R $APP_USER:$APP_USER $FLD_BIRDS_HOME_ROOT"
    install_steps+=1
}
setup_raspberry(){
  if $LEGACY_ENABLED; then
    echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo raspi-config nonint do_camera 1"
	if ! grep -q "start_x=1" /boot/config.txt; then
		result=$(echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo 'start_x=1' | sudo tee -a /boot/config.txt")
	fi
	if ! grep -q "gpu_mem=.*" /boot/config.txt; then
		result=$(echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "echo 'gpu_mem=128' | sudo tee -a /boot/config.txt")
	fi
    install_steps+=1
	if whiptail --title "Installation setup" --yesno "Do you want to restart?" 10 60; then
	  whiptail --title "Installation setup" --msgbox  "The server will be restarted and is ready to use" 10 60
		echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo reboot"
	else
	  whiptail --title "Installation setup" --msgbox  "Make sure you restart the engine before running the application." 10 60
	  exit
	fi
    #echo "$INST_USER_PWD" | su - "$INSTALL_USER" -c "sudo reboot"
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
# 7. adapt the birds_home.json
# 8. create the samba folder and samba user for remote access
########################################################################################

while true; do

    if   whiptail --title "Installation Dialog" --yesno "The following dialog guides you through the installation of your bird home. \
   The following steps will be performed: \n\n \
   1. provide the installation user used for running the installation\n (user with sudo privileges required) \n \
   2. Installation of all packages needed to run birds home\n \
   3. Setup of the application user to run the application\n \
   4. Setup of the python environment based on the requirement.txt in\n	a virtual environment \n \
   5. creation of the folder structure \n \
   6. creation of the samba folder for file access including a samba user " 20 78; then
    while true; do
        installation_dialog
		if $START_INSTALL; then
			break
		fi
      done
        echo "Start Installation"
        system_setup
        application_setup
        setup_raspberry
        cleanup
        echo "$install_steps"
    else
      exit
    fi
done