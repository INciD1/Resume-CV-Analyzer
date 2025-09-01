document.documentElement.lang = 'th';
document.documentElement.style.fontFamily = "'Sarabun', 'Noto Sans Thai', sans-serif";

// เพิ่ม Thai font
if (!document.querySelector('link[href*="Sarabun"]')) {
    const thaiFont = document.createElement('link');
    thaiFont.rel = 'stylesheet';
    thaiFont.href = 'https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap';
    document.head.appendChild(thaiFont);
}

document.addEventListener('DOMContentLoaded', function() {
    // ดึง session_id จาก URL
    const urlParts = window.location.pathname.split('/');
    const sessionId = urlParts[urlParts.length - 1];
    
    // อ้างอิง DOM elements
    const barChartContainer = document.getElementById('bar-chart-container').parentNode;
    const heatmapContainer = document.getElementById('heatmap-container');
    
    // สร้าง element ใหม่สำหรับการแสดงผลการจัดอันดับ
    const rankingContainer = document.createElement('div');
    rankingContainer.id = 'ranking-visualization';
    rankingContainer.className = 'chart-container p-4';
    barChartContainer.parentNode.replaceChild(rankingContainer, barChartContainer);
    
    // แสดง loading spinner
    rankingContainer.innerHTML = `
        <div class="loading-container">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">กำลังโหลด...</span>
            </div>
            <p class="mt-2">กำลังโหลดข้อมูล...</p>
        </div>
    `;
    
    // ดึงข้อมูลจาก API
    fetch(`/api/chart_data/${sessionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received chart data:', data);
            
            if (data && data.bar_chart) {
                createRankingVisualization(data.bar_chart);
            } else {
                console.warn('ไม่พบข้อมูลสำหรับการจัดอันดับ');
                document.getElementById('ranking-visualization').innerHTML = 
                    '<div class="alert alert-warning">ไม่พบข้อมูลสำหรับการจัดอันดับ</div>';
            }
            
            if (data && data.heatmap) {
                createHeatmap(data.heatmap);
            } else {
                console.warn('ไม่พบข้อมูลสำหรับ heatmap');
                heatmapContainer.innerHTML = '<div class="alert alert-warning">ไม่พบข้อมูลสำหรับการแสดงผลทักษะ</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            document.getElementById('ranking-visualization').innerHTML = 
                `<div class="alert alert-danger">เกิดข้อผิดพลาดในการโหลดข้อมูล: ${error.message}</div>`;
        });
        
        function createRankingVisualization(data) {
            if (!data.labels || !data.datasets || !Array.isArray(data.labels) || !Array.isArray(data.datasets)) {
                console.error('ข้อมูลการจัดอันดับไม่ถูกต้อง:', data);
                return;
            }
            
            try {
                // แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสม
                let candidatesData = [];
                const names = data.labels;
                
                for (let i = 0; i < names.length; i++) {
                    const skillScore = data.datasets[0].data[i] * 100; // ทักษะ
                    const contentScore = data.datasets[1].data[i] * 100; // เนื้อหา
                    const totalScore = data.datasets[2].data[i] * 100; // คะแนนรวม
                    
                    candidatesData.push({
                        name: names[i],
                        skillScore: skillScore,
                        contentScore: contentScore,
                        totalScore: totalScore
                    });
                }
                
                // เรียงลำดับตามคะแนนรวมจากมากไปน้อย
                candidatesData.sort((a, b) => b.totalScore - a.totalScore);
                
                // สร้าง HTML สำหรับแสดงผลการจัดอันดับ
                let html = `
                    <div class="ranking-header">
                        <h4 class="mb-3">การจัดอันดับผู้สมัคร</h4>
                        <div class="legend-container">
                            <div class="legend-item">
                                <div class="legend-color skill-color"></div>
                                <span>คะแนนทักษะ</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color content-color"></div>
                                <span>คะแนนเนื้อหา</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color total-color"></div>
                                <span>คะแนนรวม</span>
                            </div>
                        </div>
                        <div class="scroll-instruction">
                            <i class="fas fa-mouse"></i>
                            <span>เลื่อน mouse เพื่อดูอันดับทั้งหมด</span>
                        </div>
                    </div>
                    <div class="ranking-body-wrapper">
                        <div class="ranking-body">
                `;
                
                // สร้าง HTML สำหรับแต่ละคน
                candidatesData.forEach((candidate, index) => {
                    const rank = index + 1;
                    // กำหนดสีตามอันดับ
                    let medalClass = 'badge-normal';
                    let medalIcon = '';
                    
                    if (rank === 1) {
                        medalClass = 'badge-gold';
                        medalIcon = '<i class="fas fa-trophy"></i>';
                    } else if (rank === 2) {
                        medalClass = 'badge-silver';
                        medalIcon = '<i class="fas fa-medal"></i>';
                    } else if (rank === 3) {
                        medalClass = 'badge-bronze';
                        medalIcon = '<i class="fas fa-award"></i>';
                    }
                    
                    // สร้าง Short Name สำหรับการแสดงผลบนมือถือ
                    const shortName = candidate.name.length > 15 
                        ? candidate.name.substring(0, 15) + '...' 
                        : candidate.name;
                    
                    html += `
                            <div class="ranking-item ${index === 0 ? 'top-rank' : ''} mb-4" data-rank="${rank}">
                            <div class="d-flex align-items-center mb-3">
                                <div class="rank-badge ${medalClass} me-3">
                                    ${medalIcon} ${rank}
                                </div>
                                <div class="candidate-name flex-grow-1">
                                    <h5 class="mb-0 full-name">${candidate.name}</h5>
                                    <h5 class="mb-0 short-name">${shortName}</h5>
                                </div>
                                <div class="total-score-display">
                                    <span class="fw-bold">${candidate.totalScore.toFixed(1)}%</span>
                                </div>
                            </div>
                            
                            <div class="scores-container">
                                <div class="score-label">ทักษะ</div>
                                <div class="progress skill-progress" style="height: 25px; margin-bottom: 15px;">
                                    <div class="progress-bar skill-bar" role="progressbar" 
                                        style="width: ${candidate.skillScore}%;" 
                                        aria-valuenow="${candidate.skillScore}" aria-valuemin="0" aria-valuemax="100"
                                        data-bs-toggle="tooltip" title="คะแนนทักษะ: ${candidate.skillScore.toFixed(1)}%">
                                        <span class="progress-label">${candidate.skillScore.toFixed(1)}%</span>
                                    </div>
                                </div>
                                <div class="score-label">เนื้อหา</div>
                                <div class="progress content-progress" style="height: 25px; margin-bottom: 15px;">
                                    <div class="progress-bar content-bar" role="progressbar" 
                                        style="width: ${candidate.contentScore}%;" 
                                        aria-valuenow="${candidate.contentScore}" aria-valuemin="0" aria-valuemax="100"
                                        data-bs-toggle="tooltip" title="คะแนนเนื้อหา: ${candidate.contentScore.toFixed(1)}%">
                                        <span class="progress-label">${candidate.contentScore.toFixed(1)}%</span>
                                    </div>
                                </div>
                                
                                <div class="score-label">คะแนนรวม</div>
                                <div class="progress total-progress" style="height: 30px; margin-bottom: 15px;">
                                    <div class="progress-bar total-bar ${medalClass.replace('badge-', 'bar-')}" role="progressbar" 
                                        style="width: ${candidate.totalScore}%;" 
                                        aria-valuenow="${candidate.totalScore}" aria-valuemin="0" aria-valuemax="100"
                                        data-bs-toggle="tooltip" title="คะแนนรวม: ${candidate.totalScore.toFixed(1)}%">
                                        <span class="progress-label">${candidate.totalScore.toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                    <div class="scroll-controls">
                        <button class="btn btn-outline-primary scroll-up-btn" title="เลื่อนขึ้น">
                            <i class="fas fa-chevron-up"></i>
                        </button>
                        <button class="btn btn-outline-primary scroll-down-btn" title="เลื่อนลง">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </div>
                `;
                
                // แสดงผลการจัดอันดับ
                document.getElementById('ranking-visualization').innerHTML = html;
                
                // เปิดใช้งาน tooltips (ต้องมี Bootstrap 5)
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
                
                // เพิ่ม animation เมื่อโหลดเสร็จ
                setTimeout(() => {
                    const items = document.querySelectorAll('.ranking-item');
                    items.forEach((item, index) => {
                        setTimeout(() => {
                            item.classList.add('show');
                        }, index * 150);
                    });
                }, 300);
                
                // เพิ่มการรองรับ mouse scroll
                const rankingBody = document.querySelector('.ranking-body-wrapper');
                if (rankingBody) {
                    // ตรวจจับ event เมื่อเลื่อน mouse
                    rankingBody.addEventListener('wheel', function(e) {
                        e.preventDefault();
                        
                        // ปรับความเร็วในการเลื่อน
                        const scrollSpeed = 40;
                        this.scrollTop += (e.deltaY > 0) ? scrollSpeed : -scrollSpeed;
                    });
                    
                    // เพิ่มการรองรับปุ่มเลื่อนขึ้น/ลง
                    const scrollUpBtn = document.querySelector('.scroll-up-btn');
                    const scrollDownBtn = document.querySelector('.scroll-down-btn');
                    
                    if (scrollUpBtn && scrollDownBtn) {
                        scrollUpBtn.addEventListener('click', function() {
                            rankingBody.scrollTop -= 100;
                        });
                        
                        scrollDownBtn.addEventListener('click', function() {
                            rankingBody.scrollTop += 100;
                        });
                    }
                    
                    // เพิ่ม scroll indicator เมื่อมีเนื้อหามากเกินกว่าจะแสดงทั้งหมด
                    const checkScrollIndicator = function() {
                        const hasOverflow = rankingBody.scrollHeight > rankingBody.clientHeight;
                        const scrollControls = document.querySelector('.scroll-controls');
                        const scrollInstruction = document.querySelector('.scroll-instruction');
                        
                        if (scrollControls) {
                            scrollControls.style.display = hasOverflow ? 'flex' : 'none';
                        }
                        
                        if (scrollInstruction) {
                            scrollInstruction.style.display = hasOverflow ? 'flex' : 'none';
                        }
                    };
                    
                    // ตรวจสอบเมื่อโหลดเสร็จและเมื่อขนาดหน้าจอเปลี่ยน
                    setTimeout(checkScrollIndicator, 500);
                    window.addEventListener('resize', checkScrollIndicator);
                }
                
                console.log('สร้างการแสดงผลการจัดอันดับสำเร็จ');
            } catch (error) {
                console.error('เกิดข้อผิดพลาดในการสร้างการแสดงผลการจัดอันดับ:', error);
                document.getElementById('ranking-visualization').innerHTML = 
                    `<div class="alert alert-danger">เกิดข้อผิดพลาดในการแสดงผลการจัดอันดับ: ${error.message}</div>`;
            }
        }
    
    // ปรับปรุงฟังก์ชัน createHeatmap
    function createHeatmap(data) {
        // ตรวจสอบความถูกต้องของข้อมูล
        if (!data.data || !data.labels || !data.labels.x || !data.labels.y) {
            console.error('ข้อมูล heatmap ไม่ถูกต้อง:', data);
            return;
        }
    
        try {
            // จำกัดขนาดของชื่อทักษะ (แกน x) เพื่อให้แสดงผลได้ดีขึ้นบนมือถือ
            let xLabels = data.labels.x.map(label => {
                if (label.length > 10) {
                    return label.substring(0, 10) + '...';
                }
                return label;
            });
            
            // จำกัดขนาดของชื่อผู้สมัคร (แกน y) เพื่อให้แสดงผลได้ดีขึ้นบนมือถือ
            let yLabels = data.labels.y.map(label => {
                if (label.length > 12) {
                    return label.substring(0, 12) + '...';
                }
                return label;
            });
            
            // สร้างข้อมูลเต็มสำหรับ tooltip
            let fullXLabels = data.labels.x;
            let fullYLabels = data.labels.y;
            
            // สร้าง annotation สำหรับจุดที่มีค่าเป็น 1
            let annotations = [];
            for(let i = 0; i < data.data.length; i++) {
                for(let j = 0; j < data.data[i].length; j++) {
                    if(data.data[i][j] === 1) {
                        annotations.push({
                            x: xLabels[j],
                            y: yLabels[i],
                            text: '✓',
                            showarrow: false,
                            font: {
                                color: 'white',
                                size: 18
                            }
                        });
                    }
                }
            }
            
            var heatmapData = [{
                z: data.data,
                x: xLabels,
                y: yLabels,
                type: 'heatmap',
                colorscale: [
                    [0, 'rgb(240, 240, 245)'],  // ไม่มีทักษะ - สีอ่อน
                    [1, 'rgb(25, 118, 210)']    // มีทักษะ - สีเข้ม
                ],
                showscale: true,
                colorbar: {
                    title: 'ทักษะ',
                    tickvals: [0, 1],
                    ticktext: ['ไม่มี', 'มี']
                },
                hoverinfo: 'text',
                text: data.data.map(function(row, i) {
                    return row.map(function(val, j) {
                        return `ผู้สมัคร: ${fullYLabels[i]}<br>ทักษะ: ${fullXLabels[j]}<br>สถานะ: ${val === 1 ? 'มี' : 'ไม่มี'}`;
                    });
                })
            }];
    
            var layout = {
                title: {
                    text: 'การเปรียบเทียบทักษะของผู้สมัคร',
                    font: {
                        size: 20,
                        color: '#333'
                    }
                },
                xaxis: {
                    title: {
                        text: 'ทักษะที่ต้องการ',
                        font: {
                            size: 16,
                            color: '#333'
                        }
                    },
                    automargin: true,
                    tickangle: 45
                },
                yaxis: {
                    title: {
                        text: 'ผู้สมัคร',
                        font: {
                            size: 16,
                            color: '#333'
                        }
                    },
                    automargin: true
                },
                margin: {
                    l: 120, // ลดขนาดลงจากเดิม (150)
                    r: 50,  // ลดขนาดลงจากเดิม (80)
                    b: 120, // ลดขนาดลงจากเดิม (150)
                    t: 80,
                    pad: 5
                },
                annotations: annotations,
                autosize: true,
                height: window.innerWidth < 768 ? 450 : 550, // ปรับขนาดตามหน้าจอ
                font: {
                    family: 'Arial, sans-serif',
                    size: 14
                },
            };
    
            var config = {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                displaylogo: false
            };
            
            Plotly.newPlot('heatmap-container', heatmapData, layout, config);
            
            // รีไซส์เมื่อหน้าจอเปลี่ยนขนาด
            window.addEventListener('resize', function() {
                Plotly.relayout('heatmap-container', {
                    height: window.innerWidth < 768 ? 450 : 550
                });
            });
            
            // เพิ่มคำอธิบายเพิ่มเติม
            const infoDiv = document.createElement('div');
            infoDiv.className = 'heatmap-info mt-3';
            infoDiv.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">คำอธิบายแผนภูมิ</h6>
                        <p class="card-text">แผนภูมินี้แสดงทักษะของผู้สมัครแต่ละคนเทียบกับทักษะที่ต้องการ โดย:</p>
                        <div class="d-flex align-items-center mb-2">
                            <div class="heatmap-legend-color me-2" style="background-color: rgb(25, 118, 210);"></div>
                            <span>หมายถึง ผู้สมัครมีทักษะนี้ (✓)</span>
                        </div>
                        <div class="d-flex align-items-center">
                            <div class="heatmap-legend-color me-2" style="background-color: rgb(240, 240, 245);"></div>
                            <span>หมายถึง ผู้สมัครไม่มีทักษะนี้</span>
                        </div>
                    </div>
                </div>
            `;
            heatmapContainer.parentNode.insertBefore(infoDiv, heatmapContainer.nextSibling);
        } catch (error) {
            console.error('เกิดข้อผิดพลาดในการสร้าง heatmap:', error);
            heatmapContainer.innerHTML = `<div class="alert alert-danger">เกิดข้อผิดพลาดในการแสดงผลทักษะ: ${error.message}</div>`;
        }
    }
});

