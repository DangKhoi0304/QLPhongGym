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