from random import choice

from flask import render_template, request, redirect, session, flash, url_for, jsonify
from app import app, db, dao, login

from app.models import UserRole, NhanVien, GoiTap
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import RegisterForm, StaffRegisterForm, RegisterFormStaff, ChangeInfoForm, ChangePasswordForm
from app.utils_mail import send_mail_gmail

from uuid import uuid4
from werkzeug.utils import secure_filename

import cloudinary, math
import cloudinary.uploader

DEFAULT_AVATAR = "/static/images/default-avatar.jpg"
app.secret_key = 'secret_key'  # Khóa bảo mật cho session
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
DEFAULT_PASSWORD = "123456"

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    ds_goi_tap = dao.load_goi_tap(page=page)

    # 2. Truyền biến 'packages' ra template index.html
    return render_template('index.html',
                           packages=ds_goi_tap,
                           pages=math.ceil(dao.count_goi_tap()/app.config['PAGE_SIZE'])
                           )

@app.context_processor
def inject_enums():
    # trả UserRole vào mọi template Jinja => bạn có thể dùng UserRole.NGUOIQUANTRI trong template
    return dict(UserRole=UserRole)

@app.route('/logout', methods=['GET', 'POST'])
def logout_process():
    logout_user()
    return redirect('/login')

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
        #Nếu có next thì quay về trang cũ
        next_page = request.args.get('next') or request.form.get('next')
        if next_page:
            return redirect(next_page)

        # Nếu đối tượng có method get_VaiTro (là NhanVien)
        if user.NhanVienProfile:
            vai_tro = user.NhanVienProfile.vaiTro

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
    active_package = dao.get_active_package_by_user_id(current_user.id)
    return render_template('HoiVien/hoi_vien.html', taikhoan=taikhoan, active_package=active_package)

