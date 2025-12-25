
    const rawDateStr = "{{ form.ngayTap.data }}";

    let defaultDates = [];
    if (rawDateStr && rawDateStr !== "None" && rawDateStr !== "") {

        defaultDates = rawDateStr.split(',').map(d => d.trim());
    }

    flatpickr("#datepicker_edit", {
        mode: "multiple",
        dateFormat: "d-m-Y",
        locale: "vn",
        minDate: "today",


        defaultDate: defaultDates
    });


    const exerciseMap = {{ data_map | tojson }};
    const inputBaiTap = document.getElementById('input_bai_tap');
    const inputNhomCo = document.getElementById('input_nhom_co');
    const msgStatus = document.getElementById('msg_status');

    function checkBaiTap() {
        const tenBai = inputBaiTap.value;
        if (exerciseMap && exerciseMap[tenBai]) {
            inputNhomCo.value = exerciseMap[tenBai];
            inputNhomCo.readOnly = true;
            inputNhomCo.classList.add('bg-light');
            inputNhomCo.classList.remove('bg-white');
            msgStatus.innerHTML = '<i class="fas fa-check-circle text-success me-1"></i>Đã lấy từ dữ liệu hệ thống.';
            msgStatus.className = "mt-1 small text-success";
        } else {
            if (tenBai.trim() !== "") {
                inputNhomCo.readOnly = false;
                inputNhomCo.classList.remove('bg-light');
                inputNhomCo.classList.add('bg-white');
                msgStatus.innerHTML = '<i class="fas fa-pen text-warning me-1"></i>Vui lòng tự nhập nhóm cơ.';
                msgStatus.className = "mt-1 small text-warning fw-bold";
            } else {
                inputNhomCo.value = "";
                inputNhomCo.readOnly = true;
                msgStatus.innerHTML = "";
            }
        }
    }

    inputBaiTap.addEventListener('input', checkBaiTap);
    inputBaiTap.addEventListener('change', checkBaiTap);

    document.addEventListener("DOMContentLoaded", function() {
        checkBaiTap();

        if (!inputNhomCo.readOnly && inputNhomCo.value === "") {
             inputNhomCo.value = "{{ lich.nhom_co }}";
        }
    });