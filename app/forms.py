from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import Optional, NumberRange
from wtforms.fields.simple import PasswordField, SubmitField, StringField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from wtforms.widgets import ListWidget, CheckboxInput
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
        choices=[],
        coerce=int,
        validators=[DataRequired()]
    )
    soTien = IntegerField('Số tiền thanh toán', validators=[Optional(), NumberRange(min=0)])
    huanLuyenVien = SelectField('Huấn Luyện Viên',coerce=int, validators=[Optional()] )
    submit = SubmitField('Đăng ký hội viên')

class GiaHanForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    goiTap_id = SelectField('Chọn Gói Tập', validators=[DataRequired()], coerce=int)
    phuong_thuc = SelectField(
        'Phương thức thanh toán',
        choices=[('Tiền mặt', 'Tiền mặt'), ('Chuyển khoản', 'Chuyển khoản')],
        default='Tiền mặt',
        validators=[DataRequired()]
    )
    soTien = IntegerField('Số tiền thanh toán', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Xác Nhận Thanh Toán')

class ThanhToanNoForm(FlaskForm):
    dangKyGoiTap_id = HiddenField('Mã Đăng Ký', validators=[DataRequired()])
    soTienTra = IntegerField('Số tiền trả thêm', validators=[DataRequired(), NumberRange(min=1000)])
    submit = SubmitField('Thu Tiền')

class StaffRegisterForm(RegisterForm):
    role = SelectField('Vai trò', choices=[
        ('NGUOIQUANTRI', 'NGUOIQUANTRI'),
        ('THUNGAN', 'THUNGAN'),
        ('LETAN', 'LETAN'),
        ('HUANLUYENVIEN', 'Huấn Luyện Viên')
    ], validators=[DataRequired()])
    submit = SubmitField('Đăng ký nhân viên')

class TaoLichTapForm(FlaskForm):
    baiTap = StringField('Tên bài tập', validators=[DataRequired(), Length(max=255)])
    nhomCo = StringField('Thuộc nhóm cơ', validators=[DataRequired()])
    soHiep = IntegerField('Số hiệp', validators=[DataRequired(), NumberRange(min=1)])
    soLan = IntegerField('Số lần/hiệp', validators=[DataRequired(), NumberRange(min=1)])
    ngayTap = StringField('Chọn ngày tập cụ thể', validators=[DataRequired()])
    submit = SubmitField('Tạo lịch tập')

class ChonHLVForm(FlaskForm):
    hlv_id = HiddenField('Mã HLV', validators=[DataRequired()])
    submit = SubmitField('Chọn HLV này')

class SuaLichTapForm(FlaskForm):
    baiTap = StringField('Tên bài tập', validators=[DataRequired(), Length(max=255)])
    nhomCo = StringField('Thuộc nhóm cơ', validators=[DataRequired()])
    soHiep = IntegerField('Số hiệp', validators=[DataRequired(), NumberRange(min=1)])
    soLan = IntegerField('Số lần/hiệp', validators=[DataRequired(), NumberRange(min=1)])
    # Cho phép sửa ngày tập dạng văn bản (VD: HLV muốn sửa ngày 15 thành 16 thủ công)
    ngayTap = StringField('Chuỗi ngày tập', validators=[DataRequired()])
    submit = SubmitField('Lưu Thay Đổi')