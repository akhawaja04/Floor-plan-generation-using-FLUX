// Global variables
let selectedPlan = null;
let customRoomCount = 0;

// Initialize application
document.addEventListener("DOMContentLoaded", function() {
    setupFormHandlers();
    setupDownloadHandlers();
});

// CSRF token handling for Django
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : null;
}

// Update addCustomRoom to use the provided roomKey
function addCustomRoom(name, area, ratio, roomKey) {
    // Use the provided roomKey if available, otherwise format the name
    const formattedName = roomKey || name.toLowerCase().replace(/\s+/g, '_');
    
    console.log(`Adding room with formattedName: ${formattedName}`);
    
    const customRoomHTML = `
        <div class="room-item" data-room-name="${formattedName}">
            <div class="room-name">
                ${name}
                <span class="room-color" style="background-color: ${getRoomColor(formattedName)};"></span>
            </div>
            <div class="room-inputs">
                <div class="input-group">
                    <div class="input-label">Area</div>
                    <input type="number" name="${formattedName}_area" value="${area}" class="room-input" placeholder="sqft">
                </div>
                <div class="input-group">
                    <div class="input-label">Ratio</div>
                    <input type="text" name="${formattedName}_ratio" value="${ratio}" class="room-input" placeholder="width:length">
                </div>
            </div>
        </div>
    `;

    document.getElementById('customRoomsContainer').insertAdjacentHTML('beforeend', customRoomHTML);
}

// checking the sent data
// Function to handle form submission
// async function handleFormSubmission(event) {
//     event.preventDefault();
//     showLoading(true);


//     try {
//         const formData = new FormData(event.target);
//        // Log form data for debugging
//         for (let [key, value] of formData.entries()) {
//             console.log(`Form Data - Key: ${key}, Value: ${value}`);
//         }

//         const response = await fetch("/generate_prompt/", {
//             method: "POST",
//             headers: {
//                 'X-CSRFToken': getCSRFToken(),
//             },
//             body: formData
//         });

//         const data = await response.json();
//         console.log("API Response:", data);

//         if (data.success && data.image_urls) {
//             updatePreview(data.image_urls);
//             showToast(`Successfully generated ${data.image_urls.length} floor plan${data.image_urls.length > 1 ? 's' : ''}`, "success");
//         } else {
//             showToast(data.error || "Error generating floor plan", "error");
//         }
//     } catch (error) {
//         console.error("Form submission error:", error);
//         showToast("Error submitting form", "error");
//     } finally {
//         showLoading(false);
//     }
// }

// Global variable to track our simulated or actual progress
let loadingProgress = 0;
let progressInterval;

function showLoading(show, estimatedTime = 10000) {
    const overlay = document.getElementById('loadingOverlay');
    const percentageEl = document.getElementById('loadingPercentage');
    
    if (overlay) {
        overlay.classList.toggle('active', show);
        
        if (show) {
            // Reset progress
            loadingProgress = 0;
            updatePercentage(loadingProgress);
            
            // Clear any existing interval
            clearInterval(progressInterval);
            
            // Start simulated progress
            progressInterval = setInterval(() => {
                // Simulate progress - goes faster at first, then slows down approaching 100%
                if (loadingProgress < 75) {
                    loadingProgress += Math.random() * 3 + 1;
                } else if (loadingProgress < 98) {
                    loadingProgress += 0.2;
                }
                
                // Ensure we don't exceed 99% (we'll set it to 100% when actually complete)
                loadingProgress = Math.min(99, loadingProgress);
                updatePercentage(loadingProgress);
            }, estimatedTime / 100); // Adjust frequency based on estimated time
        } else {
            // When hiding, show 100% briefly before hiding
            updatePercentage(100);
            clearInterval(progressInterval);
        }
    }
}

function updatePercentage(percentage) {
    const percentageEl = document.getElementById('loadingPercentage');
    if (percentageEl) {
        percentageEl.textContent = `${Math.round(percentage)}%`;
    }
}

