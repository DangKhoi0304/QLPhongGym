from datetime import date, datetime, timedelta

from cloudinary.provisioning import users

from app import db, app
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, BOOLEAN, Date, Enum, UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum as RoleEnum, unique
from flask_login import UserMixin
import hashlib
import re
from sqlalchemy.orm import relationship, backref


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

class UserRole(RoleEnum):
    NGUOIQUANTRI = 1
    THUNGAN = 2
    LETAN = 3
    HUANLUYENVIEN = 4

class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    hoTen = Column(String(50), nullable=False)
    gioiTinh = Column(Boolean, nullable=False)
    ngaySinh = Column(Date, nullable=False)
    SDT = Column(String(20), unique=True, nullable=False)
    eMail = Column(String(255), unique=True, nullable=False)
    diaChi = Column(String(255), nullable=False)
    NgayDangKy = Column(Date, default=datetime.now)
    taiKhoan = Column(String(50), unique=True, nullable=False)
    matKhau = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=False)

    def __str__(self):
        return self.hoTen

    def get_id(self):
        return str(self.id)

    # thêm method get_username và property username để template dùng thoải mái
    def get_username(self):
        # trả tên hiển thị (bạn có thể đổi thành self.taiKhoan nếu muốn)
        return self.hoTen

    def update_profile(self, hoTen, gioiTinh, SDT, ngaySinh, diaChi):
        try:
            # 1. Cập nhật thông tin cơ bản
            if hoTen: self.hoTen = hoTen
            if SDT: self.SDT = SDT
            if diaChi: self.diaChi = diaChi

            # 2. Xử lý Giới tính (Form gửi về '1' hoặc '0')
            if gioiTinh is not None:
                self.gioiTinh = True if str(gioiTinh) == '1' else False

            # 3. Xử lý Ngày sinh (Chuyển chuỗi 'yyyy-mm-dd' sang object Date)
            if ngaySinh:
                if isinstance(ngaySinh, str):
                    self.ngaySinh = datetime.strptime(ngaySinh, '%Y-%m-%d').date()
                else:
                    self.ngaySinh = ngaySinh

            db.session.commit()
            return True, "Cập nhật thông tin thành công!"

        except Exception as e:
            db.session.rollback()
            print(f"Lỗi update: {e}")
            return False, "Lỗi!!!"

    @property
    def username(self):
        return self.get_username()

    def set_password(self, password: str):
        """Hash password an toàn và lưu vào self.matKhau"""
        # use werkzeug default pbkdf2:sha256
        self.matKhau = generate_password_hash(password)

    def check_password(self, password: str):
        """
        Kiểm tra password.
        Nếu DB đang chứa MD5 (32 hex) thì kiểm tra MD5; nếu khớp -> rehash bằng werkzeug và lưu.
        Trả về True/False.
        """
        if not self.matKhau:
            return False

        # nhận dạng MD5: chính xác 32 ký tự hex
        if isinstance(self.matKhau, str) and re.fullmatch(r'[0-9a-f]{32}', self.matKhau):
            # db đang lưu MD5 cũ
            md5_try = hashlib.md5(password.encode('utf-8')).hexdigest()
            if md5_try == self.matKhau:
                # chuyển sang hash an toàn hơn
                try:
                    self.set_password(password)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                return True
            return False

        # nếu không phải MD5 -> kiểm tra với werkzeug
        try:
            return check_password_hash(self.matKhau, password)
        except Exception:
            return False

class NhanVien(BaseModel):
    __tablename__ = 'nhanvien'

    vaiTro = Column(Enum(UserRole))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)

    user = relationship('User', backref=backref('NhanVienProfile', uselist=False))

    def get_VaiTro(self):
        return self.vaiTro

    @property
    def hoTen(self):
        return self.user.hoTen if self.user else ""

class GoiTap(BaseModel):
    __tablename__ = 'goitap'

    tenGoiTap = Column(String(255), nullable=False)
    thoiHan = Column(Integer, nullable=False)
    giaTienGoi = Column(Float, nullable=False)

    def __str__(self):
        return f"{self.tenGoiTap} ({self.thoiHan} ngày)"

