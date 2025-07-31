let censusChart, acuityChart, admissionChart;
let currentChartFilters = {};

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('date-range-filter').addEventListener('change', () => {
        currentChartFilters = {}; // Reset chart filters when dropdowns change
        fetchData();
    });
    document.getElementById('unit-filter').addEventListener('change', () => {
        currentChartFilters = {}; // Reset chart filters when dropdowns change
        fetchData();
    });
    document.getElementById('reset-filters-btn').addEventListener('click', () => {
        currentChartFilters = {};
        fetchData();
    });
    fetchData();
});

async function fetchData(filters = {}) {
    // Overwrite chart filters only if a new one is passed
    if (Object.keys(filters).length > 0) {
        currentChartFilters = filters;
    }

    const dateRange = document.getElementById('date-range-filter').value;
    const unit = document.getElementById('unit-filter').value;

    const queryParams = new URLSearchParams({
        date_range: dateRange,
        unit: unit,
        ...currentChartFilters
    });

    try {
        const response = await fetch(`/api/data?${queryParams.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        updateKPIs(data.kpis);
        updateCharts(data.charts);
        updatePatientTable(data.patient_details);
        
        document.getElementById('last-updated-time').textContent = new Date().toLocaleTimeString();
    } catch (error) {
        console.error("Error fetching or processing data:", error);
        const container = document.querySelector('.dashboard-container') || document.body;
        container.innerHTML = `<div style="color: red; padding: 20px;"><h2>Error Loading Dashboard</h2><p>${error.message}</p></div>`;
    }
}

function updateKPIs(kpis) {
    document.getElementById('bed-occupancy').textContent = kpis.bed_occupancy + '%';
    document.getElementById('patient-census').textContent = kpis.patient_census;
    document.getElementById('ventilator-utilization').textContent = kpis.ventilator_utilization + '%';
    document.getElementById('avg-los').textContent = kpis.avg_los;
}

function handleChartClick(event, chart) {
    const activePoints = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);
    if (activePoints.length > 0) {
        const clickedIndex = activePoints[0].index;
        const label = chart.data.labels[clickedIndex];
        const filterType = chart.canvas.id.split('-')[0]; // e.g., 'acuity' or 'admission'
        
        let filterKey;
        if (filterType === 'acuity') {
            filterKey = 'acuity_level';
        } else if (filterType === 'admission') {
            filterKey = 'admission_source';
        }

        if (filterKey) {
            fetchData({ [filterKey]: label });
        }
    }
}

function updateCharts(charts) {
    const chartUpdater = (chartInstance, chartId, chartConfig) => {
        const ctx = document.getElementById(chartId).getContext('2d');
        if (chartInstance) {
            chartInstance.data = chartConfig.data;
            chartInstance.options = chartConfig.options;
            chartInstance.update();
            return chartInstance;
        } else {
            return new Chart(ctx, chartConfig);
        }
    };

    censusChart = chartUpdater(censusChart, 'census-chart', {
        type: 'line',
        data: charts.census_over_time,
    });

    acuityChart = chartUpdater(acuityChart, 'acuity-chart', {
        type: 'bar',
        data: charts.acuity_levels,
        options: { 
            indexAxis: 'y', 
            onClick: (event) => handleChartClick(event, acuityChart) 
        }
    });

    admissionChart = chartUpdater(admissionChart, 'admission-chart', {
        type: 'doughnut',
        data: charts.admission_source,
        options: { 
            onClick: (event) => handleChartClick(event, admissionChart) 
        }
    });
}

function updatePatientTable(patients) {
    const tableBody = document.getElementById('patient-details-body');
    tableBody.innerHTML = '';
    patients.forEach(patient => {
        const row = `<tr>
            <td>${patient.PatientID}</td>
            <td>${patient.Unit}</td>
            <td>${patient.LengthOfStay}</td>
            <td>${patient.AcuityLevel}</td>
            <td>${patient.VentilatorStatus}</td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}
