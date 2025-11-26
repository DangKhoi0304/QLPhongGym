from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.validators import Optional
from wtforms.fields.simple import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, EqualTo, Email


class ChangePasswordForm(FlaskForm):
    mat_khau_cu = PasswordField('Mật khẩu cũ', validators=[DataRequired()])
    mat_khau_moi = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=8)])
    xac_nhan_mat_khau = PasswordField('Xác nhận mật khẩu mới', validators=[DataRequired(), EqualTo('mat_khau_moi')])
    submit = SubmitField('Đổi Mật Khẩu')

class ChangeInfoForm(FlaskForm):
    ho_va_ten = StringField('Họ và tên', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    so_dien_thoai = StringField('Số điện thoại', validators=[DataRequired()])
    tai_khoan = StringField('Tài khoản', validators=[DataRequired()])
    cccd = StringField('CCCD', validators=[DataRequired()])
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
    submit = SubmitField('Đăng ký')

class StaffRegisterForm(RegisterForm):
    # kế thừa các trường trên, thêm chọn role
    role = SelectField('Vai trò', choices=[
        ('NGUOIQUANTRI', 'NGUOIQUANTRI'),
        ('THUNGAN', 'THUNGAN'),
        ('LETAN', 'LETAN')
    ], validators=[DataRequired()])
    submit = SubmitField('Đăng ký nhân viên')