from app.models import User, HuanLuyenVien
from app import app
import  hashlib
from uuid import uuid4
from datetime import date
from app import db
from app.models import NhanVien, UserRole

def _md5(s: str) -> str:
    return hashlib.md5(s.strip().encode('utf-8')).hexdigest()

def auth_nhan_vien(taikhoan, matkhau):
    matkhau = str(hashlib.md5(matkhau.strip().encode('utf-8')).hexdigest())

    u = NhanVien.query.filter(NhanVien.taiKhoan.__eq__(taikhoan),
                          NhanVien.matKhau.__eq__(matkhau)).first()
    if u:
        return u  # nếu là nhân viên → trả về ngay

    # nếu không phải nhân viên → kiểm tra hội viên trong bảng Users
    hv = User.query.filter(User.taiKhoan.__eq__(taikhoan),
                        User.matKhau.__eq__(matkhau)).first()
    return hv


def get_user_by_id(id):
    return User.query.get(id)


def _find_any(cls, **kwargs):
    return cls.query.filter_by(**kwargs).first()

def get_user_by_username(username):
    if not username:
        return None
    return _find_any(User, taiKhoan=username) or _find_any(NhanVien, taiKhoan=username)

def get_user_by_email(email):
    if not email:
        return None
    return _find_any(User, eMail=email) or _find_any(NhanVien, eMail=email)

def get_user_by_phone(phone):
    if not phone:
        return None
    return _find_any(User, SDT=phone) or _find_any(NhanVien, SDT=phone)

def create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau):
    """Tạo User mới, hash MD5, tránh unique-collision cho email/phone rỗng."""
    if get_user_by_username(taiKhoan) or (email and get_user_by_email(email)) or (sdt and get_user_by_phone(sdt)):
        return None

    sdt = sdt.strip() if sdt and sdt.strip() else f"no-phone-{uuid4().hex}"
    email = email.strip() if email and email.strip() else f"no-email-{uuid4().hex}@no-reply.local"
    ngaySinh = ngaySinh or date.today()
    gioitinh_bool = str(gioiTinh) in ('1','True','true')

    user = User(
        hoTen=(hoTen or '').strip(),
        gioiTinh=gioitinh_bool,
        ngaySinh=ngaySinh,
        diaChi=(diaChi or '').strip(),
        SDT=sdt,
        eMail=email,
        taiKhoan=taiKhoan.strip(),
        matKhau=_md5(matKhau)
    )

    try:
        db.session.add(user)
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        return None

def promote_to_nhanvien(user, role_str):
    """
    Tạo 1 record trong nhanvien với id = user.id và vaiTro tương ứng.
    role_str: 'NGUOIQUANTRI' | 'THUNGAN' | 'LETAN'
    """
    if not user or not getattr(user, 'id', None):
        return None
    try:
        role_enum = getattr(UserRole, role_str)
    except Exception:
        return None

    # nếu đã có nhanvien tương ứng thì cập nhật vaiTro
    existing = NhanVien.query.get(user.id)
    if existing:
        existing.vaiTro = role_enum
        db.session.commit()
        return existing

    # Tạo mới nhanvien (joined table: nhanvien.id = users.id)
    nv = NhanVien(id=user.id, vaiTro=role_enum)
    try:
        db.session.add(nv)
        db.session.commit()
        return nv
    except Exception:
        db.session.rollback()
        return None

def create_huanluyenvien_from_user(user):
    if not user or not getattr(user, 'id', None):
        return False

    # kiểm tra theo PK
    existing = HuanLuyenVien.query.get(user.id)
    if existing:
        return True

    try:
        hlv = HuanLuyenVien(
            id = user.id,                # đặt id trùng user.id
            hoTen = (user.hoTen or '').strip(),
            SDT   = (user.SDT or '').strip(),
            eMail = (user.eMail or '').strip()
        )
        db.session.add(hlv)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        app.logger.exception("create_huanluyenvien_from_user error")
        return False