from datetime import date
from email.policy import default

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
    __tablename__ = 'users'  # Tạo bảng User trong DB

    id = Column(Integer, primary_key=True, autoincrement=True)
    hoTen = Column(String(50), nullable=False)
    gioiTinh = Column(Boolean, nullable=False)
    ngaySinh = Column(Date, nullable=False)
    diaChi = Column(String(255), nullable=False)
    SDT = Column(String(20), unique=True, nullable=False)
    eMail = Column(String(255), unique=True, nullable=False)
    taiKhoan = Column(String(50), unique=True, nullable=False)
    matKhau = Column(String(255), nullable=False)

    def __str__(self):
        return self.hoTen

    def get_id(self):
        return str(self.id)

    def get_taiKhoan(self):
        return self.taiKhoan

    def set_password(self, password):
        self.matKhau = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.matKhau, password)


class NhanVien(User):
    __tablename__ = 'nhanvien'  # Tạo bảng NhanVien trong DB, không tạo bảng User

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)  # Khóa ngoại trỏ tới bảng users
    vaiTro = Column(Enum(UserRole))

    def get_VaiTro(self):
        return self.vaiTro


if __name__== '__main__':
    with app.app_context():
        db.create_all()

        u = NhanVien(hoTen="Nguyễn Đăng Khôi", gioiTinh=True, ngaySinh=date(2004, 2, 21),
                     diaChi="Thành phố Hồ Chí Minh",SDT="0762464676",eMail="khoi123@gmail.com",
                     taiKhoan='admin', matKhau=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                     vaiTro=UserRole.NGUOIQUANTRI)
        db.session.add(u)
        # db.session.commit()


        # Tạo nhân viên
        nv = NhanVien(
            hoTen="Trần Quốc Phong",
            gioiTinh=True,
            ngaySinh=date(2004, 11, 24),
            diaChi="Thành phố Hồ Chí Minh",
            SDT="0799773010",
            eMail="toquocphong123@gmail.com",
            vaiTro=UserRole.THUNGAN,
            taiKhoan="quocphong",
            matKhau=str(hashlib.md5('123456'.encode('utf-8')).hexdigest())
        )
        db.session.add(nv)
        db.session.commit()
