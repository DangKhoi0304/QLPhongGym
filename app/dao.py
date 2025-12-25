
from app.models import User, GoiTap, DangKyGoiTap, ThanhToan, LichTap
from app import app
from uuid import uuid4
from datetime import date, datetime, timedelta
from app import db
from app.models import NhanVien, UserRole
from sqlalchemy import func

DEFAULT_AVATAR = "default"

def auth_nhan_vien(taikhoan, matkhau):

    user = User.query.filter_by(taiKhoan=taikhoan).first()
    if user and user.check_password(matkhau):
            return user
    return None


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

def count_goi_tap():
    return GoiTap.query.count()

def get_all_packages():
    return GoiTap.query.all()

def load_goi_tap(page=1):

    page_size = app.config['PAGE_SIZE']

    start = (page - 1) * page_size

    return GoiTap.query.slice(start, start + page_size).all()

def get_active_package_by_user_id(user_id):
    active_package = DangKyGoiTap.query.filter(
        DangKyGoiTap.hoiVien_id == user_id,
        DangKyGoiTap.trangThai == True,
        DangKyGoiTap.ngayKetThuc >= datetime.now().date(),
    ).order_by(DangKyGoiTap.ngayKetThuc).first()

    return active_package

def add_receipt(user_id, goiTap_id, nhanVien_id = None,hlv_id=None, payment_method="Tiền mặt", tien_dong =None):

    try:
        is_nhan_vien = NhanVien.query.filter_by(user_id=user_id).first()
        if is_nhan_vien:
            return False, "Tài khoản thộc Nhân Viên/HLV không được phép đăng ký gói tập!"
        DangKyGoiTap.query.filter(
            DangKyGoiTap.hoiVien_id == user_id,
            DangKyGoiTap.trangThai == True,  # Đang là 1
            DangKyGoiTap.ngayKetThuc < datetime.now().date()
        ).update({DangKyGoiTap.trangThai: False}, synchronize_session=False)

        active_package = get_active_package_by_user_id(user_id)
        if active_package:
            so_ngay = (active_package.ngayKetThuc - datetime.now().date()).days
            msg = f"Gói tập hiện tại còn {so_ngay} ngày. Vui lòng sử dụng hết trước khi đăng ký mới!"
            return False, msg

        goiTap = GoiTap.query.get(goiTap_id)
        if not goiTap:
            return False, "Gói tập không tồn tại!!!"

        tong_tien = goiTap.giaTienGoi
        tien_thanh_toan = float(tien_dong) if tien_dong else tong_tien

        dk = DangKyGoiTap(
            ngayDangKy=datetime.now().date(),
            ngayKetThuc= datetime.now().date()+  timedelta(days=goiTap.thoiHan),
            trangThai = True,
            hoiVien_id = user_id,
            goiTap_id = goiTap_id,
            huanLuyenVien_id = hlv_id
        )
        db.session.add(dk)
        db.session.flush()

        hoa_don = ThanhToan(
            soTienTT = tien_thanh_toan,
            ngayThanhToan = datetime.now(),
            phuongThuc=payment_method,
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


def get_all_member(kw=None):
    member = (db.session.query(User).join(NhanVien, User.id == NhanVien.user_id, isouter=True)
              .filter(NhanVien.id==None))
    if kw:
        kw = kw.strip()
        member = member.filter(User.hoTen.contains(kw)|
                               User.SDT.contains(kw)|
                               User.taiKhoan.contains(kw)
        )
    return member.order_by(User.id).all()

def get_payment_history_by_id(user_id):
    return ThanhToan.query.filter_by(hoiVien_id=user_id).order_by(ThanhToan.ngayThanhToan.desc()).all()

def get_debt_info(dangKyGoiTap_id):
    dk = DangKyGoiTap.query.get(dangKyGoiTap_id)
    if not dk:
        return None
    gia_goi_tap = dk.goi_tap.giaTienGoi
    da_tra = db.session.query(func.sum(ThanhToan.soTienTT))\
                       .filter(ThanhToan.dangKyGoiTap_id == dangKyGoiTap_id).scalar() or 0
    con_no = gia_goi_tap - da_tra
    return {
        "id": dk.id,
        "ten_goi": dk.goi_tap.tenGoiTap,
        "gia_goi_tap": gia_goi_tap,
        "da_tra": da_tra,
        "con_no": con_no,
        "trang_thai": "Hoàn tất" if con_no <= 0 else "Còn nợ"
    }
def add_debt_payment(dangKyGoiTap_id, so_tien, nhanVien_id):
    try:
        dk = DangKyGoiTap.query.get(dangKyGoiTap_id)
        if not dk: return False

        hd = ThanhToan(
            soTienTT=so_tien,
            ngayThanhToan=datetime.now(),
            phuongThuc="Tiền mặt (Trả nợ)",
            hoiVien_id=dk.hoiVien_id,
            dangKyGoiTap_id=dk.id,
            nhanVien_id=nhanVien_id
        )
        db.session.add(hd)
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        print(str(ex))
        return False
def stats_revenue(year = datetime.now().year):
    revenue = ((db.session.query(func.extract('month', ThanhToan.ngayThanhToan).label('thang'),GoiTap.tenGoiTap,
                               func.sum(ThanhToan.soTienTT))
            .join(DangKyGoiTap,ThanhToan.dangKyGoiTap_id==DangKyGoiTap.id)
            .join(GoiTap, DangKyGoiTap.goiTap_id==GoiTap.id))
            .filter(func.extract('year', ThanhToan.ngayThanhToan) == year)
            .order_by(func.extract('month', ThanhToan.ngayThanhToan)))
    return revenue.group_by(func.extract('month', ThanhToan.ngayThanhToan),GoiTap.tenGoiTap).all()

def stats_member_growth(year=datetime.now().year):
    member_growth = (db.session.query(func.extract('month', User.NgayDangKy),func.count(User.id)
                  ).join(NhanVien, User.id == NhanVien.user_id, isouter=True)
                     .filter(func.extract('year', User.NgayDangKy) == year, NhanVien.id ==None) #Chỉ lấy những tài khoản không phải là Nhân Viên / HLV
                    )
    return member_growth.group_by(func.extract('month', User.NgayDangKy)).all()

def count_active_members():
    return DangKyGoiTap.query.filter(
        DangKyGoiTap.trangThai == True,
        DangKyGoiTap.ngayKetThuc >= datetime.now().date()
    ).count()


def load_all_huanluyenvien():
    return NhanVien.query.filter_by(vaiTro=UserRole.HUANLUYENVIEN).all()

def assign_pt_for_member(user_id, hlv_id):
    active_pack = get_active_package_by_user_id(user_id)
    try:
        if active_pack:
            active_pack.huanLuyenVien_id = hlv_id
            db.session.commit()
            return True

        return False
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"Lỗi assign PT: {ex}")
        return False

