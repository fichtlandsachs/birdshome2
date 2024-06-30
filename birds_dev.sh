#source env/bin/activate
/bin/bash -c  "~/birdshome/bin/activate; exec /bin/bash -i"
gunicorn3 --bind 0.0.0.0:5000 --threads 5 -w 1 --timeout 120 app:app
deactivate
