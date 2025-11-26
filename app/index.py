from random import choice

from flask import render_template, request, redirect, session, flash, url_for
from app import app, db, dao, login

from app.models import UserRole
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import RegisterForm,StaffRegisterForm
from app.utils_mail import send_mail_gmail

app.secret_key = 'secret_key'  # Khóa bảo mật cho session

@app.route('/')
def index():
    return redirect('/login')

# @app.route('/login', methods=['GET', 'POST'])
# def login_process():
#     thong_bao = None
#     flag = False
#     if request.method.__eq__('POST'):
#         taiKhoan = request.form.get('taiKhoan')
#         matKhau = request.form['matKhau']
#         nv = dao.auth_nhan_vien(taikhoan=taiKhoan, matkhau=matKhau)
#         if nv:
#             flag=True
#             if nv.get_VaiTro() == UserRole.THUNGAN:
#                 login_user(nv)
#                 return redirect(f'/nhan-vien/{taiKhoan}')
#             elif nv.get_VaiTro() == UserRole.NGUOIQUANTRI:
#                 login_user(nv)
#                 return redirect('/admin')
#         if not flag:
#             gv = dao.auth_nhan_vien(taikhoan=taiKhoan, matkhau=matKhau)
#             if gv:
#                 login_user(gv)
#                 return redirect(f'/giao-vien/{taiKhoan}')
#         thong_bao = "Sai tài khoản/ mật khẩu"
#     return render_template('login.html', err_msg=thong_bao)
@app.context_processor
def inject_enums():
    # trả UserRole vào mọi template Jinja => bạn có thể dùng UserRole.NGUOIQUANTRI trong template
    return dict(UserRole=UserRole)

@app.route('/login', methods=['GET', 'POST'])
def login_process():
    thong_bao = None
    if request.method == 'POST':
        taiKhoan = request.form.get('taiKhoan')
        matKhau = request.form.get('matKhau')

        user = dao.auth_nhan_vien(taikhoan=taiKhoan, matkhau=matKhau)
        if not user:
            thong_bao = "Sai tài khoản/ mật khẩu"
            return render_template('login.html', err_msg=thong_bao)

        # đăng nhập thành công
        login_user(user)

        # Nếu đối tượng có method get_VaiTro (là NhanVien)
        if hasattr(user, 'get_VaiTro'):
            try:
                vai_tro = user.get_VaiTro()
            except Exception:
                vai_tro = None

            if vai_tro == UserRole.THUNGAN:
                return redirect(f'/nhan-vien/{taiKhoan}')
            elif vai_tro == UserRole.NGUOIQUANTRI:
                return redirect('/admin')
            else:
                # Nếu có vai trò khác, bạn có thể thêm logic ở đây
                return redirect(f'/nhan-vien/{taiKhoan}')

        # Nếu không có vaiTro => là hội viên bình thường
        return redirect(url_for('hoi_vien', taikhoan=taiKhoan))

    return render_template('login.html', err_msg=thong_bao)

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

@app.route('/nhan-vien/<taikhoan>')
def thong_tin_nhan_vien(taikhoan):
    return render_template('nhan_vien.html',taikhoan=taikhoan)

@app.route('/hoi-vien/<taikhoan>')
@login_required
def hoi_vien(taikhoan):
    return render_template('hoi_vien.html', taikhoan=taikhoan)

# @app.route('/giao-vien/<taikhoan>')
# def thong_tin_giao_vien(taikhoan):
#     gv = dao.get_gv_by_id(current_user.id)
#     return render_template('giao_vien.html', taikhoan=taikhoan, giaovien=gv)

@app.route('/logout', methods=['get', 'post'])
def logout_process():
    logout_user()
    return redirect('/login')

# @app.route('/nhan-vien/<taikhoan>/nhap-ho-so', methods=['POST'])
# def kiem_tra_tuoi(taikhoan):
#     session['taikhoan'] = taikhoan
#     quy_dinh = dao.get_quy_dinh()
#     min_age = quy_dinh.min_age
#     max_age = quy_dinh.max_age
#     ngay_sinh = request.form.get('ngaySinh')
#     if ngay_sinh:
#         ngay_sinh = datetime.strptime(ngay_sinh, "%Y-%m-%d").date()
#         hom_nay = date.today()
#         tuoi = hom_nay.year - ngay_sinh.year
#         if min_age <= tuoi <= max_age:
#             flash("Tuổi hợp lệ. Hãy nhập thông tin chi tiết.", "success")
#             return render_template('nhap_thong_tin_hoc_sinh.html', ngay_sinh=ngay_sinh, taikhoan=taikhoan)
#         else:
#             flash(f"Tuổi không phù hợp: {tuoi} tuổi!!!", "warning")
#             return redirect(f'/nhan-vien/{taikhoan}')
#     return "Không nhận được thông tin ngày sinh!"
#
# @app.route('/thay-doi-thong-tin', methods=['GET','POST'], endpoint='change_info')
# @login_required
# def change_info():
#     form = ChangeInfoForm(obj=current_user)
#     if form.validate_on_submit():
#         current_user.hoTen = form.ho_va_ten.data
#         current_user.eMail = form.email.data
#         current_user.SDT = form.so_dien_thoai.data
#         current_user.taiKhoan = form.tai_khoan.data
#         if hasattr(current_user, 'cccd') and hasattr(form, 'cccd'):
#             current_user.cccd = form.cccd.data
#
#         db.session.commit()
#         flash("Cập nhật thông tin thành công.", "success")
#         return redirect(url_for('change_info'))
#
#     return render_template('thaydoithongtin.html', form=form)


