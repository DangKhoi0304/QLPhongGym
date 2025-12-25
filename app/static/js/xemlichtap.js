   document.addEventListener("DOMContentLoaded", function() {
        const accordionContainer = document.getElementById('scheduleAccordion');
        const loadingState = document.getElementById('loadingState');

        if (!accordionContainer || rawSchedule.length === 0) return;

        const organizedData = {};

        function getWeekNumber(d) {
            d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
            d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay()||7));
            var yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
            var weekNo = Math.ceil(( ( (d - yearStart) / 86400000) + 1)/7);
            return { year: d.getUTCFullYear(), week: weekNo };
        }

        rawSchedule.forEach(item => {

            const dates = item.ngayTapStr.match(/\d{2}\/\d{2}\/\d{4}/g);

            if (dates) {
                dates.forEach(dateStr => {

                    const parts = dateStr.split('/');
                    const day = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1;
                    const year = parseInt(parts[2], 10);

                    const dateObj = new Date(year, month, day);
                    const weekInfo = getWeekNumber(dateObj);

                    const weekKey = `Tuần ${weekInfo.week} - Năm ${weekInfo.year}`;

                    const daysMap = ['Chủ Nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
                    const dayKey = `${daysMap[dateObj.getDay()]} (${dateStr})`;

                    if (!organizedData[weekKey]) organizedData[weekKey] = {};
                    if (!organizedData[weekKey][dayKey]) organizedData[weekKey][dayKey] = [];

                    organizedData[weekKey][dayKey].push(item);
                });
            }
        });

        loadingState.style.display = 'none';

        const sortedWeeks = Object.keys(organizedData).sort((a, b) => {

             const matchA = a.match(/Tuần (\d+) - Năm (\d+)/);
             const matchB = b.match(/Tuần (\d+) - Năm (\d+)/);
             if (matchA && matchB) {
                 if (matchA[2] !== matchB[2]) return matchA[2] - matchB[2];
                 return matchA[1] - matchB[1];
             }
             return 0;
        });

        if (sortedWeeks.length === 0) {
            accordionContainer.innerHTML = '<div class="text-center p-3">Không phân tích được dữ liệu ngày tháng.</div>';
            return;
        }

        sortedWeeks.forEach((weekKey, index) => {
            const collapseId = `collapse${index}`;
            const headerId = `heading${index}`;

            const showClass = index === sortedWeeks.length - 1 ? 'show' : '';
            const btnCollapsed = index === sortedWeeks.length - 1 ? '' : 'collapsed';

            let weekHtml = `
                <div class="accordion-item border-0 mb-3 shadow-sm rounded overflow-hidden">
                    <h2 class="accordion-header" id="${headerId}">
                        <button class="accordion-button ${btnCollapsed}" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}">
                            <i class="bi bi-calendar-check me-2"></i> ${weekKey}
                        </button>
                    </h2>
                    <div id="${collapseId}" class="accordion-collapse collapse ${showClass}" data-bs-parent="#scheduleAccordion">
                        <div class="accordion-body bg-light">
            `;

            const daysInWeek = organizedData[weekKey];
            const sortedDays = Object.keys(daysInWeek).sort((a, b) => {

                const getTs = (s) => {
                    const dParts = s.match(/\d{2}\/\d{2}\/\d{4}/)[0].split('/');
                    return new Date(dParts[2], dParts[1]-1, dParts[0]).getTime();
                };
                return getTs(a) - getTs(b);
            });

            sortedDays.forEach(dayKey => {
                const exercises = daysInWeek[dayKey];
                weekHtml += `
                    <div class="day-card rounded">
                        <div class="day-header rounded-top d-flex justify-content-between">
                            <span>${dayKey}</span>
                            <span class="badge bg-primary rounded-pill">${exercises.length} bài</span>
                        </div>
                        <div class="p-0">
                `;

                exercises.forEach(ex => {
                    weekHtml += `
                        <div class="exercise-item d-flex justify-content-between align-items-center bg-white">
                            <div>
                                <div class="fw-bold text-dark">${ex.baiTap}</div>
                                <div class="small text-muted"><i class="bi bi-tag me-1"></i>${ex.nhomCo}</div>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-light text-dark border me-1">Hiệp: ${ex.soHiep}</span>
                                <span class="badge bg-light text-dark border">Lần: ${ex.soLan}</span>
                            </div>
                        </div>
                    `;
                });

                weekHtml += `</div></div>`;
            });

            weekHtml += `
                        </div>
                    </div>
                </div>
            `;
            accordionContainer.innerHTML += weekHtml;
        });
    });


  