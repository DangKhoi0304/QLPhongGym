from datetime import date, datetime
from app import db, app
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, BOOLEAN, Date, Enum, UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum as RoleEnum, unique
from flask_login import UserMixin
import hashlib
from sqlalchemy.orm import relationship, Relationship


class UserRole(RoleEnum):
    NGUOIQUANTRI = 1
    THUNGAN = 2
    LETAN = 3


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    # goiTap = Column(Integer, nullable=True)

    def update_profile(self, hoTen, gioiTinh,SDT, ngaySinh, diaChi):
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

    def __str__(self):
        return self.hoTen

    def get_id(self):
        return str(self.id)

    # thêm method get_username và property username để template dùng thoải mái
    def get_username(self):
        # trả tên hiển thị (bạn có thể đổi thành self.taiKhoan nếu muốn)
        return self.hoTen

    @property
    def username(self):
        return self.get_username()

    def set_password(self, password):
        # dùng werkzeug để hash an toàn
        self.matKhau = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return check_password_hash(self.matKhau, password)


class NhanVien(User):
    __tablename__ = 'nhanvien'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    vaiTro = Column(Enum(UserRole))

    def get_VaiTro(self):
        return self.vaiTro

class HuanLuyenVien(db.Model):
    __tablename__ = 'huanluyenvien'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)  # <-- PK = FK users.id
    hoTen = db.Column(db.String(255))
    SDT = db.Column(db.String(20))
    eMail = db.Column(db.String(255))

    user = db.relationship('User', backref=db.backref('huanluyenvien', uselist=False))

if __name__== '__main__':
    with app.app_context():
        db.create_all()

        # Tạo user test - dùng set_password để hash an toàn
        # u = NhanVien(
        #     hoTen="Nguyễn Đăng Khôi",
        #     gioiTinh=True,
        #     ngaySinh=date(2004, 2, 21),
        #     diaChi="Thành phố Hồ Chí Minh",
        #     SDT="0762464676",
        #     eMail="khoi123@gmail.com",
        #     taiKhoan='admin',
        #     vaiTro=UserRole.NGUOIQUANTRI
        # )
        # u.set_password('123456')
        # db.session.add(u)
        #
        #
        # nv = NhanVien(
        #     hoTen="Trần Quốc Phong",
        #     gioiTinh=True,
        #     ngaySinh=date(2004, 11, 24),
        #     diaChi="Thành phố Hồ Chí Minh",
        #     SDT="0799773010",
        #     eMail="toquocphong123@gmail.com",
        #     vaiTro=UserRole.THUNGAN,
        #     taiKhoan="quocphong",
        # )
        # nv.set_password('123456')
        # db.session.add(nv)
        # db.session.commit()
        #
        # nv = NhanVien(
        #     hoTen="Tô Quốc Bình",
        #     gioiTinh=True,
        #     ngaySinh=date(2004, 11, 24),
        #     diaChi="Thành phố Hồ Chí Minh",
        #     SDT="0733546410",
        #     eMail="toquocbinh123@gmail.com",
        #     vaiTro=UserRole.LETAN,
        #     taiKhoan="binh",
        # )
        # nv.set_password('123456')
        # db.session.add(nv)
        # db.session.commit()