class DangKyGoiTap(BaseModel):
    __tablename__ = 'dangkygoitap'

    ngayDangKy = Column(Date, default=datetime.now, nullable=False)
    ngayKetThuc = Column(Date, nullable=False)
    trangThai = Column(Boolean, default=True)  # True: Đang kích hoạt, False: Hết hạn/Hủy

    hoiVien_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    goiTap_id = Column(Integer, ForeignKey('goitap.id'), nullable=False)
    huanLuyenVien_id = Column(Integer, ForeignKey('nhanvien.id'), nullable=True)

    hoi_vien = relationship('User', backref='DangKyGoiTap', lazy=True)
    goi_tap = relationship('GoiTap', backref='DangKyGoiTap', lazy=True)
    huan_luyen_vien = relationship('NhanVien', backref='ds_hoi_vien_dang_ky', lazy=True)

    def tinh_ngay_het_han(self):
        if self.goi_tap and self.goi_tap.thoiHan:
            if not self.ngayDangKy:
                self.ngayDangKy = datetime.now().date()
        self.ngayKetThuc = self.ngayDangKy + timedelta(days=int(self.goi_tap.thoiHan))

class LichTap(BaseModel):
    __tablename__ = 'lichtap'

    baiTap = Column(String(255), nullable=False)  # Squat, Bench Press...
    nhom_co = Column(String(100), nullable=True)
    soHiep = Column(Integer, nullable=False)
    soLan = Column(Integer, nullable=False)  # Số lần/hiệp
    ngayTap = Column(String(100), nullable=False)  # "Thứ 2, 4, 6"

    dangKyGoiTap_id = Column(Integer, ForeignKey('dangkygoitap.id'), nullable=False)
    danh_muc_id = Column(Integer, ForeignKey('danhmucbaitap.id'), nullable=True)

    dang_ky = relationship('DangKyGoiTap', backref='ds_lich_tap', lazy=True)
    danh_muc = relationship('DanhMucBaiTap')

class ThanhToan(BaseModel):
    __tablename__ = 'thanhtoan'
    soTienTT = Column(Float, nullable=False)
    ngayThanhToan = Column(Date, default=datetime.now)
    phuongThuc = Column(String(50), default='Trực Tuyên')

    hoiVien_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    dangKyGoiTap_id = Column(Integer,ForeignKey('dangkygoitap.id'), nullable=False)
    nhanVien_id = Column(Integer, ForeignKey('nhanvien.id'), nullable=True)

    hoi_vien = relationship('User', backref='ThanhToan', lazy=True)
    dang_ky = relationship('DangKyGoiTap', backref='ThanhToan', lazy=True)
    nhan_vien = relationship('NhanVien', backref='ThanhToan', lazy=True)

class DanhMucBaiTap(BaseModel):
    __tablename__ = 'danhmucbaitap'

    ten_bai_tap = Column(String(100), nullable=False)  # VD: Squat, Hít đất
    nhom_co = Column(String(50))  # VD: Ngực, Chân, Tay...

    def __str__(self):
        return self.ten_bai_tap

