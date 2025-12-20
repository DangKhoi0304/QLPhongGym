from random import choice

from flask import render_template, request, redirect, session, flash, url_for, jsonify
from app import app, db, dao, login
from datetime import timedelta, datetime
from app.models import UserRole, NhanVien, GoiTap, DangKyGoiTap, DanhMucBaiTap, QuyDinh
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import RegisterForm, StaffRegisterForm, RegisterFormStaff, ChangeInfoForm, ChangePasswordForm, \
    TaoLichTapForm, ChonHLVForm, SuaLichTapForm, GiaHanForm
from app.utils_mail import send_mail_gmail

from uuid import uuid4
from werkzeug.utils import secure_filename
import re
import cloudinary, math
import cloudinary.uploader

DEFAULT_AVATAR = "default"
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

        # Xác thực user (hàm này check trong bảng User)
        user = dao.auth_nhan_vien(taikhoan=taiKhoan, matkhau=matKhau)

        if not user:
            thong_bao = "Sai tài khoản hoặc mật khẩu."
            return render_template('login.html', err_msg=thong_bao)

        # Đăng nhập thành công
        login_user(user)

        # Nếu có next page (trang người dùng muốn vào trước đó) thì ưu tiên chuyển hướng
        next_page = request.args.get('next') or request.form.get('next')
        if next_page:
            return redirect(next_page)

        # --- PHÂN QUYỀN CHUYỂN HƯỚNG (ROUTING) ---

        # 1. Kiểm tra: Có phải Nhân Viên (Admin, Thu ngân, Lễ tân) không?
        # (Dựa vào backref 'NhanVienProfile' trong models.py)
        if user.NhanVienProfile:
            vai_tro = user.NhanVienProfile.vaiTro

            # Nếu là Admin
            if vai_tro == UserRole.NGUOIQUANTRI:
                return redirect('/admin')

            # Nếu là Thu ngân hoặc Lễ tân
            # (Bạn có thể tách riêng if nếu muốn trang khác nhau, ở đây mình gom chung)
            elif vai_tro == UserRole.THUNGAN or vai_tro == UserRole.LETAN:
                return redirect(f'/nhan-vien/{taiKhoan}')

        # 2. Kiểm tra: Có phải Huấn Luyện Viên không? [MỚI]
        # (Dựa vào backref 'huanluyenvien' trong models.py)
        if getattr(user, 'huanluyenvien', None):
            # Chuyển hướng đến trang dashboard dành riêng cho HLV
            return redirect(f'/nhan-vien/{taiKhoan}')

        # 3. Mặc định: Là Hội Viên
        return redirect(url_for('hoi_vien', taikhoan=taiKhoan))

    # Nếu là GET request thì trả về trang login
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

@app.route('/hoi-vien/<taikhoan>/lich_su')
@login_required
def hoi_vien_lich_su(taikhoan):
    if current_user.taiKhoan != taikhoan:
        flash("Bạn không có quyền truy cập lịch sử của người khác.", "danger")
        return redirect(url_for('index'))

    history = dao.get_payment_history_by_id(current_user.id)
    return render_template('HoiVien/lich_su_giao_dich.html', taikhoan=taikhoan, history=history)

