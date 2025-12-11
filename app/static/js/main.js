document.addEventListener('DOMContentLoaded', function() {
    // Lấy phần tử input file
    const avatarUploadInput = document.getElementById('avatar-upload');

    if (avatarUploadInput) {
        avatarUploadInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Lấy container chứa ảnh để xử lý hiệu ứng loading
            const avatarContainer = document.getElementById('avatar-container');

            // Hiệu ứng làm mờ để báo đang xử lý
            if (avatarContainer) avatarContainer.style.opacity = '0.5';

            // Chuẩn bị dữ liệu gửi đi
            const formData = new FormData();
            formData.append('file', file);

            // Gọi API upload
            fetch('/api/upload-avatar', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (avatarContainer) avatarContainer.style.opacity = '1';

                if (data.success) {
                    // 1. Xóa nội dung cũ (ảnh cũ hoặc chữ cái fallback)
                    avatarContainer.innerHTML = '';

                    // 2. Tạo thẻ img mới với link từ Cloudinary trả về
                    const newImg = document.createElement('img');
                    newImg.src = data.image_url;
                    newImg.className = 'w-100 rounded-circle object-fit-cover animate__animated animate__fadeIn'; // Thêm class animation nếu muốn
                    newImg.alt = 'Avatar';

                    // 3. Chèn ảnh mới vào khung
                    avatarContainer.appendChild(newImg);

                    console.log("Upload thành công:", data.image_url);
                } else {
                    alert("Lỗi: " + (data.error || "Không thể tải ảnh lên"));
                }
            })
            .catch(error => {
                if (avatarContainer) avatarContainer.style.opacity = '1';
                console.error('Error:', error);
                alert("Đã có lỗi xảy ra khi kết nối đến server.");
            });
        });
    }
});

let crr_goiTap_id = null;
let paymentModalObj = null;

function openPaymentModal(goiTap_id, tenGoi, giaTienGoi, thoiHan){
    crr_goiTap_id = goiTap_id;
    document.getElementById('modalTenGoi').innerText = tenGoi;
    document.getElementById('modalGiaTien').innerText = giaTienGoi.toLocaleString('vi-VN') + ' VNĐ';
    document.getElementById('modalThoiHan').innerText = thoiHan + ' Ngày';

    const today = new Date();
    const endDate = new Date();
    endDate.setDate(today.getDate() + thoiHan);
    document.getElementById('modalNgayBatDau').innerText = today.toLocaleDateString('vi-VN');
    document.getElementById('modalNgayKetThuc').innerText = endDate.toLocaleDateString('vi-VN');

    document.getElementById('step-confirm').style.display = 'block';
    document.getElementById('step-success').style.display = 'none';
    document.getElementById('step-error').style.display = 'none';

    const modalElement = document.getElementById('paymentModal');
    paymentModalObj = new bootstrap.Modal(modalElement);
    paymentModalObj.show();
}

function submitPayment() {
    if (!crr_goiTap_id) return;

    fetch('/api/buy_package', {
            method: 'POST',
            body: JSON.stringify({
                'goiTap_id': crr_goiTap_id
            }),
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.code === 200) {
               document.getElementById('step-confirm').style.display = 'none'; // Ẩn form
                document.getElementById('step-success').style.display = 'block'; // Hiện thông báo
            } else {
                document.getElementById('step-error').style.display = 'block';

                document.getElementById('errorMessage').innerText = data.msg;
            }
        })
        .catch(err => {
            console.error(err);
            alert("Hệ thống lỗi! Xem console để biết chi tiết.");
        });
}