class QuyDinh(BaseModel):
    __tablename__ = 'quydinh'

    ten_quy_dinh = Column(String(100), nullable=False, unique=True)
    gia_tri = Column(Integer, nullable=False)

    def __str__(self): return self.ten_quy_dinh

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # g1 = GoiTap(tenGoiTap="Gói 1 Tháng", thoiHan=30, giaTienGoi=500000)
        # g2 = GoiTap(tenGoiTap="Gói 3 Tháng", thoiHan=90, giaTienGoi=1200000)
        # g3 = GoiTap(tenGoiTap="Gói 6 Tháng", thoiHan=180, giaTienGoi=2000000)
        # g4 = GoiTap(tenGoiTap="Gói 1 Năm", thoiHan=365, giaTienGoi=3500000)
        #
        # # 3. Lưu vào database
        # db.session.add_all([g1, g2, g3, g4])
        # db.session.commit()
        #
        # b1 = DanhMucBaiTap(ten_bai_tap="Squat (Gánh tạ)", nhom_co="Chân")
        # b2 = DanhMucBaiTap(ten_bai_tap="Bench Press (Đẩy ngực)", nhom_co="Ngực")
        # b3 = DanhMucBaiTap(ten_bai_tap="Deadlift", nhom_co="Lưng/Đùi")
        #
        # db.session.add_all([b1, b2, b3])
        # db.session.commit()
        #
        # qd = QuyDinh(ten_quy_dinh="Số ngày tập tối đa", gia_tri=4)
        # db.session.add(qd)
        # db.session.commit()
        #
        # # ---------------------------------------------------------
        # # 1. TẠO ADMIN (Nguyễn Đăng Khôi)
        # # ---------------------------------------------------------
        # u_admin = User(
        #     hoTen="Nguyễn Đăng Khôi",
        #     gioiTinh=True,
        #     ngaySinh=date(2004, 2, 21),
        #     diaChi="Thành phố Hồ Chí Minh",
        #     SDT="0762464676",
        #     eMail="khoi123@gmail.com",
        #     taiKhoan='admin',
        #     # Không truyền vaiTro vào đây nữa
        #     avatar='https://res.cloudinary.com/dkolhuqlp/image/upload/v1757611287/bhwvisacx76eb4aluzmw.jpg'
        # )
        # u_admin.set_password('123456')
        # db.session.add(u_admin)
        # db.session.commit()  # Commit để sinh ra ID
        #
        # # Tạo chức danh Nhân Viên cho Admin
        # nv_admin = NhanVien(
        #     user_id=u_admin.id,
        #     vaiTro=UserRole.NGUOIQUANTRI
        # )
        # db.session.add(nv_admin)
        #
        # # ---------------------------------------------------------
        # # 2. TẠO THU NGÂN (Trần Quốc Phong)
        # # ---------------------------------------------------------
        # u_phong = User(
        #     hoTen="Trần Quốc Phong",
        #     gioiTinh=True,
        #     ngaySinh=date(2004, 11, 24),
        #     diaChi="Thành phố Hồ Chí Minh",
        #     SDT="0799773010",
        #     eMail="toquocphong123@gmail.com",
        #     taiKhoan="quocphong",
        #     avatar='https://res.cloudinary.com/dkolhuqlp/image/upload/v1757611287/bhwvisacx76eb4aluzmw.jpg'
        # )
        # u_phong.set_password('123456')
        # db.session.add(u_phong)
        # db.session.commit()
        #
        # # Gán vai trò Thu Ngân
        # nv_phong = NhanVien(
        #     user_id=u_phong.id,
        #     vaiTro=UserRole.THUNGAN
        # )
        # db.session.add(nv_phong)
        #
        # # ---------------------------------------------------------
        # # 3. TẠO LỄ TÂN (Tô Quốc Bình)
        # # ---------------------------------------------------------
        # u_binh = User(
        #     hoTen="Tô Quốc Bình",
        #     gioiTinh=True,
        #     ngaySinh=date(2004, 11, 24),
        #     diaChi="Thành phố Hồ Chí Minh",
        #     SDT="0733546410",
        #     eMail="toquocbinh123@gmail.com",
        #     taiKhoan="binh",
        #     avatar='https://res.cloudinary.com/dkolhuqlp/image/upload/v1757611287/bhwvisacx76eb4aluzmw.jpg'
        # )
        # u_binh.set_password('123456')
        # db.session.add(u_binh)
        # db.session.commit()
        #
        # # Gán vai trò Lễ Tân
        # nv_binh = NhanVien(
        #     user_id=u_binh.id,
        #     vaiTro=UserRole.LETAN
        # )
        # db.session.add(nv_binh)
        # db.session.commit()
        #
        # # ---------------------------------------------------------
        # # 4. TẠO HUẤN LUYỆN VIÊN (Lý Đức)
        # # ---------------------------------------------------------
        # # Bước 1: Tạo User
        # u_hlv = User(
        #     hoTen="Lý Đức",
        #     gioiTinh=True,
        #     ngaySinh=date(1990, 6, 15),
        #     diaChi="Quận 1, TP.HCM",
        #     SDT="0912345678",
        #     eMail="lyduc.gym@gmail.com",
        #     taiKhoan="hlv1",
        #     avatar='https://res.cloudinary.com/dkolhuqlp/image/upload/v1757611287/bhwvisacx76eb4aluzmw.jpg'
        # )
        # u_hlv.set_password('123456')  # Mật khẩu test
        # db.session.add(u_hlv)
        # db.session.commit()  # Commit để có ID
        #
        # nv_hlv = NhanVien(user_id=u_hlv.id, vaiTro=UserRole.HUANLUYENVIEN)
        # db.session.add(nv_hlv)
        #
        # db.session.commit()
