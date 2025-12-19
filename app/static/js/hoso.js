document.addEventListener("DOMContentLoaded", function() {
    // 1. Khởi tạo Tooltip của Bootstrap (cho nút upload ảnh)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Tự động tắt thông báo (Alert) sau 1 giây (1000ms)
    var alerts = document.querySelectorAll('.alert');
    if (alerts) {
        alerts.forEach(function(alert) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 1000);
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const avatarInput = document.getElementById('avatar-upload');
    const avatarContainer = document.getElementById('avatar-container');

    if (avatarInput) {

      avatarInput.addEventListener('change', async function () {
        const f = this.files[0];
        if (!f) return;
        const fd = new FormData();
        fd.append('file', f);

        // Lấy URL từ thuộc tính data-url trong HTML
        const uploadUrl = this.dataset.url;

        try {
          const res = await fetch(uploadUrl, { // Sử dụng biến uploadUrl thay vì {{ url_for... }}
            method: 'POST',
            body: fd,
          });
          const json = await res.json();
          if (json.success && json.image_url) {
            // Cập nhật ảnh hiển thị ngay lập tức
            const img = avatarContainer.querySelector('img');
            if (img) img.setAttribute('src', json.image_url);

            location.reload();
          } else {
            alert(json.error || 'Upload thất bại');
          }
        } catch (e) {
          console.error(e);
          alert('Lỗi khi upload avatar');
        }
      });
    }
});