def get_members_by_hlv(hlv_id):
    return DangKyGoiTap.query.filter(
        DangKyGoiTap.huanLuyenVien_id == hlv_id,
        DangKyGoiTap.trangThai == True,
        DangKyGoiTap.ngayKetThuc >= datetime.now().date()
    ).all()

def add_schedule(dangKyId, baiTap, nhom_co, soHiep, soLan, ngayTap, danh_muc_id=None):
    try:
        lich = LichTap(
            dangKyGoiTap_id=dangKyId,
            baiTap=baiTap,
            nhom_co=nhom_co,
            soHiep=soHiep,
            soLan=soLan,
            ngayTap=ngayTap,
            danh_muc_id=danh_muc_id
        )
        db.session.add(lich)
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"Lỗi add schedule: {ex}")
        return False

def get_schedule_by_dangky(dangKyId):
    return LichTap.query.filter_by(dangKyGoiTap_id=dangKyId).all()

def get_schedule_item_by_id(id):
    return LichTap.query.get(id)

def update_schedule(id, baiTap,nhom_co, soHiep, soLan, ngayTap, danh_muc_id=None):
    try:
        lich = LichTap.query.get(id)
        if lich:
            lich.baiTap = baiTap
            lich.nhom_co = nhom_co
            lich.soHiep = soHiep
            lich.soLan = soLan
            lich.ngayTap = ngayTap
            if danh_muc_id:  # Chỉ cập nhật nếu có giá trị
                lich.danh_muc_id = danh_muc_id
            db.session.commit()
            return True
    except Exception as ex:
        db.session.rollback()
        print(f"Lỗi update: {ex}")
    return False

def delete_schedule(id):
    try:
        lich = LichTap.query.get(id)
        if lich:
            db.session.delete(lich)
            db.session.commit()
            return True
    except Exception as ex:
        db.session.rollback()
        print(f"Lỗi delete: {ex}")
    return False