async function handleFormSubmission(event) {
    event.preventDefault();
    
    // Show loading with an estimated time (in ms) - adjust based on your average generation time
    showLoading(true, 15000); // 15 seconds estimated time
    
    try {
        const formData = new FormData(event.target);
        // Log form data for debugging
        for (let [key, value] of formData.entries()) {
            console.log(`Form Data - Key: ${key}, Value: ${value}`);
        }

        const response = await fetch("/generate_prompt/", {
            method: "POST",
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
            body: formData
        });

        const data = await response.json();
        console.log("API Response:", data);

        if (data.success && data.image_urls) {
            // Briefly show 100% before hiding
            updatePercentage(100);
            setTimeout(() => {
                showLoading(false);
                updatePreview(data.image_urls);
                showToast(`Successfully generated ${data.image_urls.length} floor plan${data.image_urls.length > 1 ? 's' : ''}`, "success");
            }, 500);
        } else {
            showLoading(false);
            showToast(data.error || "Error generating floor plan", "error");
        }
    } catch (error) {
        console.error("Form submission error:", error);
        showLoading(false);
        showToast("Error submitting form", "error");
    }
}


// Custom room management
window.showNewRoomForm = function() {
    document.getElementById("newRoomForm").classList.add("active");
};

window.confirmAddRoom = function() {
    let roomName = document.getElementById("newRoomName").value.trim();
    const roomArea = document.getElementById("newRoomArea").value;
    const roomRatio = document.getElementById("newRoomRatio").value;
    
    if (!roomName || !roomArea || !roomRatio) {
        showToast("Please fill in all room fields", "error");
        return;
    }
    
    // Replace spaces with underscores to match Django's expected format
    let baseRoomKey = roomName.replace(/\s+/g, '_').toLowerCase();
    
    // Check if this room name already exists by looking for matching inputs directly
    const existingInputs = document.querySelectorAll(`input[name="${baseRoomKey}_area"]`);
    
    let roomKey = baseRoomKey;
    
    if (existingInputs.length > 0) {
        // Room exists, we need to find a unique name
        let count = 1;
        
        // Keep checking until we find a name that doesn't exist
        while (document.querySelector(`input[name="${baseRoomKey}_${count}_area"]`)) {
            count++;
        }
        
        roomKey = `${baseRoomKey}_${count}`;
    }
    
    console.log(`Using room key: ${roomKey} for room: ${roomName}`);
    
    // Call addCustomRoom with the determined roomKey
    addCustomRoom(roomName, roomArea, roomRatio, roomKey);
    cancelNewRoom();
};


window.cancelNewRoom = function() {
    document.getElementById("newRoomForm").classList.remove("active");
    clearNewRoomForm();
};
// Setup form handlers
function setupFormHandlers() {
    const roomConfigForm = document.getElementById("roomConfigForm");
    if (roomConfigForm) {
        roomConfigForm.addEventListener("submit", handleFormSubmission);
    }
}


function getRoomColor(roomName) {
    const baseName = roomName.split('_')[0];
    const baseColors = {
        kitchen: "lightcoral",
        living: "palegoldenrod",
        common: "orange",
        balcony: "OliveDrab",
        master: "gold",
        bathroom: "skyblue",
        storage: "Orchid"
    };
    

    return baseColors[baseName] || "#" + Math.floor(Math.random() * 16777215).toString(16);
}


// Function to select an image
function selectImage(imageUrl) {
    document.getElementById('selectedImageUrl').value = imageUrl;
    showToast('Image selected', 'info');
}

