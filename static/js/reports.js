document.addEventListener('DOMContentLoaded', function() {
    const reportsButton = document.getElementById('reports');
    if (reportsButton) {
        reportsButton.addEventListener('click', fetchReports);
    }
});

async function fetchReports() {
    const username = localStorage.getItem('savedUsername');
    
    try {
        const response = await fetch('/fetch-reports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        });

        if (response.ok) {
            const reports = await response.json();
            displayReportsModal(reports);
        } else {
            console.error('Failed to fetch reports');
        }
    } catch (error) {
        console.error('Error fetching reports:', error);
    }
}

function displayReportsModal(reports) {
    // Remove existing modal if it exists
    const existingModal = document.getElementById('reports-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal container
    const modalContainer = document.createElement('div');
    modalContainer.id = 'reports-modal';
    modalContainer.className = 'reports-modal';

    // Create reports list
    const reportsList = document.createElement('div');
    reportsList.className = 'reports-list';

    reports.forEach(report => {
        const reportItem = document.createElement('div');
        reportItem.className = 'report-item';
        reportItem.innerHTML = `
            <h3>${report.title || 'Untitled Report'}</h3>
            <p>Date: ${report.date || 'N/A'}</p>
            <button onclick="showReportDetails('${report._id}')">View Details</button>
        `;
        reportsList.appendChild(reportItem);
    });

    modalContainer.appendChild(reportsList);
    document.body.appendChild(modalContainer);

    // Add close functionality
    modalContainer.addEventListener('click', function(event) {
        if (event.target === modalContainer) {
            modalContainer.remove();
        }
    });
}

async function showReportDetails(reportId) {
    const username = localStorage.getItem('savedUsername');

    try {
        const response = await fetch('/report-details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                reportId: reportId,
                username: username 
            })
        });

        if (response.ok) {
            const reportDetails = await response.json();
            createReportDetailsModal(reportDetails);
        } else {
            console.error('Failed to fetch report details');
        }
    } catch (error) {
        console.error('Error fetching report details:', error);
    }
}

function createReportDetailsModal(reportDetails) {
    // Remove existing details modal
    const existingModal = document.getElementById('report-details-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create details modal
    const detailsModal = document.createElement('div');
    detailsModal.id = 'report-details-modal';
    detailsModal.className = 'report-details-modal';

    // Generate detailed HTML
    const detailsHTML = Object.entries(reportDetails)
        .filter(([key]) => !['_id', 'title'].includes(key))
        .map(([key, value]) => `<p><strong>${key}:</strong> ${value}</p>`)
        .join('');

    detailsModal.innerHTML = `
        <div class="report-details-content">
            <h2>${reportDetails.title || 'Report Details'}</h2>
            ${detailsHTML}
            <button onclick="closeReportDetails()">Close</button>
        </div>
    `;

    document.body.appendChild(detailsModal);
}

function closeReportDetails() {
    const detailsModal = document.getElementById('report-details-modal');
    if (detailsModal) {
        detailsModal.remove();
    }
}