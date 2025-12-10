import hashlib

from flask_admin import Admin

from app import app, db
from flask_admin.contrib.sqla import ModelView
from app.models import NhanVien, User

admin = Admin(app=app, name='Người Quản Trị', template_mode='bootstrap4')

class NhanVienView(ModelView):
    column_list = ['user.hoTen', 'user.gioiTinh','user.ngaySinh','user.diaChi','user.SDT','user.eMail','user.taiKhoan', 'vaiTro']

    column_labels = {
        'user.hoTen': 'Họ tên',
        'user.gioiTinh': 'Giới tính',
        'user.ngaySinh': 'Ngày sinh',
        'user.diaChi': 'Địa chỉ',
        'user.SDT': 'Số điện thoại',
        'user.eMail': 'Email',
        'user.taiKhoan': 'Tài khoản',
        'vaiTro': 'Vai trò'
    }
    ccolumn_searchable_list = ['user.hoTen', 'user.taiKhoan']
    column_filters = ['vaiTro', 'user.gioiTinh']

    can_create = False

    def on_model_change(self, form, model, is_created):
        if form.matKhau.data:
            model.matKhau = hashlib.md5(form.matKhau.data.encode('utf-8')).hexdigest()
        super(NhanVienView, self).on_model_change(form, model, is_created)


admin.add_view(NhanVienView(NhanVien, db.session))


