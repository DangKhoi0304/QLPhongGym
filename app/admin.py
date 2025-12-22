from flask import redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user
from wtforms import SelectField
from app import app, db
from app.models import User, GoiTap, UserRole, DanhMucBaiTap, QuyDinh, NhanVien

DEFAULT_AVATAR = "default"


# --- 1. CẤU HÌNH BẢO MẬT TRANG CHỦ DASHBOARD (/admin) ---
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # Kiểm tra quyền: Phải đăng nhập VÀ là NGUOIQUANTRI
        if not (current_user.is_authenticated and \
                getattr(current_user, 'NhanVienProfile', None) and \
                current_user.NhanVienProfile.vaiTro == UserRole.NGUOIQUANTRI):
            # Nếu không đủ quyền -> Chuyển hướng về trang đăng nhập
            return redirect('/login')

        # Nếu đúng là Admin -> Cho phép vào trang Dashboard
        return super(MyAdminIndexView, self).index()


# --- 2. CẤU HÌNH BẢO MẬT CÁC MODEL VIEW CON ---
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and \
            getattr(current_user, 'NhanVienProfile', None) and \
            current_user.NhanVienProfile.vaiTro == UserRole.NGUOIQUANTRI

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/login')


class UserView(AuthenticatedModelView):
    # --- CẤU HÌNH DANH SÁCH (LIST VIEW) ---
    column_list = ['hoTen', 'taiKhoan', 'vai_tro_hien_thi', 'SDT', 'gioiTinh', 'NgayDangKy', 'avatar']

    column_labels = {
        'hoTen': 'Họ Tên',
        'taiKhoan': 'Tài Khoản',
        'matKhau': 'Mật Khẩu',
        'vai_tro_hien_thi': 'Vai Trò',
        'SDT': 'Số ĐT',
        'eMail': 'Email',
        'gioiTinh': 'Giới Tính',
        'NgayDangKy': 'Ngày ĐK',
        'avatar': 'Avatar'
    }

    column_searchable_list = ['hoTen', 'SDT', 'taiKhoan']
    column_filters = ['gioiTinh']

    # --- CẤU HÌNH FORM (EDIT/CREATE) ---
    can_create = True
    can_edit = True
    can_delete = True

    # Loại bỏ avatar để không hiện ô nhập
    form_columns = ['hoTen', 'taiKhoan', 'matKhau', 'chon_quyen', 'SDT', 'eMail', 'gioiTinh', 'ngaySinh', 'diaChi']

    form_excluded_columns = ['NhanVienProfile', 'DangKyGoiTap', 'ThanhToan']

    form_extra_fields = {
        'chon_quyen': SelectField('Phân Quyền', choices=[
            ('HOIVIEN', 'Hội Viên (Khách)'),
            ('NGUOIQUANTRI', 'Quản Trị Viên'),
            ('THUNGAN', 'Thu Ngân'),
            ('LETAN', 'Lễ Tân'),
            ('HUANLUYENVIEN', 'Huấn Luyện Viên')
        ], default='HOIVIEN')
    }

    # --- LOGIC HIỂN THỊ QUYỀN ---
    def _role_formatter(view, context, model, name):
        if model.NhanVienProfile:
            role = model.NhanVienProfile.vaiTro
            return role.name if role else "Nhân Viên"
        return "Hội Viên"

    column_formatters = {
        'vai_tro_hien_thi': _role_formatter
    }

    # --- LOGIC PRE-FILL ---
    def on_form_prefill(self, form, id):
        user = User.query.get(id)
        if user.NhanVienProfile:
            role_enum = user.NhanVienProfile.vaiTro
            form.chon_quyen.data = role_enum.name
        else:
            form.chon_quyen.data = 'HOIVIEN'

    # --- LOGIC LƯU DỮ LIỆU ---
    def on_model_change(self, form, model, is_created):
        # Nếu là tạo mới, set cứng avatar là "default"
        if is_created:
            model.avatar = DEFAULT_AVATAR

        # Xử lý Mật khẩu
        raw_password = form.matKhau.data
        if raw_password:
            model.set_password(raw_password)

        # Xử lý Phân Quyền
        selected_role = form.chon_quyen.data

        if selected_role == 'HOIVIEN':
            # Nếu chọn Hội viên -> Xóa record NhanVien nếu đang tồn tại
            if model.NhanVienProfile:
                db.session.delete(model.NhanVienProfile)
        else:
            # Nếu chọn vai trò Nhân viên (Admin, Thu Ngân, HLV...)
            role_enum = getattr(UserRole, selected_role)

            if model.NhanVienProfile:
                # Nếu đã là nhân viên -> Cập nhật vai trò mới
                model.NhanVienProfile.vaiTro = role_enum
            else:
                # Nếu chưa là nhân viên -> Tạo record NhanVien mới
                # Dùng relationship assignment để SQLAlchemy tự gán user_id sau khi flush
                new_nv = NhanVien(vaiTro=role_enum)
                model.NhanVienProfile = new_nv
                db.session.add(new_nv)


# --- CÁC VIEW QUẢN LÝ KHÁC ---
class GoiTapView(AuthenticatedModelView):
    column_list = ['tenGoiTap', 'thoiHan', 'giaTienGoi']
    column_labels = {
        'tenGoiTap': 'Tên Gói',
        'thoiHan': 'Thời Hạn (Ngày)',
        'giaTienGoi': 'Giá Tiền (VNĐ)',
    }
    form_columns = ['tenGoiTap', 'thoiHan', 'giaTienGoi']
    can_create = True
    can_edit = True
    can_delete = True


class DanhMucBaiTapView(AuthenticatedModelView):
    column_list = ['ten_bai_tap', 'nhom_co']
    column_labels = {'ten_bai_tap': 'Tên Bài', 'nhom_co': 'Nhóm Cơ'}
    form_columns = ['ten_bai_tap', 'nhom_co']
    column_searchable_list = ['ten_bai_tap', 'nhom_co']
    can_create = True
    can_edit = True
    can_delete = True


class QuyDinhView(AuthenticatedModelView):
    column_list = ['ten_quy_dinh', 'gia_tri']
    column_labels = {'ten_quy_dinh': 'Quy Định', 'gia_tri': 'Giá Trị (Ngày)'}
    form_columns = ['gia_tri']
    can_create = False
    can_delete = False
    can_edit = True


# --- 3. KHỞI TẠO ADMIN VÀ THÊM VIEW ---

# [QUAN TRỌNG] Thêm index_view=MyAdminIndexView() để bảo vệ trang chủ Admin
admin = Admin(app=app,
              name='QUẢN TRỊ GYM',
              template_mode='bootstrap4',
              index_view=MyAdminIndexView())

# Thêm Link điều hướng trên Header
admin.add_link(MenuLink(name='Đăng Xuất', url='/logout'))  # Nút đăng xuất

# Thêm các trang quản lý vào Menu
admin.add_view(UserView(User, db.session, name='Quản Lý Người Dùng'))
admin.add_view(GoiTapView(GoiTap, db.session, name='Quản Lý Gói Tập'))
admin.add_view(DanhMucBaiTapView(DanhMucBaiTap, db.session, name='Danh Mục Bài Tập'))
admin.add_view(QuyDinhView(QuyDinh, db.session, name='Quy Định Hệ Thống'))