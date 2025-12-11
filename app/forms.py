from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.validators import Optional
from wtforms.fields.simple import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from flask_wtf.file import FileField, FileAllowed

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mật khẩu hiện tại', validators=[DataRequired(), Length(min=6)])
    new_password = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('Xác nhận mật khẩu mới', validators=[DataRequired(), EqualTo('new_password', message='Mật khẩu không khớp')])
    submit = SubmitField('Đổi mật khẩu')

class ChangeInfoForm(FlaskForm):
    hoTen = StringField('Họ và tên', validators=[DataRequired(), Length(max=50)])
    gioiTinh = SelectField('Giới tính', choices=[('1', 'Nam'), ('0', 'Nữ')], validators=[Optional()])
    ngaySinh = DateField('Ngày sinh', format='%Y-%m-%d', validators=[Optional()])
    SDT = StringField('Số điện thoại', validators=[DataRequired(), Length(max=20)])
    diaChi = StringField('Địa chỉ', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Cập nhật thông tin')

class RegisterForm(FlaskForm):
    hoTen = StringField('Họ và tên', validators=[DataRequired(), Length(min=2, max=200)])
    gioiTinh = SelectField('Giới tính', choices=[('1','Nam'),('0','Nữ')], validators=[Optional()])
    ngaySinh = DateField('Ngày sinh', format='%Y-%m-%d', validators=[Optional()])
    diaChi = StringField('Địa chỉ', validators=[Optional(), Length(max=255)])
    SDT = StringField('Số điện thoại', validators=[Optional(), Length(max=20)])
    eMail = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    taiKhoan = StringField('Tài khoản', validators=[DataRequired(), Length(min=3, max=50)])
    matKhau = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6)])
    matKhau2 = PasswordField('Xác nhận mật khẩu', validators=[DataRequired(), EqualTo('matKhau', message='Mật khẩu không khớp')])
    avatar = FileField("Ảnh đại diện",validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], "Chỉ cho phép ảnh!")])
    submit = SubmitField('Đăng ký')

class RegisterFormStaff(FlaskForm):
    hoTen = StringField('Họ và tên', validators=[DataRequired(), Length(min=2, max=200)])
    gioiTinh = SelectField('Giới tính', choices=[('1','Nam'),('0','Nữ')], validators=[Optional()])
    ngaySinh = DateField('Ngày sinh', format='%Y-%m-%d', validators=[Optional()])
    diaChi = StringField('Địa chỉ', validators=[Optional(), Length(max=255)])
    SDT = StringField('Số điện thoại', validators=[Optional(), Length(max=20)])
    eMail = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    taiKhoan = StringField('Tài khoản', validators=[DataRequired(), Length(min=3, max=50)])
    phuongThuc = SelectField('Phương thức thanh toán',
                             choices=[('Tiền mặt','Tiền mặt'), ('Chuyển khoản', 'Chuyển khoản')],
                             default='Tiền mặt')
    goiTap = SelectField(
        'Gói tập',
        choices=[('1','1 tháng'),('2','3 tháng'),('3','6 tháng'),('4','1 năm')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Đăng ký hội viên')


class StaffRegisterForm(RegisterForm):
    # kế thừa các trường trên, thêm chọn role
    role = SelectField('Vai trò', choices=[
        ('NGUOIQUANTRI', 'NGUOIQUANTRI'),
        ('THUNGAN', 'THUNGAN'),
        ('LETAN', 'LETAN')
    ], validators=[DataRequired()])
    submit = SubmitField('Đăng ký nhân viên')