@app.route('/dangky', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Lấy dữ liệu từ form
        hoTen = form.hoTen.data
        gioiTinh = form.gioiTinh.data
        ngaySinh = form.ngaySinh.data
        diaChi = form.diaChi.data
        sdt = form.SDT.data
        email = form.eMail.data
        taiKhoan = form.taiKhoan.data
        matKhau = form.matKhau.data

        # Kiểm tra trùng
        if dao.get_user_by_username(taiKhoan):
            flash("Tài khoản đã tồn tại. Vui lòng chọn tên khác.", "danger")
            return render_template('register.html', form=form)
        if email and dao.get_user_by_email(email):
            flash("Email đã được sử dụng.", "danger")
            return render_template('register.html', form=form)
        if sdt and dao.get_user_by_phone(sdt):
            flash("Số điện thoại đã được sử dụng.", "danger")
            return render_template('register.html', form=form)

        # Tạo user (dao.create_user sẽ hash MD5 như hiện tại)
        user = dao.create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau)
        if not user:
            flash("Tạo tài khoản thất bại. Vui lòng thử lại.", "danger")
            return render_template('register.html', form=form)

        # Gửi email xác nhận (dùng send_mail_gmail từ app/utils_mail.py)
        if email and email.strip():
            try:
                send_mail_gmail(
                    to_email=email.strip(),
                    subject="Xác nhận đăng ký hội viên",
                    plain_text=f"Xin chào {hoTen},\nBạn đã đăng ký thành công tài khoản {taiKhoan}.",
                    html_text=f"<p>Xin chào <b>{hoTen}</b>,</p>"
                              f"<p>Bạn đã đăng ký thành công tài khoản <b>{taiKhoan}</b> tại phòng Gym.</p>"
                )
                flash("Đăng ký thành công! Email xác nhận đã được gửi.", "success")
            except Exception as ex:
                # log lỗi để debug
                app.logger.error("Lỗi gửi mail: %s", ex)
                flash("Đăng ký thành công, nhưng gửi email thất bại.", "warning")
        else:
            flash("Đăng ký thành công!", "success")

        return redirect(url_for('login_process'))

    return render_template('register.html', form=form)

@app.route('/nhan-vien/dangky-hlv', methods=['GET','POST'])
@login_required
def staff_dangky_hlv():
    # BỎ kiểm tra vai trò — ai đã login cũng được mở form để tạo HLV
    form = RegisterForm()

    # Debug: ghi nhận khi có POST đến
    if request.method == 'POST':
        app.logger.debug("=== POST to /nhan-vien/dangky-hlv ===")
        app.logger.debug("request.form: %s", request.form.to_dict())

    # Nếu form hợp lệ -> xử lý tạo user
    if form.validate_on_submit():
        app.logger.debug("Form validated OK. form.data: %s", form.data)
        try:
            user = dao.create_user(
                form.hoTen.data,
                form.gioiTinh.data,
                form.ngaySinh.data,
                form.diaChi.data,
                form.SDT.data,
                form.eMail.data,
                form.taiKhoan.data,
                form.matKhau.data
            )
        except Exception as ex:
            app.logger.exception("Exception khi gọi dao.create_user:")
            flash("Lỗi khi tạo user: " + str(ex), "danger")
            return render_template('dangky_hlv.html', form=form)

        if not user:
            # dao trả None khi trùng hoặc lỗi theo logic của bạn
            app.logger.debug("dao.create_user returned falsy (None/False).")
            flash("Tạo tài khoản thất bại (có thể trùng username/email/SĐT).", "danger")
            # show form.errors nếu có
            try:
                app.logger.debug("form.errors (after validate): %s", form.errors)
            except Exception:
                pass
            return render_template('dangky_hlv.html', form=form)

        # tạo record huanluyenvien (dao helper)
        try:
            ok = dao.create_huanluyenvien_from_user(user)
            app.logger.debug("create_huanluyenvien_from_user returned: %s", ok)
        except Exception as ex:
            app.logger.exception("Exception khi tạo huanluyenvien:")
            flash("Tạo HLV thành công nhưng có lỗi khi lưu huấn luyện viên: " + str(ex), "warning")
            return redirect(url_for('thong_tin_nhan_vien', taikhoan=current_user.taiKhoan))

        if ok:
            flash("Tạo HLV thành công và lưu vào huanluyenvien.", "success")
        else:
            flash("Tạo HLV thành công nhưng lưu vào huanluyenvien thất bại.", "warning")

        return redirect(url_for('thong_tin_nhan_vien', taikhoan=current_user.taiKhoan))

    # Nếu là POST nhưng validate thất bại -> show lỗi để debug
    if request.method == 'POST' and not form.validate():
        app.logger.debug("Form.validate_on_submit() == False. form.errors: %s", form.errors)
        flash("Form không hợp lệ: " + str(form.errors), "danger")

    return render_template('dangky_hlv.html', form=form)



if __name__ == '__main__':
    from app import admin
    app.run(debug=True)
