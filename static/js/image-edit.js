/**
 * Image editing functionality for article images
 */

let currentArticleId = null;

function showImageModal(articleId) {
    currentArticleId = articleId;
    
    // Reset form
    const fileInput = document.getElementById('imageFileInput');
    const urlInput = document.getElementById('imageUrlInput');
    const preview = document.getElementById('imagePreview');
    
    if (fileInput) fileInput.value = '';
    if (urlInput) urlInput.value = '';
    if (preview) preview.style.display = 'none';
    
    // Show modal
    const modalElement = document.getElementById('imageEditModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Preview image when URL is entered
    const urlInput = document.getElementById('imageUrlInput');
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            const url = this.value.trim();
            const preview = document.getElementById('imagePreview');
            const previewImg = document.getElementById('previewImg');
            
            if (url && preview && previewImg) {
                previewImg.src = url;
                preview.style.display = 'block';
                previewImg.onerror = function() {
                    preview.style.display = 'none';
                };
            } else if (preview) {
                preview.style.display = 'none';
            }
        });
    }

    // Preview image when file is selected
    const fileInput = document.getElementById('imageFileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            const preview = document.getElementById('imagePreview');
            const previewImg = document.getElementById('previewImg');
            const urlInput = document.getElementById('imageUrlInput');
            
            if (file && preview && previewImg) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
                
                // Clear URL input
                if (urlInput) urlInput.value = '';
            } else if (preview) {
                preview.style.display = 'none';
            }
        });
    }

    // Save image button
    const saveBtn = document.getElementById('saveImageBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            if (!currentArticleId) return;
            
            const fileInput = document.getElementById('imageFileInput');
            const urlInput = document.getElementById('imageUrlInput');
            const url = urlInput ? urlInput.value.trim() : '';
            
            this.disabled = true;
            this.textContent = 'Sparar...';
            
            const formData = new FormData();
            
            if (fileInput && fileInput.files[0]) {
                formData.append('image_file', fileInput.files[0]);
            } else if (url) {
                formData.append('image_url', url);
            } else {
                alert('Välj en bild eller ange en URL');
                this.disabled = false;
                this.textContent = 'Spara bild';
                return;
            }
            
            fetch(`/api/article/${currentArticleId}/image`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update all images for this article
                    updateArticleImages(currentArticleId, data.image_url);
                    
                    // Close modal
                    const modalElement = document.getElementById('imageEditModal');
                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        if (modal) modal.hide();
                    }
                    
                    // Show success message
                    showAlert('Bilden har uppdaterats!', 'success');
                } else {
                    alert('Fel vid sparande: ' + (data.error || 'Okänt fel'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ett fel uppstod vid sparande av bilden');
            })
            .finally(() => {
                this.disabled = false;
                this.textContent = 'Spara bild';
            });
        });
    }
});

function updateArticleImages(articleId, newImageUrl) {
    // Update main table image
    const mainContainers = document.querySelectorAll(`[data-article-id="${articleId}"]`);
    mainContainers.forEach(container => {
        const mainImg = container.querySelector('.article-image');
        if (mainImg && mainImg.tagName === 'IMG') {
            mainImg.src = newImageUrl;
        }
    });
    
    // Update expanded detail images
    const detailSelectors = [`#details-${articleId}`, `#search-details-${articleId}`];
    detailSelectors.forEach(selector => {
        const detailContainer = document.querySelector(`${selector} .image-edit-container`);
        if (detailContainer) {
            const detailImg = detailContainer.querySelector('.editable-image');
            if (detailImg) {
                if (detailImg.tagName === 'IMG') {
                    detailImg.src = newImageUrl;
                } else {
                    // Replace placeholder with actual image
                    const newImg = document.createElement('img');
                    newImg.src = newImageUrl;
                    newImg.alt = 'Artikel';
                    newImg.className = 'img-fluid rounded shadow-sm editable-image';
                    newImg.style.cssText = 'max-width: 200px; max-height: 200px; object-fit: cover;';
                    detailImg.replaceWith(newImg);
                }
            }
        }
    });
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}