/**
 * ProcureIQ Data Extraction JavaScript
 * Handles the data extraction functionality
 */

// Initialize the data extraction page
function initializeDataExtractionPage() {
    console.log('Initializing data extraction page');
    
    // Setup event listeners for process button
    const processButton = document.getElementById('process-documents-btn');
    if (processButton) {
        console.log('Found process button, attaching event listener');
        processButton.addEventListener('click', function() {
            const rfqId = this.getAttribute('data-rfq-id');
            processDocuments(rfqId);
        });
    } else {
        console.warn('Process button not found');
    }
    
    // Setup handlers for existing items
    setupItemRowHandlers();
    
    // Setup add new item button
    const addItemButton = document.getElementById('add-item-btn');
    if (addItemButton) {
        console.log('Found add item button, attaching event listener');
        addItemButton.addEventListener('click', addNewItemRow);
    } else {
        console.warn('Add item button not found');
    }
    
    // Setup save button
    const saveButton = document.getElementById('save-items-btn');
    if (saveButton) {
        console.log('Found save button, attaching event listener with RFQ ID:', saveButton.getAttribute('data-rfq-id'));
        saveButton.addEventListener('click', function() {
            const rfqId = this.getAttribute('data-rfq-id');
            if (rfqId) {
                saveItemCorrections(rfqId);
            } else {
                console.error('Save button clicked but no RFQ ID found');
                showToast('Error: Could not determine RFQ ID', 'danger');
            }
        });
    } else {
        console.warn('Save button not found');
    }
}

