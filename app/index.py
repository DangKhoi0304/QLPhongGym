from random import choice

from flask import render_template, request, redirect, session, flash, url_for
from sqlalchemy import and_, Null
from app import app, db, dao, login
from datetime import date, datetime

# from app.dao import get_class_by_id
from app.models import UserRole
from flask_login import login_user, logout_user, current_user, login_required

app.secret_key = 'secret_key'  # Khóa bảo mật cho session

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login_process():
    thong_bao = None
    flag = False
    if request.method.__eq__('POST'):
        taiKhoan = request.form.get('taiKhoan')
        matKhau = request.form['matKhau']
        nv = dao.auth_nhan_vien(taikhoan=taiKhoan, matkhau=matKhau)
        if nv:
            flag=True
            if nv.get_VaiTro() == UserRole.THUNGAN:
                login_user(nv)
                return redirect(f'/nhan-vien/{taiKhoan}')
            elif nv.get_VaiTro() == UserRole.NGUOIQUANTRI:
                login_user(nv)
                return redirect('/admin')
        if not flag:
            gv = dao.auth_nhan_vien(taikhoan=taiKhoan, matkhau=matKhau)
            if gv:
                login_user(gv)
                return redirect(f'/giao-vien/{taiKhoan}')
        thong_bao = "Sai tài khoản/ mật khẩu"
    return render_template('login.html', err_msg=thong_bao)

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

@app.route('/nhan-vien/<taikhoan>')
def thong_tin_nhan_vien(taikhoan):
    return render_template('nhan_vien.html',taikhoan=taikhoan)

@app.route('/giao-vien/<taikhoan>')
def thong_tin_giao_vien(taikhoan):
    gv = dao.get_gv_by_id(current_user.id)
    return render_template('giao_vien.html', taikhoan=taikhoan, giaovien=gv)

@app.route('/logout', methods=['get', 'post'])
def logout_process():
    logout_user()
    return redirect('/login')

@app.route('/nhan-vien/<taikhoan>/nhap-ho-so', methods=['POST'])
def kiem_tra_tuoi(taikhoan):
    session['taikhoan'] = taikhoan
    quy_dinh = dao.get_quy_dinh()
    min_age = quy_dinh.min_age
    max_age = quy_dinh.max_age
    ngay_sinh = request.form.get('ngaySinh')
    if ngay_sinh:
        ngay_sinh = datetime.strptime(ngay_sinh, "%Y-%m-%d").date()
        hom_nay = date.today()
        tuoi = hom_nay.year - ngay_sinh.year
        if min_age <= tuoi <= max_age:
            flash("Tuổi hợp lệ. Hãy nhập thông tin chi tiết.", "success")
            return render_template('nhap_thong_tin_hoc_sinh.html', ngay_sinh=ngay_sinh, taikhoan=taikhoan)
        else:
            flash(f"Tuổi không phù hợp: {tuoi} tuổi!!!", "warning")
            return redirect(f'/nhan-vien/{taikhoan}')
    return "Không nhận được thông tin ngày sinh!"


if __name__ == '__main__':
    from app import admin
    app.run(debug=True)
