document.addEventListener('DOMContentLoaded', function() {
    const avatarUploadInput = document.getElementById('avatar-upload');

    if (avatarUploadInput) {
        avatarUploadInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;

            const avatarContainer = document.getElementById('avatar-container');

            if (avatarContainer) avatarContainer.style.opacity = '0.5';

            const formData = new FormData();
            formData.append('file', file);

            fetch('/api/upload-avatar', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (avatarContainer) avatarContainer.style.opacity = '1';

                if (data.success) {
                    avatarContainer.innerHTML = '';

                    const newImg = document.createElement('img');
                    newImg.src = data.image_url;
                    newImg.className = 'w-100 rounded-circle object-fit-cover animate__animated animate__fadeIn'; // Thêm class animation nếu muốn
                    newImg.alt = 'Avatar';

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

function viewHistory(userId, userName) {
        document.getElementById('histUserName').innerText = userName;
        const myModal = new bootstrap.Modal(document.getElementById('modalHistory'));
        myModal.show();

        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = '';
        document.getElementById('loadingHist').classList.remove('d-none');
        document.getElementById('emptyHist').classList.add('d-none');

        fetch(`/api/payment-history/${userId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('loadingHist').classList.add('d-none');

                if (data.length === 0) {
                    document.getElementById('emptyHist').classList.remove('d-none');
                } else {

                    data.forEach(item => {
                        const row = `
                            <tr>
                                <td class="ps-4 fw-bold text-secondary">${item.ngay}</td>
                                <td><span class="badge bg-info text-dark">${item.goi || 'N/A'}</span></td>
                                <td>${item.phuong_thuc}</td>
                                <td class="text-end pe-4 fw-bold text-success">${item.tien} đ</td>
                            </tr>
                        `;
                        tbody.innerHTML += row;
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Lỗi tải dữ liệu!</td></tr>';
                document.getElementById('loadingHist').classList.add('d-none');
            });
    }

function setupPayment(userId, userName) {
        const idField = document.getElementById('user_id_field') || document.getElementById('user_id');
        if(idField) {
            idField.value = userId;
        }
        document.getElementById('payUserName').innerText = userName;
    }
    let currentDebt = 0;

    function setupDebt(dangKyGoiTap_id, userName, debtAmount) {

        document.getElementById('debtUserName').innerText = userName;
        document.getElementById('debtAmountDisplay').innerText = debtAmount.toLocaleString();

        const hiddenInput = document.querySelector('input[name="dangKyGoiTap_id"]');
        if(hiddenInput) {
            hiddenInput.value = dangKyGoiTap_id;
        }

        currentDebt = debtAmount;
        document.getElementById('inputDebtAmount').value = '';
    }

    function fillFullDebt() {
        document.getElementById('inputDebtAmount').value = currentDebt;
    }