// Process the documents of an RFQ
function processDocuments(rfqId) {
    showLoadingSpinner('items-container', 'Processing documents with AI...');
    
    fetch(`/rfq/${rfqId}/process`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error processing documents');
        }
        return response.json();
    })
    .then(data => {
        hideLoadingSpinner('items-container');
        if (data.status === 'success') {
            if (data.items && data.items.length > 0) {
                // Display the AI-generated items directly
                displayExtractedItems(data.items);
                showToast(`AI processing complete. Found ${data.items.length} items.`, 'success');
                // Enable save button
                const saveButton = document.getElementById('save-items-btn');
                if (saveButton) {
                    saveButton.disabled = false;
                }
            } else {
                // If no items in response, reload the page
                window.location.reload();
            }
        } else if (data.status === 'invalid_rfq') {
            // Handle invalid RFQ case
            displayExtractedItems(data.items);
            showToast(`Warning: ${data.message}`, 'warning');
            
            // Disable the save button
            const saveButton = document.getElementById('save-items-btn');
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.title = 'Cannot save - Not a valid RFQ document';
            }
            
            // Add alert message
            const itemsContainer = document.getElementById('items-container');
            if (itemsContainer) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-warning mt-3';
                alertDiv.innerHTML = '<strong>Cannot proceed:</strong> The document does not appear to be a valid RFQ. Please upload a valid RFQ document.';
                itemsContainer.appendChild(alertDiv);
            }
        } else {
            showToast(`Error: ${data.message || 'Unknown error'}`, 'danger');
        }
    })
    .catch(error => {
        hideLoadingSpinner('items-container');
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Display extracted items in the table
function displayExtractedItems(items) {
    const itemsContainer = document.getElementById('items-container');
    if (!itemsContainer) return;
    
    let html = `
    <table id="items-table" class="table table-striped">
        <thead>
            <tr>
                <th>#</th>
                <th>Item Name</th>
                <th>Quantity</th>
                <th>Description</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    if (items && items.length > 0) {
        items.forEach((item, index) => {
            html += `
            <tr data-item-id="${item.id}">
                <td class="item-number">${index + 1}</td>
                <td>
                    <input type="text" class="form-control item-name" value="${item.name || ''}" required>
                </td>
                <td>
                    <input type="number" class="form-control item-quantity" value="${item.quantity || 1}" min="1">
                </td>
                <td>
                    <textarea class="form-control item-description">${item.description || ''}</textarea>
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger delete-item-btn">
                        Delete
                    </button>
                </td>
            </tr>
            `;
        });
    } else {
        html += `
        <tr>
            <td colspan="5" class="text-center">No items extracted. You can add items manually or process documents again.</td>
        </tr>
        `;
    }
    
    html += `
        </tbody>
    </table>
    `;
    
    itemsContainer.innerHTML = html;
    
    // Setup handlers for the new rows
    setupItemRowHandlers();
}

// Setup handlers for item table rows
function setupItemRowHandlers() {
    // Delete item button handlers
    document.querySelectorAll('.delete-item-btn').forEach(button => {
        button.addEventListener('click', function() {
            const row = this.closest('tr');
            row.remove();
            renumberItems();
        });
    });
}

// Renumber the items in the table
function renumberItems() {
    document.querySelectorAll('#items-table .item-number').forEach((cell, index) => {
        cell.textContent = index + 1;
    });
}

// Add a new empty item row to the table
function addNewItemRow() {
    const itemsTable = document.getElementById('items-table');
    if (!itemsTable) return;
    
    const tbody = itemsTable.querySelector('tbody');
    const rowCount = tbody.querySelectorAll('tr').length;
    
    // Remove the "no items" row if it exists
    const noItemsRow = tbody.querySelector('tr td[colspan="5"]');
    if (noItemsRow) {
        noItemsRow.closest('tr').remove();
    }
    
    // Create a new row with a random ID
    const newId = 'new-' + Date.now();
    const newRow = document.createElement('tr');
    newRow.setAttribute('data-item-id', newId);
    
    newRow.innerHTML = `
        <td class="item-number">${rowCount + 1}</td>
        <td>
            <input type="text" class="form-control item-name" value="" required>
        </td>
        <td>
            <input type="number" class="form-control item-quantity" value="1" min="1">
        </td>
        <td>
            <textarea class="form-control item-description"></textarea>
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-danger delete-item-btn">
                Delete
            </button>
        </td>
    `;
    
    tbody.appendChild(newRow);
    
    // Setup handlers for the new row
    setupItemRowHandlers();
}

// Save the corrected items
function saveItemCorrections(rfqId) {
    console.log('Save button clicked for RFQ ID:', rfqId);
    
    const itemRows = document.querySelectorAll('#items-table tbody tr');
    console.log('Found item rows:', itemRows.length);
    
    const items = [];
    
    itemRows.forEach((row, index) => {
        // Skip the "no items" row if it exists
        if (row.querySelector('td[colspan="5"]')) {
            console.log('Skipping no-items row');
            return;
        }
        
        const itemId = row.getAttribute('data-item-id');
        const nameInput = row.querySelector('.item-name');
        const quantityInput = row.querySelector('.item-quantity');
        const descriptionInput = row.querySelector('.item-description');
        
        if (!nameInput || !quantityInput || !descriptionInput) {
            console.error('Missing input elements in row', index);
            return;
        }
        
        const name = nameInput.value;
        const quantity = parseInt(quantityInput.value) || 1;
        const description = descriptionInput.value;
        
        console.log(`Item ${index}:`, { id: itemId, name, quantity, description });
        
        if (name) {
            items.push({
                id: itemId,
                name: name,
                quantity: quantity,
                description: description
            });
        } else {
            console.warn('Skipping item with empty name');
        }
    });
    
    if (items.length === 0) {
        showToast('Please add at least one item', 'warning');
        return;
    }
    
    console.log('Sending items to server:', items);
    
    // Create a JSON string for debugging
    const jsonBody = JSON.stringify(items);
    console.log('Request JSON body:', jsonBody);
    
    fetch(`/rfq/${rfqId}/items`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: jsonBody
    })
    .then(response => {
        console.log('Server response status:', response.status);
        console.log('Server response headers:', [...response.headers.entries()]);
        
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Error response body:', text);
                throw new Error(`Error saving items: ${response.status} ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Save successful:', data);
        showToast('Items saved successfully', 'success');
    })
    .catch(error => {
        console.error('Save error:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Get confidence class based on value
function getConfidenceClass(confidence) {
    if (!confidence) return 'bg-secondary';
    if (confidence >= 0.8) return 'bg-success';
    if (confidence >= 0.5) return 'bg-info';
    if (confidence >= 0.3) return 'bg-warning';
    return 'bg-danger';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDataExtractionPage();
});