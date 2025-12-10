from app.models import User, HuanLuyenVien, GoiTap, DangKyGoiTap, ThanhToan
from app import app
from uuid import uuid4
from datetime import date, datetime, timedelta
from app import db
from app.models import NhanVien, UserRole

DEFAULT_AVATAR = "default"

import hashlib


# ----------------------------------------------------------------------
#  AUTH — sử dụng check_password() để hỗ trợ cả MD5 và mật khẩu mới
# ----------------------------------------------------------------------
def auth_nhan_vien(taikhoan, matkhau):
    # Kiểm tra nhân viên trước


    user = User.query.filter_by(taiKhoan=taikhoan).first()
    if user and user.check_password(matkhau):
        # if user.NhanVienProfile:
        #     return user.NhanVienProfile

        return user
    return None



# ----------------------------------------------------------------------
#  Functions tìm user
# ----------------------------------------------------------------------
def get_user_by_id(id):
    return User.query.get(id)

def _find_any(cls, **kwargs):
    return cls.query.filter_by(**kwargs).first()

def get_user_by_username(username):
    if not username:
        return None
    return _find_any(User, taiKhoan=username)

def get_user_by_email(email):
    if not email:
        return None
    return _find_any(User, eMail=email)

def get_user_by_phone(phone):
    if not phone:
        return None
    return _find_any(User, SDT=phone)


# ----------------------------------------------------------------------
#  CREATE USER — lưu mật khẩu bằng set_password() (PBKDF2)
# ----------------------------------------------------------------------
def create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau, goiTap=None, avatar=None):

    # kiểm tra trùng
    if get_user_by_username(taiKhoan) or (email and get_user_by_email(email)) or (sdt and get_user_by_phone(sdt)):
        return None

    # fallback cho dữ liệu thiếu
    sdt = sdt.strip() if sdt and sdt.strip() else f"no-phone-{uuid4().hex}"
    email = email.strip() if email and email.strip() else f"no-email-{uuid4().hex}@no-reply.local"
    ngaySinh = ngaySinh or date.today()
    gioitinh_bool = str(gioiTinh) in ('1', 'True', 'true')

    # avatar default = "default"
    avatar = (avatar.strip() if avatar and isinstance(avatar, str) and avatar.strip() else DEFAULT_AVATAR)

    # tạo đối tượng user
    user = User(
        hoTen=(hoTen or '').strip(),
        gioiTinh=gioitinh_bool,
        ngaySinh=ngaySinh,
        diaChi=(diaChi or '').strip(),
        SDT=sdt,
        eMail=email,
        taiKhoan=taiKhoan.strip(),
        avatar=avatar
    )

    # HASH mật khẩu an toàn — KHÔNG dùng MD5
    user.set_password(matKhau)

    try:
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as ex:
        db.session.rollback()
        app.logger.exception("create_user error: %s", ex)
        return None


# ----------------------------------------------------------------------
#  Promote User -> Nhân Viên
# ----------------------------------------------------------------------
def promote_to_nhanvien(user, role_str):
    if not user or not getattr(user, 'id', None):
        return None
    try:
        role_enum = getattr(UserRole, role_str)
    except Exception:
        return None

    existing = NhanVien.query.get(user_id=user.id).first()
    if existing:
        existing.vaiTro = role_enum
        db.session.commit()
        return existing

    nv = NhanVien(user_id=user.id, vaiTro=role_enum)

    try:
        db.session.add(nv)
        db.session.commit()
        return nv
    except Exception:
        db.session.rollback()
        return None


# ----------------------------------------------------------------------
#  Tạo Huấn luyện viên
# ----------------------------------------------------------------------
def create_huanluyenvien_from_user(user):
    if not user or not getattr(user, 'id', None):
        return False

    existing = HuanLuyenVien.query.get(user.id)
    if existing:
        return True

    try:
        hlv = HuanLuyenVien(
            id=user.id,
            hoTen=(user.hoTen or '').strip(),
            SDT=(user.SDT or '').strip(),
            eMail=(user.eMail or '').strip()
        )

        db.session.add(hlv)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        app.logger.exception("create_huanluyenvien_from_user error")
        return False
# ----------------------------------------------------------------------
#  Xử lý gói tập - Phân trang
# ----------------------------------------------------------------------
def count_goi_tap():
    return GoiTap.query.count()

def load_goi_tap(page=1):

    page_size = app.config['PAGE_SIZE']

    start = (page - 1) * page_size

    return GoiTap.query.slice(start, start + page_size).all()

def add_receipt(user_id, goiTap_id, nhanVien_id = None):
    try:
        goiTap = GoiTap.query.get(goiTap_id)
        if not goiTap:
            return False, "Gói tập không tồn tại!!!"
        ngayDangKy = datetime.now().date()
        ngayKetThuc = ngayDangKy + timedelta(days=goiTap.thoiHan)

        dk = DangKyGoiTap(
            ngayDangKy=ngayDangKy,
            ngayKetThuc=ngayKetThuc,
            trangThai = True,
            hoiVien_id = user_id,
            goiTap_id = goiTap_id
        )
        db.session.add(dk)
        db.session.flush()

        method = "Tiền mặt" if nhanVien_id else "Chuyển khoản"

        hoa_don = ThanhToan(
            soTienTT = goiTap.giaTienGoi,
            ngayThanhToan = datetime.now(),
            phuongThuc = method,
            hoiVien_id = user_id,
            dangKyGoiTap_id = dk.id,
            nhanVien_id = nhanVien_id
        )
        db.session.add(hoa_don)

        db.session.commit()
        return True, "Đăng ký thành công"
    except Exception as ex:
        db.session.rollback()
        app.logger.exception("add_Receipt error: %s", ex)
        return False