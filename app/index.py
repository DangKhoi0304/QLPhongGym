from random import choice

from flask import render_template, request, redirect, session, flash, url_for, jsonify
from app import app, db, dao, login
from datetime import timedelta, datetime
from app.models import UserRole, NhanVien, GoiTap, DangKyGoiTap
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import RegisterForm, StaffRegisterForm, RegisterFormStaff, ChangeInfoForm, ChangePasswordForm, TaoLichTapForm, ChonHLVForm, SuaLichTapForm
from app.utils_mail import send_mail_gmail

from uuid import uuid4
from werkzeug.utils import secure_filename
import re
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


@app.route('/chon-hlv', methods=['GET', 'POST'])
@login_required
def choose_pt():
    # ... (giữ nguyên logic kiểm tra gói tập active) ...
    active_package = dao.get_active_package_by_user_id(current_user.id)
    if not active_package:
        return redirect('/') # hoặc thông báo lỗi

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
    if not getattr(current_user, 'huanluyenvien', None):
        return redirect('/')

    form = TaoLichTapForm()

    if form.validate_on_submit():
        baiTap = form.baiTap.data
        soHiep = form.soHiep.data
        soLan = form.soLan.data

        # --- XỬ LÝ NGÀY TỪ LỊCH ---
        # Dữ liệu nhận được dạng: "2025-12-15, 2025-12-17"
        raw_dates_str = form.ngayTap.data

        formatted_list = []
        if raw_dates_str:
            # Tách chuỗi thành list các ngày
            raw_list = [d.strip() for d in raw_dates_str.split(',') if d.strip()]

            for d_str in raw_list:
                try:
                    # 1. Chuyển chuỗi thành đối tượng ngày giờ
                    date_obj = datetime.strptime(d_str, '%d-%m-%Y')  # Flatpickr trả về dd-mm-yyyy

                    # 2. Tìm thứ tiếng Việt (0=Thứ 2, 6=CN)
                    days_map = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ Nhật']
                    day_name = days_map[date_obj.weekday()]

                    # 3. Tạo chuỗi đẹp: "Thứ 2 (15/12/2025)"
                    formatted_item = f"{day_name} ({date_obj.strftime('%d/%m/%Y')})"
                    formatted_list.append(formatted_item)
                except ValueError:
                    continue

                    # Nối lại thành chuỗi để lưu Database
        final_ngay_tap = ", ".join(formatted_list)

        if dao.add_schedule(dangky_id, baiTap, soHiep, soLan, final_ngay_tap):
            flash("Đã thêm bài tập thành công!", "success")
            return redirect(url_for('create_schedule', dangky_id=dangky_id))
        else:
            flash("Lỗi khi thêm lịch.", "danger")

    current_schedule = dao.get_schedule_by_dangky(dangky_id)
    dk = DangKyGoiTap.query.get(dangky_id)

    return render_template('HuanLuyenVien/tao_lich.html',
                           form=form,
                           schedule=current_schedule,
                           member=dk.hoi_vien,
                           dangky_id=dangky_id)

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
    if not lich:
        return redirect('/')

    form = SuaLichTapForm()

    # --- XỬ LÝ POST: KHI BẤM LƯU ---
    if form.validate_on_submit():
        # Dữ liệu từ Flatpickr gửi lên sẽ là: "15-12-2025, 19-12-2025" (Raw date)
        raw_dates_str = form.ngayTap.data

        # Chúng ta cần format lại thành "Thứ 2 (15/12/2025)..." cho đẹp
        formatted_list = []
        if raw_dates_str:
            # Tách chuỗi dựa trên dấu phẩy hoặc khoảng trắng
            raw_list = [d.strip() for d in raw_dates_str.split(',') if d.strip()]

            for d_str in raw_list:
                try:
                    # Chuyển từ string "15-12-2025" sang đối tượng Date
                    date_obj = datetime.strptime(d_str, '%d-%m-%Y')

                    # Lấy tên thứ tiếng Việt
                    weekday_index = date_obj.weekday()  # 0=Thứ 2, 6=CN
                    days_map = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ Nhật']
                    day_name = days_map[weekday_index]

                    # Tạo chuỗi đẹp: "Thứ 2 (15/12/2025)"
                    formatted_item = f"{day_name} ({date_obj.strftime('%d/%m/%Y')})"
                    formatted_list.append(formatted_item)
                except ValueError:
                    continue  # Bỏ qua nếu lỗi định dạng

        # Nối lại thành chuỗi dài để lưu DB
        final_ngay_tap = ", ".join(formatted_list)

        if dao.update_schedule(id, form.baiTap.data, form.soHiep.data, form.soLan.data, final_ngay_tap):
            flash("Cập nhật thành công!", "success")
            return redirect(url_for('create_schedule', dangky_id=lich.dangKyGoiTap_id))
        else:
            flash("Lỗi cập nhật.", "danger")

    # --- XỬ LÝ GET: KHI MỞ FORM ---
    if request.method == 'GET':
        form.baiTap.data = lich.baiTap
        form.soHiep.data = lich.soHiep
        form.soLan.data = lich.soLan

        # Xử lý ngược: Trích xuất ngày từ chuỗi đẹp "Thứ 2 (15/12/2025)" -> "15-12-2025"
        # Dùng Regex để tìm pattern ngày tháng dd/mm/yyyy
        if lich.ngayTap:
            dates = re.findall(r'\d{2}/\d{2}/\d{4}', lich.ngayTap)
            # Chuyển dấu / thành dấu - để Flatpickr hiểu (15/12/2025 -> 15-12-2025)
            dates_formatted = [d.replace('/', '-') for d in dates]
            # Gán vào form để hiển thị lên lịch
            form.ngayTap.data = ", ".join(dates_formatted)
        else:
            form.ngayTap.data = ""

    return render_template('HuanLuyenVien/sua_lich.html', form=form, lich=lich)

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
