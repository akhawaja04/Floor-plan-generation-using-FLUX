document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all download buttons
    const downloadButtons = document.querySelectorAll('.download-btn');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            const imageUrl = this.closest('.group').querySelector('input[name="selectedImageUrl"]').value;
            downloadImage(format, imageUrl);
        });
    });
});

async function downloadImage(format, imageUrl) {
    if (!imageUrl) {
        console.error('No image URL found');
        return;
    }

    try {
        // Extract the filename from the image URL
        const filename = imageUrl.split('/').pop();
        
        if (!filename) throw new Error("Invalid filename extracted.");

        const response = await fetch(`/download_image/${format}/?image_url=${encodeURIComponent(filename)}`, {
            method: 'GET',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': getCSRFToken() 
            },
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

        console.log(`Floor plan downloaded successfully as ${format.toUpperCase()}`);
        // If you have a toast function
        if (typeof showToast === 'function') {
            showToast(`Floor plan downloaded successfully as ${format.toUpperCase()}`, 'success');
        }
    } catch (error) {
        console.error('Download error:', error);
        // If you have a toast function
        if (typeof showToast === 'function') {
            showToast('Error downloading floor plan', 'error');
        }
    }
}

// Function to get CSRF token
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}