@app.route("/hoso", methods=['GET', 'POST'])
@login_required
def ho_so():
    form = ChangeInfoForm()
    form_pw = ChangePasswordForm()

    # --- XỬ LÝ POST (Cập nhật thông tin / Đổi mật khẩu) ---
    if request.method == 'POST':
        action = request.form.get('action')

        # 1. Cập nhật thông tin cá nhân
        if action == 'update_profile':
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
                app.logger.debug("ChangeInfoForm errors: %s", form.errors)
                flash("Form cập nhật thông tin không hợp lệ.", "danger")
                return redirect(url_for('ho_so'))

        # 2. Đổi mật khẩu
        elif action == 'change_password':
            if form_pw.validate_on_submit():
                current_pw = form_pw.current_password.data
                new_pw = form_pw.new_password.data

                if not current_user.check_password(current_pw):
                    flash("Mật khẩu hiện tại không đúng.", "danger")
                    return redirect(url_for('ho_so'))

                try:
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
            flash("Yêu cầu không hợp lệ.", "danger")
            return redirect(url_for('ho_so'))

    # --- XỬ LÝ GET (Hiển thị form) ---

    # Fill dữ liệu cũ vào form
    form.hoTen.data = current_user.hoTen
    form.gioiTinh.data = '1' if current_user.gioiTinh else '0'
    form.SDT.data = current_user.SDT
    form.ngaySinh.data = current_user.ngaySinh
    form.diaChi.data = current_user.diaChi

    user_info = dao.get_user_by_id(current_user.id)

    # [QUAN TRỌNG] Logic chọn Layout Header
    # Mặc định là layout của Hội viên
    layout_template = 'layout/base.html'

    # Nếu là Nhân viên hoặc HLV -> Dùng layout Nhân viên
    if current_user.NhanVienProfile or getattr(current_user, 'huanluyenvien', None):
        layout_template = 'layoutNhanVien/base.html'

    return render_template("HoiVien/ho_so.html",
                           user_info=user_info,
                           form=form,
                           form_pw=form_pw,
                           layout=layout_template)  # Truyền biến layout qua đây

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
    if current_user.NhanVienProfile or getattr(current_user, 'huanluyenvien', None):
        return jsonify({'code': 403, 'msg': 'Tài khoản nội bộ không thể mua gói tập.'})

    data = request.json
    goiTap_id = data['goiTap_id']
    if not goiTap_id:
        return jsonify({'code': 400, 'msg': 'Lỗi: Không tìm thấy gói tập'})

    success, msg = dao.add_receipt(user_id=current_user.id, goiTap_id=goiTap_id, nhanVien_id=None)

    if success:
        return jsonify({'code': 200, 'msg': 'Đăng ký thành công!'})
    else:
        return jsonify({'code': 400, 'msg': msg})

@app.route('/thu-ngan/quan-ly-thanh-toan', methods=['GET', 'POST'])
@login_required
def payment_management():
    # Quyền truy cập
    if not current_user.NhanVienProfile or current_user.NhanVienProfile.vaiTro not in [UserRole.THUNGAN, UserRole.NGUOIQUANTRI]:
        flash("Bạn không có quyền truy cập", "danger")
        return redirect('/')

    form = GiaHanForm()
    packages = dao.get_all_packages()
    form.goiTap_id.choices = [
        (p.id, f"{p.tenGoiTap} - {int(p.giaTienGoi):,} VNĐ") for p in packages
    ]

    if form.validate_on_submit():
        user_id = form.user_id.data
        goiTap_id = form.goiTap_id.data
        phuong_thuc = form.phuong_thuc.data

        success, msg = dao.add_receipt(
            user_id=user_id,
            goiTap_id=goiTap_id,
            nhanVien_id=current_user.NhanVienProfile.id,
            payment_method=phuong_thuc
        )

        if success:
            flash(f"Gia hạn thành công! {msg}", "success")
        else:
            flash(f"Không thể gia hạn: {msg}", "danger")

        return redirect(request.url)  # Reload trang để clear form

        # Nếu form submit bị lỗi (ví dụ thiếu field), in lỗi ra log để debug
    if form.errors:
        print("Form Errors:", form.errors)
        flash("Dữ liệu gửi lên không hợp lệ.", "danger")

        # 5. Xử lý hiển thị danh sách (GET) - Giữ nguyên logic tìm kiếm cũ
    keyword = request.args.get('keyword', '')
    members_raw = dao.get_all_member(keyword)

    members_data = []
    if members_raw:
        for m in members_raw:
            active_pack = dao.get_active_package_by_user_id(m.id)
            members_data.append({
                'info': m,
                'active_pack': active_pack
            })

    # Truyền biến form sang template
    return render_template('ThuNgan/quan_ly_thanh_toan.html',
                           members=members_data,
                           form=form,  # <-- Truyền form vào đây
                           keyword=keyword)


