import hashlib

from flask_admin import Admin
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, validators, ValidationError

from app import app, db
from flask_admin.contrib.sqla import ModelView
from app.models import NhanVien

admin = Admin(app=app, name='Người Quản Trị', template_mode='bootstrap4')

class NhanVienView(ModelView):
    column_labels = {
        'hoTen': 'Họ tên',
        'gioiTinh': 'Giới tính',
        'ngaySinh': 'Ngày sinh',
        'diaChi': 'Địa chỉ',
        'SDT': 'Số điện thoại',
        'eMail': 'Email',
        'taiKhoan': 'Tài khoản',
        'matKhau': 'Mật khẩu',
        'vaiTro': 'Vai trò'
    }
    column_searchable_list = ['hoTen']
    column_filters = ['vaiTro','gioiTinh']

    def on_model_change(self, form, model, is_created):
        if form.matKhau.data:
            model.matKhau = hashlib.md5(form.matKhau.data.encode('utf-8')).hexdigest()
        super(NhanVienView, self).on_model_change(form, model, is_created)


admin.add_view(NhanVienView(NhanVien, db.session))


