import flask_wtf
from wtforms import (
    StringField,
    BooleanField,
    SubmitField,
    SelectField,
    RadioField

)
from wtforms.fields import (
    TimeField,
    IntegerField,
    DecimalRangeField,
    PasswordField
)
from wtforms.validators import (
    DataRequired,
    URL
)


class AdminForm(flask_wtf.FlaskForm):
    style = {'class': 'adminFormOutputField', 'disabled': 'disabled"', 'style': 'border:0'}
    """Admin Bereich für Nistkasten"""
    duration_vid = DecimalRangeField(
        'Dauer der Videoaufnahme in s', [
            DataRequired()
        ],
        default=15
    )
    duration_vidVal = IntegerField(
        '', render_kw=style
    )
    motion_handling_enabled = BooleanField(label='automatische Erkennung',default=True)
    vid_res_x = IntegerField(
        'Video X', render_kw=style

    )
    vid_res_y = IntegerField(
        'Video Y', render_kw=style
    )
    sensitivity = DecimalRangeField(
        'Empflindlichkeit', default=3000

    )
    sensitivityVal = IntegerField(
        '', render_kw=style

    )

    vid_drehen_enabled = BooleanField(
        'Bild um 180 Grad drehen'
    )

    prefix_vid = StringField(
        'Videoprefix',
        [
            DataRequired(message="Please enter a prefix for the video naming.")
        ]
    )
    replay_enabled = BooleanField(
        'automatische Aufnahmen'
    )
    replay_interval = IntegerField(
        'Intervall Einzelbilder in Minuten'
    )
    replay_days = IntegerField(
        'Zeitraum für Zeitraffer'
    )
    frames_per_sec_replay = IntegerField(
        'Bilder je sec Zeitraffer'
    )
    upload_enabled = BooleanField(
        'Serverupload'
    )
    delete_enabled = BooleanField(
        'Datei nach Upload löschen'
    )
    radio_ftp = RadioField(
        'Protokoll', choices=[('ftp_upload', 'FTP'), ('folder_upload', 'eingebundenes Verzeichnis'), ('remoteFolder_upload', 'Netzlaufwerk')]
    )
    num_retry_upload = IntegerField(
        'Anzahl Versuche Upload'
    )
    pause_retry_upload = IntegerField(
        'Anzahl Versuche Upload bei Nichterreichbarkeit in Minuten'
    )
    server_upload = StringField(
        'Server für Upload'
    )
    folder_upload = StringField(
        'Verzeichnis für Upload'
    )
    time_upload = TimeField(
        'Zeitpunkt für Upload'
    )
    user_upload = StringField(
        'Nutzer für Upload'
    )
    password_upload = PasswordField(
        'Passwort für Upload'
    )
    prefix_pic = StringField(
        'Prefix für Bilder'
    )
    days_replay = IntegerField(
        'Zeitraum für Zeitraffer in Tagen'
    )
    vid_sorter_enabled = BooleanField(
        'Videosortierer'
    )
    time_vid_sorter = TimeField(
        'Zeitpunkt für Videosortierung'
    )
    pic_ending = SelectField(
        'Endung der Bilder',
        [DataRequired()],
        choices=[
            ('jpg', '.jpg')
        ]
    )

    website = StringField(
        'Website',
        validators=[URL()]
    )
    submit = SubmitField('Speichern')
    del_nodetect = SubmitField('Verzeichnis Nodetect leeren')