// เพิ่ม CSS ในหน้า
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent += `
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
        }
        
        .ranking-header {
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #dee2e6;
            text-align: center;
        }
        
        .legend-container {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
            justify-content: center;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .legend-color {
            width: 18px;
            height: 18px;
            border-radius: 4px;
        }
        
        .skill-color {
            background-color: #4285F4;
        }
        
        .content-color {
            background-color: #34A853;
        }
        
        .total-color {
            background-color: #333;
        }
        
        .ranking-item {
            background-color: #fff;
            padding: 22px;
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border-left: 5px solid #ddd;
            opacity: 1; /* เปลี่ยนจาก 0 เป็น 1 เพื่อให้แสดงทันที */
            transform: translateY(0);
            margin-bottom: 20px;
        }
        
        .ranking-item.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .ranking-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .top-rank {
            border-left: 5px solid #ffc107;
        }
        
        .rank-badge {
            min-width: 45px;
            height: 45px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 1.25rem;
            box-shadow: 0 3px 6px rgba(0,0,0,0.16);
        }
        
        .badge-gold {
            background: linear-gradient(135deg, #ffd700, #e6bc00);
        }
        
        .badge-silver {
            background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
        }
        
        .badge-bronze {
            background: linear-gradient(135deg, #cd7f32, #a05a2c);
        }
        
        .badge-normal {
            background: linear-gradient(135deg, #6c757d, #495057);
        }
        
        .bar-gold {
            background: linear-gradient(135deg, #ffd700, #e6bc00);
        }
        
        .bar-silver {
            background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
        }
        
        .bar-bronze {
            background: linear-gradient(135deg, #cd7f32, #a05a2c);
        }
        
        .bar-normal {
            background: #6c757d;
        }
        
        .total-score-display {
            background-color: #f8f9fa;
            padding: 8px 12px;
            border-radius: 30px;
            font-size: 1rem;
            border: 1px solid #e9ecef;
            white-space: nowrap;
        }
        
        .scores-container {
            margin-top: 5px;
        }
        
        .score-label {
            font-weight: 500;
            margin-bottom: 4px;
            color: #495057;
        }
        
        .progress {
            margin-bottom: 15px;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            background-color: #e9ecef;
        }
        
        .progress-label {
            margin-left: 10px;
            font-weight: 600;
            text-shadow: 0 0 2px rgba(0,0,0,0.5);
            font-size: 14px;
        }
        
        .skill-bar {
            background-color: #4285F4;
        }
    
        .content-bar {
            background-color: #34A853;
        }
    
        .total-bar {
            background-color: #333;
        }
        
        .chart-container {
            width: 100%;
            min-height: 500px;
            margin-bottom: 30px;
            background-color: #fff;
            border: 1px solid #eaeaea;
            border-radius: 10px;
            position: relative;
            padding: 25px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.04);
            overflow: hidden;
        }
        
        .heatmap-info {
            margin-bottom: 30px;
        }
        
        .heatmap-legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        
        .full-name {
            display: block;
        }
        
        .short-name {
            display: none;
        }
        
        /* สำหรับหน้าจอขนาดกลาง */
        @media (max-width: 991px) {
            .chart-container {
                padding: 20px;
            }
            
            .rank-badge {
                min-width: 40px;
                height: 40px;
                font-size: 1.1rem;
            }
            
            .total-score-display {
                padding: 6px 10px;
                font-size: 0.9rem;
            }
            
            .progress-label {
                font-size: 12px;
            }
        }
        
        .ranking-body-wrapper {
            max-height: 200px;
            overflow-y: auto;
            padding-right: 10px; /* เพิ่มระยะห่างเล็กน้อย */
            scrollbar-width: thin;
            scrollbar-color: #c1c1c1 #f1f1f1;
            position: relative;
            overscroll-behavior: contain; /* ป้องกันการเลื่อนหน้าเมื่อเลื่อนดูข้อมูลถึงสุด */
            scroll-behavior: smooth; /* ทำให้การเลื่อนดูเรียบขึ้น */
        }
        
        /* ปรับแต่ง scrollbar สำหรับ Chrome, Edge, Safari */
        .ranking-body-wrapper::-webkit-scrollbar {
            width: 8px;
        }
        
        .ranking-body-wrapper::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .ranking-body-wrapper::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 10px;
        }
        
        .ranking-body-wrapper::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        
        .scroll-instruction {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 12px;
            background-color: #e9f0ff;
            border-radius: 6px;
            margin: 15px auto;
            max-width: 350px;
            color: #0d6efd;
            font-size: 1rem;
            border: 1px solid #0d6efd;
            font-weight: 500;
        }
        
        .scroll-instruction i {
            font-size: 1.1rem;
            color: #0d6efd;
        }
        
        .scroll-controls {
            display: flex;
            flex-direction: column;
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            gap: 10px;
            z-index: 100;
        }
        
        .scroll-controls button {
            width: 45px;
            height: 45px;
            padding: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            box-shadow: 0 3px 8px rgba(0,0,0,0.15);
            background-color: white;
            border: 2px solid #0d6efd;
            transition: all 0.5s ease;
        }
        
        .scroll-controls button:hover {
            background-color: #f8f9fa;
        }
        
        /* สำหรับหน้าจอขนาดเล็ก */
        @media (max-width: 768px) {
            .ranking-body-wrapper {
                max-height: 500px;
            }
            
            .scroll-controls {
                right: 10px;
            }
            
            .scroll-controls button {
                width: 35px;
                height: 35px;
                padding: 6px;
            }
            
            .scroll-instruction {
                font-size: 0.8rem;
                padding: 8px;
            }
            
            .ranking-item {
                padding: 15px;
            }
            
            .legend-container {
                gap: 10px;
            }
            
            .rank-badge {
                min-width: 35px;
                height: 35px;
                font-size: 1rem;
            }
            
            .total-score-display {
                padding: 4px 8px;
                font-size: 0.85rem;
            }
            
            .progress {
                height: 20px !important;
            }
            
            .total-progress {
                height: 25px !important;
            }
            
            .progress-label {
                font-size: 11px;
                margin-left: 5px;
            }
            
            .full-name {
                display: none;
            }
            
            .short-name {
                display: block;
            }
        }
        
        /* สำหรับหน้าจอขนาดเล็กมาก */
        @media (max-width: 480px) {
            .chart-container {
                min-height: 350px;
                padding: 10px;
            }
            
            .ranking-item {
                padding: 12px;
            }
            
            .rank-badge {
                min-width: 30px;
                height: 30px;
                font-size: 0.9rem;
            }
            
            .candidate-name h5 {
                font-size: 1rem;
            }
            
            .total-score-display {
                padding: 3px 6px;
                font-size: 0.8rem;
            }
            
            .score-label {
                font-size: 0.9rem;
            }
            
            .progress-bar span {
                font-size: 10px;
            }
        }
    `;
    document.head.appendChild(style);
    
    // เพิ่ม Font Awesome สำหรับไอคอน (ถ้ายังไม่มี)
    if (!document.querySelector('link[href*="font-awesome"]')) {
        const fontAwesome = document.createElement('link');
        fontAwesome.rel = 'stylesheet';
        fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
        document.head.appendChild(fontAwesome);
    }
});