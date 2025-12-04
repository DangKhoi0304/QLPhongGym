from random import choice

from flask import render_template, request, redirect, session, flash, url_for, jsonify
from app import app, db, dao, login

from app.models import UserRole, NhanVien
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import RegisterForm, StaffRegisterForm, RegisterFormStaff, ChangeInfoForm
from app.utils_mail import send_mail_gmail

import cloudinary
import cloudinary.uploader
app.secret_key = 'secret_key'  # Khóa bảo mật cho session

DEFAULT_PASSWORD = "123456"
@app.route('/')
def index():
    return redirect('/login')

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

        # return redirect(url_for('HoiVien/hoi-vien', taikhoan=taiKhoan))

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
    return render_template('HoiVien/hoi_vien.html', taikhoan=taikhoan)

@app.route("/hoso", methods=['GET', 'POST'])
def ho_so():
    form = ChangeInfoForm()
    if form.validate_on_submit():
        hoTen = form.hoTen.data
        gioiTinh = form.gioiTinh.data
        SDT = form.SDT.data
        ngaySinh = form.ngaySinh.data
        diaChi = form.diaChi.data

        success, msg = current_user.update_profile(hoTen, gioiTinh, SDT, ngaySinh, diaChi)

        if success:
            flash(msg, "success")
            return redirect(url_for('ho_so'))
        else:
            flash(msg, "ranger")

    if request.method == 'GET':
        form.hoTen.data = current_user.hoTen
        form.gioiTinh.data = current_user.gioiTinh
        form.SDT.data = current_user.SDT
        form.ngaySinh.data = current_user.ngaySinh
        form.diaChi.data = current_user.diaChi
        # Xử lý riêng cho Giới tính (User lưu True/False nhưng Form Select cần chuỗi '1'/'0')
        form.gioiTinh.data = '1' if current_user.gioiTinh else '0'

    user_info = dao.get_user_by_id(current_user.id)
    return render_template("HoiVien/hoso.html", user_info=user_info, form=form)


@app.route('/api/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file nào được gửi'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Chưa chọn file'}), 400

    if file:
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                public_id=f"avatar_{current_user.id}",
                folder="avatars",  # Tạo thư mục avatars trên Cloudinary
                overwrite=True,
                resource_type="image"
            )

            # Lấy URL ảnh an toàn (https)
            image_url = upload_result['secure_url']

            # Lưu URL vào Database
            current_user.avatar = image_url
            db.session.commit()

            # Trả về URL để hiển thị ngay
            return jsonify({'success': True, 'image_url': image_url})

        except Exception as e:
            app.logger.error(f"Lỗi upload Cloudinary: {e}")
            return jsonify({'error': 'Lỗi khi upload lên Cloudinary'}), 500

    return jsonify({'error': 'File không hợp lệ'}), 400

@app.route('/logout', methods=['GET', 'POST'])
def logout_process():
    logout_user()
    return redirect('/login')

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

@app.route('/dangky/nhanvien', methods=['GET','POST'])
def staff_register():
    form = RegisterFormStaff()
    if form.validate_on_submit():
        hoTen = form.hoTen.data
        gioiTinh = form.gioiTinh.data
        ngaySinh = form.ngaySinh.data
        diaChi = form.diaChi.data
        sdt = form.SDT.data
        email = form.eMail.data
        taiKhoan = form.taiKhoan.data
        goiTap = form.goiTap.data

        matKhau = DEFAULT_PASSWORD

        # Kiểm tra trùng
        if dao.get_user_by_username(taiKhoan):
            flash("Tài khoản đã tồn tại. Vui lòng chọn tên khác.", "danger")
            return render_template('LeTan/dang_ky_hoi_vien.html', form=form)
        if email and dao.get_user_by_email(email):
            flash("Email đã được sử dụng.", "danger")
            return render_template('LeTan/dang_ky_hoi_vien.html', form=form)
        if sdt and dao.get_user_by_phone(sdt):
            flash("Số điện thoại đã được sử dụng.", "danger")
            return render_template('LeTan/dang_ky_hoi_vien.html', form=form)

        # Tạo user — DAO create_user phải chấp nhận goiTap (mã bạn đã cập nhật)
        user = dao.create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau, goiTap)
        if not user:
            flash("Tạo tài khoản thất bại. Vui lòng thử lại.", "danger")
            return render_template('LeTan/dang_ky_hoi_vien.html', form=form)

        # Gửi email xác nhận kèm mật khẩu mặc định
        if email:
            try:
                send_mail_gmail(
                    to_email=email.strip(),
                    subject="Xác nhận đăng ký hội viên - Phòng Gym",
                    plain_text=(
                        f"Xin chào {hoTen},\n\n"
                        f"Bạn đã được tạo tài khoản tại Phòng Gym.\n"
                        f"Tài khoản: {taiKhoan}\n"
                        f"Mật khẩu mặc định: {DEFAULT_PASSWORD}\n\n"
                        "Vui lòng đăng nhập và đổi mật khẩu ngay lần đầu tiên để bảo mật."
                    ),
                    html_text=(
                        f"<p>Xin chào <b>{hoTen}</b>,</p>"
                        f"<p>Bạn đã được tạo tài khoản tại Phòng Gym.</p>"
                        f"<ul>"
                        f"<li><b>Tài khoản:</b> {taiKhoan}</li>"
                        f"<li><b>Mật khẩu mặc định:</b> {DEFAULT_PASSWORD}</li>"
                        f"</ul>"
                        f"<p>Vui lòng đăng nhập và đổi mật khẩu ngay lần đầu tiên để bảo mật.</p>"
                    )
                )
                flash("Đăng ký thành công! Email xác nhận đã được gửi.", "success")
            except Exception as ex:
                app.logger.error("Lỗi gửi mail: %s", ex)
                flash("Đăng ký thành công, nhưng gửi email thất bại.", "warning")
        else:
            flash("Đăng ký thành công!", "success")

        return redirect(url_for('staff_register'))

    return render_template('LeTan/dang_ky_hoi_vien.html', form=form)

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

@app.context_processor
def inject_current_user_role():
    role = None
    try:
        if current_user.is_authenticated:
            # Nếu current_user là nhân viên (có vaiTro)
            if hasattr(current_user, 'vaiTro') and current_user.vaiTro is not None:
                role = current_user.vaiTro.name
            else:
                # Nếu current_user là User → kiểm tra bảng nhanvien
                nv = db.session.get(current_user.id)
                if nv and nv.vaiTro:
                    role = nv.vaiTro.name
    except:
        role = None

    return dict(current_user_role=role)

if __name__ == '__main__':
    from app import admin
    app.run(debug=True)