@app.route("/hoso", methods=['GET', 'POST'])
@login_required
def ho_so():
    form = ChangeInfoForm()
    form_pw = ChangePasswordForm()

    # Xử lý POST — dùng hidden input 'action' để phân biệt
    if request.method == 'POST':
        action = request.form.get('action')

        # ----- cập nhật thông tin profile -----
        if action == 'update_profile':
            # validate_on_submit() sẽ kiểm tra CSRF token + các validator
            if form.validate_on_submit():
                hoTen = form.hoTen.data
                gioiTinh = form.gioiTinh.data
                SDT = form.SDT.data
                ngaySinh = form.ngaySinh.data
                diaChi = form.diaChi.data

                success, msg = current_user.update_profile(hoTen, gioiTinh, SDT, ngaySinh, diaChi)
                if success:
                    flash(msg, "success")
                else:
                    flash(msg, "danger")
                return redirect(url_for('ho_so'))
            else:
                # form lỗi — show lỗi để dev biết
                app.logger.debug("ChangeInfoForm errors: %s", form.errors)
                flash("Form cập nhật thông tin không hợp lệ.", "danger")
                return redirect(url_for('ho_so'))

        # ----- đổi mật khẩu -----
        elif action == 'change_password':
            if form_pw.validate_on_submit():
                current_pw = form_pw.current_password.data
                new_pw = form_pw.new_password.data

                # check mật khẩu hiện tại
                # lưu ý: bạn dùng hiện tại hashing MD5 -> dùng check_password tương ứng
                if not current_user.check_password(current_pw):
                    flash("Mật khẩu hiện tại không đúng.", "danger")
                    return redirect(url_for('ho_so'))

                try:
                    # cập nhật mật khẩu: dùng method set_password của model
                    current_user.set_password(new_pw)
                    db.session.commit()
                    flash("Đổi mật khẩu thành công.", "success")
                except Exception as ex:
                    db.session.rollback()
                    app.logger.exception("Lỗi khi đổi mật khẩu: %s", ex)
                    flash("Đổi mật khẩu thất bại.", "danger")
                return redirect(url_for('ho_so'))
            else:
                app.logger.debug("ChangePasswordForm errors: %s", form_pw.errors)
                flash("Form đổi mật khẩu không hợp lệ.", "danger")
                return redirect(url_for('ho_so'))

        else:
            # POST nhưng không có action rõ ràng
            app.logger.debug("Unknown POST action on /ho_so: %s", request.form.to_dict())
            flash("Yêu cầu không hợp lệ.", "danger")
            return redirect(url_for('ho_so'))

    # ----- GET: fill dữ liệu ban đầu cho form -----
    # Populate ChangeInfoForm từ current_user
    form.hoTen.data = current_user.hoTen
    form.gioiTinh.data = '1' if current_user.gioiTinh else '0'
    form.SDT.data = current_user.SDT
    form.ngaySinh.data = current_user.ngaySinh
    form.diaChi.data = current_user.diaChi

    user_info = dao.get_user_by_id(current_user.id)

    return render_template("HoiVien/ho_so.html", user_info=user_info, form=form, form_pw=form_pw)

    return render_template("HoiVien/ho_so.html", user_info=user_info, form=form)

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
@app.route('/api/buy_package', methods=['POST'])
@login_required
def buy_package():
    data = request.json
    goiTap_id = data['goiTap_id']
    if not goiTap_id:
        return jsonify({'code': 400, 'msg': 'Lỗi: Không tìm thấy gói tập'})

    success, msg = dao.add_receipt(user_id=current_user.id, goiTap_id=goiTap_id, nhanVien_id=None)

    if success:
        return jsonify({'code': 200, 'msg': 'Đăng ký thành công!'})
    else:
        return jsonify({'code': 400, 'msg': msg})


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

        # Xử lý avatar upload (từ input name="avatar")
        avatar_url = DEFAULT_AVATAR
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            # kiểm tra extension
            filename = secure_filename(avatar_file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in ALLOWED_EXT:
                try:
                    # Nếu bạn đã cấu hình cloudinary.config(...) ở chỗ khởi tạo app
                    upload_result = cloudinary.uploader.upload(
                        avatar_file,
                        public_id=f"avatar_{uuid4().hex}",
                        folder="avatars",
                        overwrite=True,
                        resource_type="image",
                        transformation=[{"width": 512, "height": 512, "crop": "limit"}]
                    )
                    avatar_url = upload_result.get('secure_url') or avatar_url
                except Exception as ex:
                    app.logger.exception("Lỗi upload avatar lên Cloudinary: %s", ex)
                    # fallback: để avatar_url = DEFAULT_AVATAR
            else:
                flash("File ảnh không hợp lệ (chỉ jpg/png/gif).", "warning")

        # Tạo user — truyền avatar vào DAO
        user = dao.create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau, avatar=avatar_url)
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
        phuongThuc = form.phuongThuc.data

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
        user = dao.create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau)
        if user:
            try:
                nhanVien_id = current_user.NhanVienProfile.id if current_user.NhanVienProfile else None
                success, msg = dao.add_receipt(
                    user_id=user.id,
                    goiTap_id=goiTap,
                    nhanVien_id=nhanVien_id,
                    payment_method=phuongThuc
                )
                if success:
                    flash(f"Đăng ký thành công cho hội viên {hoTen}!", "success")
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
                    flash(f"Tạo tài khoản thành công nhưng lỗi đăng ký gói: {msg}", "warning")
            except Exception as e:
                flash(f"Lỗi hệ thống khi thanh toán: {str(e)}", "danger")
            else:
                flash("Tạo tài khoản thất bại.", "danger")

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

            if current_user.NhanVienProfile:

                role = current_user.NhanVienProfile.vaiTro.name
    except Exception as e:
        print(f"Lỗi inject role: {e}")
        role = None

    return dict(current_user_role=role)

if __name__ == '__main__':
    from app import admin
    app.run(debug=True)
