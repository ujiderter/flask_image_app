from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileRequired, FileAllowed
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from PIL import Image
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lc0F7ojAAAAAAFH7xmExcTim17I_fkxbg-OU5Qj'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lc0F7ojAAAAAFtMRYaCaXYSmk4sDDrZKU2Zl2Kp'
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}

Bootstrap(app)

class ImageForm(FlaskForm):
    upload = FileField('Загрузите изображение', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')
    ])
    # поле формы с capture
    recaptcha = RecaptchaField()
    submit = SubmitField('Отправить')

def split_and_shift_image(image_path):
    img = Image.open(image_path)
    width, height = img.size

    half_width = width // 2
    half_height = height // 2

    parts = [
        img.crop((0, 0, half_width, half_height)),  # Верхний левый
        img.crop((half_width, 0, width, half_height)),  # Верхний правый
        img.crop((half_width, half_height, width, height)),  # Нижний правый
        img.crop((0, half_height, half_width, height))  # Нижний левый
    ]

    shifted_parts = [parts[3], parts[0], parts[1], parts[2]]

    new_img = Image.new('RGB', (width, height))
    new_img.paste(shifted_parts[0], (0, 0))
    new_img.paste(shifted_parts[1], (half_width, 0))
    new_img.paste(shifted_parts[2], (half_width, half_height))
    new_img.paste(shifted_parts[3], (0, half_height))

    return new_img

def plot_color_distribution(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')

    r, g, b = img.split()
    r_data = list(r.getdata())
    g_data = list(g.getdata())
    b_data = list(b.getdata())

    plt.figure()
    plt.hist(r_data, bins=256, color='red', alpha=0.5, label='Red')
    plt.hist(g_data, bins=256, color='green', alpha=0.5, label='Green')
    plt.hist(b_data, bins=256, color='blue', alpha=0.5, label='Blue')
    plt.legend()
    plt.title('Color Distribution')
    plt.xlabel('Color Value')
    plt.ylabel('Frequency')

    plot_path = os.path.join(app.config['UPLOAD_FOLDER'], 'color_distribution.png')
    plt.savefig(plot_path)
    plt.close()

    return plot_path

@app.route('/', methods=['GET', 'POST'])
def index():
    form = ImageForm()
    if form.validate_on_submit():
        file = form.upload.data
        filename = secure_filename(file.filename)
        original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(original_image_path)

        shifted_image = split_and_shift_image(original_image_path)
        shifted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'shifted_' + filename)
        shifted_image.save(shifted_image_path)

        plot_path = plot_color_distribution(original_image_path)

        return render_template('index.html', form=form, original_image=original_image_path, shifted_image=shifted_image_path, plot_image=plot_path)

    return render_template('index.html', form=form)