function updatePreview(images) {
    console.log("Updating preview with images:", images);
    const previewContainer = document.getElementById("preview-container");
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0];

    if (!previewContainer) {
        console.error("Preview container not found!");
        return;
    }

    // Create the popup only once
    let previewTimeout;
    const popup = document.querySelector('.image-preview-popup') || document.createElement('div');
    popup.className = 'image-preview-popup';
    popup.style.position = 'absolute';
    popup.style.display = 'none';
    popup.style.zIndex = 9999;
    popup.style.border = '2px solid #fff';
    popup.style.backgroundColor = '#fff';
    popup.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.2)';
    popup.style.padding = '5px';
    document.body.appendChild(popup);

    // Clear previous images
    const previewGrid = previewContainer.querySelector('.preview-grid') ||
        document.createElement('div');
    previewGrid.className = 'preview-grid';
    previewGrid.innerHTML = '';

    if (!images || images.length === 0) {
        previewGrid.innerHTML = `<div class="no-images">No images generated.</div>`;
        return;
    }

    previewGrid.classList.add(`images-${images.length}`);

    images.forEach((imageUrl, index) => {
        console.log(`Creating image element for URL: ${imageUrl}`);

        const wrapper = document.createElement('div');
        wrapper.className = 'preview-image-wrapper';

        const imgElement = document.createElement('img');
        imgElement.src = `${imageUrl}?t=${timestamp}`;
        imgElement.alt = `Generated Floor Plan ${index + 1}`;
        imgElement.className = 'preview-image loading';

        // Error and load handling
        imgElement.onerror = () => {
            console.error(`Failed to load image: ${imageUrl}`);
            wrapper.innerHTML = `
                <div class="error-message">
                    Failed to load image ${index + 1}
                    <button onclick="retryImage('${imageUrl}', ${index})">Retry</button>
                </div>
            `;
        };

        imgElement.onload = () => {
            imgElement.classList.remove('loading');
            showToast(`Image ${index + 1} loaded successfully`, "success");
        };

        // Hover preview
        imgElement.addEventListener('mouseenter', (e) => {
            previewTimeout = setTimeout(() => {
                popup.innerHTML = `<img src="${imgElement.src}" style="max-width: 400px; max-height: 400px;" />`;
                popup.style.left = `${e.pageX + 20}px`;
                popup.style.top = `${e.pageY + 20}px`;
                popup.style.display = 'block';
            }, 500); // show after 0.5s
        });

        imgElement.addEventListener('mousemove', (e) => {
            popup.style.left = `${e.pageX + 20}px`;
            popup.style.top = `${e.pageY + 20}px`;
        });

        imgElement.addEventListener('mouseleave', () => {
            clearTimeout(previewTimeout);
            popup.style.display = 'none';
        });

        // Click to select
        imgElement.addEventListener('click', () => {
            selectImage(imageUrl);
        });

        wrapper.appendChild(imgElement);
        previewGrid.appendChild(wrapper);
    });

    // Replace or append the grid
    const existingGrid = previewContainer.querySelector('.preview-grid');
    if (existingGrid) {
        existingGrid.replaceWith(previewGrid);
    } else {
        previewContainer.prepend(previewGrid);
    }

    // Update status
    const status = previewContainer.querySelector('.generation-status');
    if (status) {
        status.textContent = `Generated ${images.length} floor plan${images.length > 1 ? 's' : ''}`;
    }
}




async function downloadImage(format) {
    let imageUrl = document.getElementById('selectedImageUrl').value;
    
    if (!imageUrl) {
        const previewImages = document.querySelectorAll('.preview-image');
        if (previewImages.length === 0) {
            showToast('Please generate a floor plan first', 'error');
            return;
        }
        imageUrl = previewImages[previewImages.length - 1].src;
    }

    try {
        const url = new URL(imageUrl, window.location.origin);
        const filename = url.pathname.split('/').pop();

        if (!filename) throw new Error("Invalid filename extracted.");

        const response = await fetch(`/download_image/${format}/?image_url=${encodeURIComponent(filename)}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
        });

        if (!response.ok) throw new Error('Download failed');

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `floorplan.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);

        showToast(`Floor plan downloaded successfully as ${format.toUpperCase()}`, 'success');
    } catch (error) {
        console.error('Download error:', error);
        showToast('Error downloading floor plan', 'error');
    }
}