@app.route('/api/payment-history/<int:user_id>')
@login_required
def get_payment_history_api(user_id):
    # Kiểm tra quyền thu ngân/admin
    if not current_user.NhanVienProfile:
        flash("Bạn không có quyền truy cập", "danger")
        return redirect('/')

    history = dao.get_payment_history_by_id(user_id)
    data = []
    for p in history:
        ten_goi = None
        if p.dang_ky and p.dang_ky.goi_tap:
            ten_goi = p.dang_ky.goi_tap.tenGoiTap

        data.append({
            'ngay' : p.ngayThanhToan.strftime('%d/%m/%Y'),
            'goi' : ten_goi,
            'tien': "{:,.0f}".format(p.soTienTT),
            'phuong_thuc': p.phuongThuc

        })
    return jsonify(data)

@app.route('/thu-ngan/thong-ke')
@login_required
def thong_ke_doanh_thu():
    if not current_user.NhanVienProfile or current_user.NhanVienProfile.vaiTro not in [UserRole.THUNGAN, UserRole.NGUOIQUANTRI]:
        flash("Bạn không có quyền truy cập", "danger")
        return redirect('/')
    year = request.args.get('year', datetime.now().year, type=int)
    raw_revenue = dao.stats_revenue(year)
    data_members= dao.stats_member_growth(year)
    total_active = dao.count_active_members()

    package_name = set(item[1] for item in raw_revenue)
    revenue_datasets = {name: [0]*12 for name in package_name}

    total_revenue = 0
    for thang, ten_goi, tien in raw_revenue:
        idx = int(thang) -1
        revenue_datasets[ten_goi][idx] =tien
        total_revenue+=tien

    colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796']

    final_revenue_datasets = []
    for i, (pkg_name, data) in enumerate(revenue_datasets.items()):
        final_revenue_datasets.append({
            'label': pkg_name,
            'data': data,
            'backgroundColor': colors[i % len(colors)],
            'stack': 'Stack 0',
        })

    # 3. Xử lý dữ liệu Hội viên (Giữ nguyên logic cũ)
    member_values = [0] * 12
    for mon, val in data_members:
        member_values[int(mon) - 1] = val

    month_labels = [f"Tháng {i}" for i in range(1, 13)]

    return render_template('ThuNgan/thong_ke_bao_cao.html',
                           month_labels=month_labels,
                           revenue_datasets=final_revenue_datasets,  # <-- Truyền biến mới này
                           total_revenue=total_revenue,  # <-- Truyền tổng doanh thu
                           member_values=member_values,
                           total_active=total_active,
                           selected_year=year)

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

        avatar_url = DEFAULT_AVATAR
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            # kiểm tra extension
            filename = secure_filename(avatar_file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in ALLOWED_EXT:
                try:
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
            else:
                flash("File ảnh không hợp lệ (chỉ jpg/png/gif).", "warning")

        # Tạo user — DAO create_user phải chấp nhận goiTap (mã bạn đã cập nhật)
        user = dao.create_user(hoTen, gioiTinh, ngaySinh, diaChi, sdt, email, taiKhoan, matKhau, avatar=avatar_url)
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
        # else:
        #     flash("Tạo tài khoản thất bại.", "danger")

        return redirect(url_for('staff_register'))

    return render_template('LeTan/dang_ky_hoi_vien.html', form=form)

@app.route('/chon-hlv', methods=['GET', 'POST'])
@login_required
def choose_pt():
    # ... (giữ nguyên logic kiểm tra gói tập active) ...
    active_package = dao.get_active_package_by_user_id(current_user.id)
    if not active_package:
        return redirect('/')

    form = ChonHLVForm()

    if form.validate_on_submit():
        hlv_id = form.hlv_id.data
        if dao.assign_pt_for_member(current_user.id, hlv_id):
            flash("Đăng ký Huấn luyện viên thành công!", "success")
            return redirect(url_for('hoi_vien', taikhoan=current_user.taiKhoan))
        else:
            flash("Có lỗi xảy ra.", "danger")

    ds_hlv = dao.load_all_huanluyenvien()
    return render_template('HoiVien/chon_hlv.html', ds_hlv=ds_hlv, form=form)


@app.route('/hlv-panel/tao-lich/<int:dangky_id>', methods=['GET', 'POST'])
@login_required
def create_schedule(dangky_id):
    # 1. Kiểm tra quyền
    if not getattr(current_user, 'huanluyenvien', None):
        return redirect('/')

    form = TaoLichTapForm()

    # 2. Load dữ liệu gợi ý
    ds_bai_tap = DanhMucBaiTap.query.all()
    goi_y_list = [b.ten_bai_tap for b in ds_bai_tap]
    data_map = {b.ten_bai_tap: b.nhom_co for b in ds_bai_tap}

    if form.validate_on_submit():
        raw_dates_str = form.ngayTap.data
        formatted_list = []

        if raw_dates_str:
            # --- BƯỚC 1: LẤY DANH SÁCH NGÀY MỚI ---
            new_dates_list = [d.strip().replace('-', '/') for d in raw_dates_str.split(',') if d.strip()]

            # --- BƯỚC 2: LẤY DANH SÁCH NGÀY CŨ TỪ DB ---
            lich_cu = dao.get_schedule_by_dangky(dangky_id)
            old_dates_list = []
            for lich in lich_cu:
                found_dates = re.findall(r'\d{2}/\d{2}/\d{4}', lich.ngayTap)
                old_dates_list.extend(found_dates)

            # --- [LOGIC MỚI] BƯỚC 3: KIỂM TRA QUY ĐỊNH THEO TỪNG TUẦN ---

            # Lấy quy định tối đa
            quydinh = QuyDinh.query.filter_by(ten_quy_dinh="Số ngày tập tối đa").first()

            if quydinh:
                max_days = int(quydinh.gia_tri)

                # Tạo Dictionary để gom nhóm: Key=(Năm, Tuần), Value={Set các ngày}
                # Ví dụ: { (2025, 52): {'22/12', '24/12'}, (2026, 1): {'05/01'} }
                map_old = {}  # Ngày cũ trong DB
                map_total = {}  # Tổng (Cũ + Mới)

                # Hàm helper để gom nhóm ngày vào map
                def group_dates_by_week(date_list, target_map):
                    for d_str in date_list:
                        try:
                            dt = datetime.strptime(d_str, '%d/%m/%Y')
                            # Lấy (Năm, Số tuần) theo chuẩn ISO. Ví dụ: (2025, 52)
                            key_week = dt.isocalendar()[:2]

                            if key_week not in target_map:
                                target_map[key_week] = set()
                            target_map[key_week].add(d_str)
                        except ValueError:
                            continue

                # Gom nhóm dữ liệu
                group_dates_by_week(old_dates_list, map_old)
                group_dates_by_week(old_dates_list + new_dates_list, map_total)

                # DUYỆT QUA TỪNG TUẦN ĐỂ KIỂM TRA
                for week_key, dates_in_week in map_total.items():
                    current_total = len(dates_in_week)  # Số ngày trong tuần này (sau khi thêm)

                    # Lấy số ngày cũ của tuần này (nếu có)
                    old_count = len(map_old.get(week_key, set()))

                    # LOGIC THÔNG MINH (Giữ lại logic bạn thích):
                    # Nếu tuần này TRƯỚC ĐÓ đã vi phạm (Cũ > Max), nhưng lần này không thêm ngày mới -> Cho qua
                    if old_count > max_days:
                        if current_total > old_count:
                            year, week_num = week_key
                            flash(
                                f"Tuần {week_num}/{year}: Lịch cũ ({old_count} ngày) đã quá quy định. Bạn không được thêm ngày mới vào tuần này.",
                                "danger")
                            return redirect(url_for('create_schedule', dangky_id=dangky_id))

                    # Nếu tuần này TRƯỚC ĐÓ bình thường, giờ thêm vào bị lố -> Chặn
                    else:
                        if current_total > max_days:
                            year, week_num = week_key
                            flash(
                                f"Tuần {week_num}/{year}: Bạn chọn {current_total} ngày. Quy định tối đa {max_days} ngày/tuần.",
                                "danger")
                            return redirect(url_for('create_schedule', dangky_id=dangky_id))

            # -----------------------------------------------------------

            # --- BƯỚC 4: XỬ LÝ FORMAT VÀ LƯU (Như cũ) ---
            temp_dates = []
            for d_str in new_dates_list:
                try:
                    dt = datetime.strptime(d_str, '%d/%m/%Y')
                    temp_dates.append(dt)
                except ValueError:
                    continue

            temp_dates.sort()

            days_map = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ Nhật']
            for date_obj in temp_dates:
                day_name = days_map[date_obj.weekday()]
                formatted_item = f"{day_name} ({date_obj.strftime('%d/%m/%Y')})"
                formatted_list.append(formatted_item)

        final_ngay_tap = ", ".join(formatted_list)

        if dao.add_schedule(dangky_id, form.baiTap.data, form.nhomCo.data, form.soHiep.data, form.soLan.data,
                            final_ngay_tap):
            flash("Thêm bài tập thành công!", "success")
            return redirect(url_for('create_schedule', dangky_id=dangky_id))
        else:
            flash("Lỗi khi thêm lịch.", "danger")

    current_schedule = dao.get_schedule_by_dangky(dangky_id)
    dk = DangKyGoiTap.query.get(dangky_id)

    return render_template('HuanLuyenVien/tao_lich.html',
                           form=form,
                           schedule=current_schedule,
                           member=dk.hoi_vien,
                           dangky_id=dangky_id,
                           data_map=data_map,
                           goi_y_list=goi_y_list)

@app.route('/hoi-vien/lich-tap')
@login_required
def member_view_schedule():
    # 1. Lấy gói tập đang kích hoạt của user hiện tại
    active_package = dao.get_active_package_by_user_id(current_user.id)

    if not active_package:
        flash("Bạn chưa đăng ký gói tập nào!", "warning")
        # Nếu chưa có gói tập, quay về trang dashboard
        return redirect(url_for('hoi_vien', taikhoan=current_user.taiKhoan))

    # 2. Lấy danh sách lịch tập dựa trên gói đăng ký ID
    # (Hàm dao.get_schedule_by_dangky bạn đã thêm vào dao.py ở bước trước)
    schedule = dao.get_schedule_by_dangky(active_package.id)

    # 3. Trả về giao diện xem lịch
    return render_template('HoiVien/xem_lich_tap.html',
                           schedule=schedule,
                           hlv=active_package.huan_luyen_vien)


@app.route('/hlv/danh-sach-hoi-vien')
@login_required
def danh_sach_hoi_vien():
    # 1. Kiểm tra quyền: Phải là HLV mới được vào
    if not getattr(current_user, 'huanluyenvien', None):
        flash("Bạn không có quyền truy cập trang này", "danger")
        return redirect('/')

    # 2. Lấy danh sách hội viên (đặt tên biến tiếng Việt cho dễ hiểu)
    ds_hoi_vien = dao.get_members_by_hlv(current_user.id)

    # 3. Render giao diện (đổi tên file html luôn)
    return render_template('HuanLuyenVien/danh_sach_hoi_vien.html', ds_hoi_vien=ds_hoi_vien)


# --- ROUTE XÓA LỊCH TẬP ---
@app.route('/hlv-panel/xoa-lich/<int:id>')
@login_required
def delete_schedule_item(id):
    # Lấy thông tin lịch để biết nó thuộc về gói đăng ký nào (để redirect về đúng chỗ)
    lich = dao.get_schedule_item_by_id(id)
    if not lich:
        flash("Lịch tập không tồn tại.", "danger")
        return redirect('/hlv/danh-sach-hoi-vien')

    dangky_id = lich.dangKyGoiTap_id

    if dao.delete_schedule(id):
        flash("Đã xóa bài tập thành công!", "success")
    else:
        flash("Lỗi khi xóa.", "danger")

    # Quay lại trang tạo lịch của hội viên đó
    return redirect(url_for('create_schedule', dangky_id=dangky_id))


# --- ROUTE SỬA LỊCH TẬP ---
@app.route('/hlv-panel/sua-lich/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_schedule_item(id):
    lich = dao.get_schedule_item_by_id(id)
    if not lich: return redirect('/')

    form = SuaLichTapForm()

    # --- CHUẨN BỊ DỮ LIỆU GỢI Ý (Giống trang tạo lịch) ---
    ds_bai_tap = DanhMucBaiTap.query.all()
    goi_y_list = [b.ten_bai_tap for b in ds_bai_tap]
    data_map = {b.ten_bai_tap: b.nhom_co for b in ds_bai_tap}
    # -----------------------------------------------------

    # XỬ LÝ POST (LƯU)
    if form.validate_on_submit():
        # Xử lý ngày tháng (Code cũ giữ nguyên)
        raw_dates_str = form.ngayTap.data
        formatted_list = []
        if raw_dates_str:
            raw_list = [d.strip() for d in raw_dates_str.split(',') if d.strip()]
            for d_str in raw_list:
                try:
                    date_obj = datetime.strptime(d_str, '%d-%m-%Y')
                    day_name = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ Nhật'][date_obj.weekday()]
                    formatted_list.append(f"{day_name} ({date_obj.strftime('%d/%m/%Y')})")
                except ValueError:
                    continue
        final_ngay_tap = ", ".join(formatted_list)

        # Gọi hàm update (thêm tham số nhomCo)
        if dao.update_schedule(id,
                               form.baiTap.data,
                               form.nhomCo.data,  # <--- Cập nhật nhóm cơ
                               form.soHiep.data,
                               form.soLan.data,
                               final_ngay_tap):
            flash("Cập nhật thành công!", "success")
            return redirect(url_for('create_schedule', dangky_id=lich.dangKyGoiTap_id))
        else:
            flash("Lỗi cập nhật.", "danger")

    # XỬ LÝ GET (HIỂN THỊ DỮ LIỆU CŨ)
    if request.method == 'GET':
        form.baiTap.data = lich.baiTap
        form.nhomCo.data = lich.nhom_co
        form.soHiep.data = lich.soHiep
        form.soLan.data = lich.soLan

        # [QUAN TRỌNG] Xử lý ngày tháng để hiện lại lên lịch
        # Dữ liệu trong DB dạng: "Thứ 2 (22/12/2025), Thứ 4 (24/12/2025)"
        if lich.ngayTap:
            # 1. Dùng Regex để chỉ lấy phần ngày tháng (22/12/2025)
            dates = re.findall(r'\d{2}/\d{2}/\d{4}', lich.ngayTap)

            # 2. Đổi dấu / thành dấu - (22-12-2025) để Flatpickr hiểu
            # 3. Nối lại bằng dấu phẩy (,)
            form.ngayTap.data = ",".join([d.replace('/', '-') for d in dates])
            # Kết quả: "22-12-2025,24-12-2025"
        else:
            form.ngayTap.data = ""

    return render_template('HuanLuyenVien/sua_lich.html',
                           form=form,
                           lich=lich,
                           goi_y_list=goi_y_list,
                           data_map=data_map)

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
