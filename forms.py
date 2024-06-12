from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from flask_wtf.file import FileAllowed, FileRequired

class ProfilePictureForm(FlaskForm):
    profile_picture = FileField('Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Upload')
