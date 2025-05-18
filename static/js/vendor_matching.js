/**
 * ProcureIQ Vendor Matching JavaScript
 * Handles the vendor matching functionality
 */

// Initialize the vendor matching page
function initializeVendorMatchingPage() {
    // Setup event listeners for match vendors button
    const matchButton = document.getElementById('match-vendors-btn');
    if (matchButton) {
        matchButton.addEventListener('click', function() {
            const rfqId = this.getAttribute('data-rfq-id');
            matchVendorsForRfq(rfqId);
        });
    }
    
    // Initialize email generation buttons
    initializeEmailButtons();
    
    // Setup search form
    const searchForm = document.getElementById('vendor-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            searchVendors();
        });
    }
}

// Match vendors for items in an RFQ
function matchVendorsForRfq(rfqId) {
    showLoadingSpinner('vendor-matches-container', 'Finding suitable vendors...');
    
    fetch(`/vendors/match/${rfqId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error matching vendors');
        }
        return response.json();
    })
    .then(data => {
        hideLoadingSpinner('vendor-matches-container');
        displayVendorMatches(data, rfqId);
        showToast('Vendor matching completed', 'success');
    })
    .catch(error => {
        hideLoadingSpinner('vendor-matches-container');
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Display vendor matches for items
function displayVendorMatches(itemVendorMatches, rfqId) {
    const container = document.getElementById('vendor-matches-container');
    if (!container) return;
    
    let html = '';
    
    if (Object.keys(itemVendorMatches).length === 0) {
        html = `
        <div class="alert alert-info">
            No vendor matches found. You can try expanding your search criteria or adding more vendors to the system.
        </div>
        `;
    } else {
        // For each item, display matched vendors
        for (const itemId in itemVendorMatches) {
            const item = itemVendorMatches[itemId];
            const matchedVendors = item.vendors;
            
            html += `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="card-title">Item: ${item.name}</h5>
                    <h6 class="card-subtitle text-muted">${item.description || 'No description'}</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Vendor</th>
                                    <th>Match Score</th>
                                    <th>Type</th>
                                    <th>Location</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            if (matchedVendors && matchedVendors.length > 0) {
                matchedVendors.forEach((match, index) => {
                    const vendor = match.vendor;
                    const matchScore = match.score;
                    
                    html += `
                    <tr>
                        <td>
                            <strong>${vendor.name}</strong>
                            ${vendor.website ? `<br><a href="${vendor.website}" target="_blank" class="small">${vendor.website}</a>` : ''}
                        </td>
                        <td>
                            <div class="progress">
                                <div class="progress-bar ${getMatchScoreClass(matchScore)}" 
                                     role="progressbar" 
                                     style="width: ${matchScore}%" 
                                     aria-valuenow="${matchScore}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                    ${Math.round(matchScore)}%
                                </div>
                            </div>
                        </td>
                        <td>${vendor.vendor_type}</td>
                        <td>${vendor.location.country}${vendor.location.city ? ', ' + vendor.location.city : ''}</td>
                        <td>
                            <button type="button" 
                                    class="btn btn-sm btn-primary generate-email-btn" 
                                    data-rfq-id="${rfqId}" 
                                    data-vendor-id="${vendor.id}"
                                    data-serial="${index + 1}">
                                <span data-feather="mail"></span> Email
                            </button>
                            <a href="/vendors/${vendor.id}" class="btn btn-sm btn-outline-secondary">
                                <span data-feather="info"></span> Details
                            </a>
                        </td>
                    </tr>
                    `;
                });
            } else {
                html += `
                <tr>
                    <td colspan="5" class="text-center">No vendors found for this item.</td>
                </tr>
                `;
            }
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            `;
        }
    }
    
    container.innerHTML = html;
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Initialize email buttons
    initializeEmailButtons();
}

// Initialize email generation buttons
function initializeEmailButtons() {
    document.querySelectorAll('.generate-email-btn').forEach(button => {
        button.addEventListener('click', function() {
            const rfqId = this.getAttribute('data-rfq-id');
            const vendorId = this.getAttribute('data-vendor-id');
            const serial = this.getAttribute('data-serial');
            generateEmail(rfqId, vendorId, serial);
        });
    });
}

// Generate an email for a vendor
function generateEmail(rfqId, vendorId, serial) {
    showLoadingSpinner('email-preview-container', 'Generating email...');
    
    fetch(`/emails/generate/${rfqId}/${vendorId}?serial=${serial}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error generating email');
        }
        return response.json();
    })
    .then(data => {
        hideLoadingSpinner('email-preview-container');
        showEmailPreviewModal(data);
    })
    .catch(error => {
        hideLoadingSpinner('email-preview-container');
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Show email preview modal
function showEmailPreviewModal(email) {
    const modalContainer = document.getElementById('modal-container');
    if (!modalContainer) {
        const div = document.createElement('div');
        div.id = 'modal-container';
        document.body.appendChild(div);
    }
    
    const modal = `
    <div class="modal fade" id="emailPreviewModal" tabindex="-1" aria-labelledby="emailPreviewModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="emailPreviewModalLabel">Email Preview</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">To:</label>
                        <p class="form-control-plaintext">${email.vendor_name} &lt;${email.vendor_email}&gt;</p>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Subject:</label>
                        <p class="form-control-plaintext">${email.subject}</p>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Body:</label>
                        <div class="card">
                            <div class="card-body">
                                ${email.body.replace(/\n/g, '<br>')}
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Attachments:</label>
                        <ul class="list-group">
                            ${email.attachments.map(att => `<li class="list-group-item">${att}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary send-email-btn" data-email-id="${email.id}">Send Email</button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    document.getElementById('modal-container').innerHTML = modal;
    
    // Initialize and show the modal
    const modalElement = document.getElementById('emailPreviewModal');
    const bootstrapModal = new bootstrap.Modal(modalElement);
    bootstrapModal.show();
    
    // Setup send email button
    document.querySelector('.send-email-btn').addEventListener('click', function() {
        const emailId = this.getAttribute('data-email-id');
        sendEmail(emailId);
        bootstrapModal.hide();
    });
}

// Send an email
function sendEmail(emailId) {
    showToast('Sending email...', 'info');
    
    fetch(`/emails/send/${emailId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error sending email');
        }
        return response.json();
    })
    .then(data => {
        showToast('Email sent successfully', 'success');
    })
    .catch(error => {
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Search vendors by criteria
function searchVendors() {
    const form = document.getElementById('vendor-search-form');
    const formData = new FormData(form);
    
    const queryParams = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
        if (value) {
            queryParams.append(key, value);
        }
    }
    
    showLoadingSpinner('search-results-container', 'Searching vendors...');
    
    fetch(`/vendors/search?${queryParams.toString()}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error searching vendors');
        }
        return response.json();
    })
    .then(data => {
        hideLoadingSpinner('search-results-container');
        displaySearchResults(data);
    })
    .catch(error => {
        hideLoadingSpinner('search-results-container');
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Display vendor search results
function displaySearchResults(vendors) {
    const container = document.getElementById('search-results-container');
    if (!container) return;
    
    let html = '';
    
    if (vendors.length === 0) {
        html = `
        <div class="alert alert-info">
            No vendors found matching your criteria. Try broadening your search.
        </div>
        `;
    } else {
        html = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Vendor</th>
                        <th>Type</th>
                        <th>Location</th>
                        <th>Specializations</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        vendors.forEach(vendor => {
            html += `
            <tr>
                <td>
                    <strong>${vendor.name}</strong>
                    ${vendor.website ? `<br><a href="${vendor.website}" target="_blank" class="small">${vendor.website}</a>` : ''}
                </td>
                <td>${vendor.vendor_type}</td>
                <td>${vendor.location.country}${vendor.location.city ? ', ' + vendor.location.city : ''}</td>
                <td>
                    ${vendor.specializations.map(spec => `<span class="badge bg-secondary me-1">${spec}</span>`).join('')}
                </td>
                <td>
                    <a href="/vendors/${vendor.id}" class="btn btn-sm btn-primary">
                        <span data-feather="info"></span> Details
                    </a>
                </td>
            </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        </div>
        `;
    }
    
    container.innerHTML = html;
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Get match score class based on score value
function getMatchScoreClass(score) {
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-info';
    if (score >= 40) return 'bg-primary';
    if (score >= 20) return 'bg-warning';
    return 'bg-danger';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeVendorMatchingPage();
});