async function openInLibreCAD() {
    let imageUrl = document.getElementById('selectedImageUrl').value;

    if (!imageUrl) {
        const previewImages = document.querySelectorAll('.preview-image');
        if (previewImages.length === 0) {
            showToast('Please generate a floor plan first', 'error');
            return;
        }
        imageUrl = previewImages[previewImages.length - 1].src;
    }

    try {
        const url = new URL(imageUrl, window.location.origin);
        const filename = url.pathname.split('/').pop();

        if (!filename) throw new Error("Invalid filename extracted.");

        const response = await fetch(`/download_image/redirect/?image_url=${encodeURIComponent(filename)}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong');
        }

        showToast('Opened in LibreCAD successfully', 'success');
        console.log('LibreCAD launch response:', data);

    } catch (error) {
        console.error('LibreCAD redirect error:', error);
        showToast('Error opening in LibreCAD', 'error');
    }
}

// Download handlers
function setupDownloadHandlers() {
    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            if (format === 'redirect') {
                openInLibreCAD();
            } 
            else {
                downloadImage(format);
            }
        });
    });
}

document.getElementById('ratioInput').addEventListener('input', function () {
    const value = this.value;
    const match = value.match(/^(\d{1,2}):(\d{1,2})$/);
    if (match) {
      const width = parseInt(match[1], 10);
      const length = parseInt(match[2], 10);
      if (width < 1 || width > 20 || length < 1 || length > 20) {
        this.setCustomValidity("Both numbers must be between 1 and 20.");
      } else {
        this.setCustomValidity(""); // input is valid
      }
    } else {
      this.setCustomValidity("Format must be width:length (e.g., 4:5)");
    }
  });
// Function to retry loading a failed image
window.retryImage = function(url, index) {
    const timestamp = new Date().getTime();
    const wrapper = document.querySelector(`.preview-image-wrapper:nth-child(${index + 1})`);
    if (wrapper) {
        const img = document.createElement('img');
        img.src = `${url}?t=${timestamp}`;
        img.alt = `Generated Floor Plan ${index + 1}`;
        img.className = 'preview-image loading';

        img.onload = () => {
            img.classList.remove('loading');
            showToast(`Image ${index + 1} reloaded successfully`, "success");
        };

        img.onerror = () => {
            wrapper.innerHTML = `
                <div class="error-message">
                    Failed to load image ${index + 1}
                    <button onclick="retryImage('${url}', ${index})">Retry</button>
                </div>
            `;
        };

        wrapper.innerHTML = '';
        wrapper.appendChild(img);
    }
}

// Function to show full-size image
window.showFullSizeImage = function(url) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <img src="${url}" alt="Full size floor plan">
        </div>
    `;

    modal.querySelector('.close-modal').onclick = () => {
        modal.remove();
    };

    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    };

    document.body.appendChild(modal);
}

// Add these styles for the modal
const modalStyles = `
.image-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.9);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    position: relative;
    max-width: 90%;
    max-height: 90%;
}

.modal-content img {
    max-width: 100%;
    max-height: 90vh;
    object-fit: contain;
}

.close-modal {
    position: absolute;
    top: -30px;
    right: -30px;
    color: white;
    font-size: 30px;
    cursor: pointer;
}

.loading {
    opacity: 0.5;
}

.error-message {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: red;
}

.error-message button {
    margin-top: 10px;
    padding: 5px 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.error-message button:hover {
    background-color: #0056b3;
}
`;

// Add the styles to the document
const styleSheet = document.createElement("style");
styleSheet.textContent = modalStyles;
document.head.appendChild(styleSheet);





function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => {
            toast.className = 'toast';
        }, 3000);
    }
}

function clearNewRoomForm() {
    document.getElementById("newRoomName").value = "";
    document.getElementById("newRoomArea").value = "";
    document.getElementById("newRoomRatio").value = "";
}