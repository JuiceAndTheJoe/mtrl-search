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
    const currentSection = document.getElementById('currentImageSection');
    const currentImg = document.getElementById('currentImg');
    
    if (fileInput) fileInput.value = '';
    if (urlInput) urlInput.value = '';
    if (preview) preview.style.display = 'none';
    
    // Check if article has current image and show it
    const expandedContainer = document.querySelector(`#details-${articleId} .image-edit-container, #search-details-${articleId} .image-edit-container`);
    if (expandedContainer && currentSection && currentImg) {
        const currentImage = expandedContainer.querySelector('.editable-image');
        if (currentImage && currentImage.tagName === 'IMG' && currentImage.src) {
            currentImg.src = currentImage.src;
            currentSection.style.display = 'block';
        } else {
            currentSection.style.display = 'none';
        }
    }
    
    // Show modal
    const modalElement = document.getElementById('imageEditModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Event delegation for edit image buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-image-btn')) {
            e.stopPropagation(); // Prevent row expansion
            const button = e.target.closest('.edit-image-btn');
            const articleId = button.getAttribute('data-article-id');
            if (articleId) {
                showImageModal(parseInt(articleId));
            }
        }
        
        // Event delegation for view image buttons
        if (e.target.closest('.view-image-btn')) {
            e.stopPropagation(); // Prevent row expansion
            const button = e.target.closest('.view-image-btn');
            const imageUrl = button.getAttribute('data-image-url');
            const articleName = button.getAttribute('data-article-name');
            if (imageUrl) {
                showImageViewer(imageUrl, articleName);
            }
        }
        
        // Prevent row expansion when clicking on image edit overlay
        if (e.target.closest('.image-edit-overlay')) {
            e.stopPropagation();
        }
        
        // Prevent row expansion when clicking on search link
        if (e.target.closest('.btn-outline-primary')) {
            e.stopPropagation();
        }
    });
    
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

    // Delete image button
    const deleteBtn = document.getElementById('deleteImageBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            if (!currentArticleId) return;
            
            if (confirm('Är du säker på att du vill ta bort denna bild?')) {
                this.disabled = true;
                this.textContent = 'Tar bort...';
                
                fetch(`/api/article/${currentArticleId}/image`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update images to show placeholders
                        removeArticleImages(currentArticleId);
                        
                        // Close modal
                        const modalElement = document.getElementById('imageEditModal');
                        if (modalElement) {
                            const modal = bootstrap.Modal.getInstance(modalElement);
                            if (modal) modal.hide();
                        }
                        
                        // Show success message
                        showAlert('Bilden har tagits bort!', 'success');
                    } else {
                        alert('Fel vid borttagning: ' + (data.error || 'Okänt fel'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Ett fel uppstod vid borttagning av bilden');
                })
                .finally(() => {
                    this.disabled = false;
                    this.textContent = 'Ta bort bild';
                });
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

    // Download image button
    const downloadBtn = document.getElementById('downloadImageBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            const img = document.getElementById('fullscreenImg');
            if (img && img.src) {
                downloadImage(img.src, img.alt || 'artikel-bild');
            }
        });
    }
});

function updateArticleImages(articleId, newImageUrl) {
    console.log(`Updating images for article ${articleId} with URL: ${newImageUrl}`);
    
    // Update main table image (the small one in the table row)
    const mainImageContainer = document.querySelector(`.main-image-container[data-article-id="${articleId}"]`);
    if (mainImageContainer) {
        const mainImg = mainImageContainer.querySelector('.article-image, .article-image-placeholder');
        if (mainImg) {
            if (mainImg.tagName === 'IMG') {
                console.log('Updating main table image');
                mainImg.src = newImageUrl;
            } else {
                // Replace placeholder with actual image in main table
                console.log('Replacing placeholder in main table');
                const newImg = document.createElement('img');
                newImg.src = newImageUrl;
                newImg.alt = 'Artikel';
                newImg.className = 'article-image img-thumbnail';
                newImg.onerror = function() { this.style.display = 'none'; };
                mainImg.replaceWith(newImg);
            }
        }
    }
    
    // Update expanded detail images
    const detailSelectors = [`#details-${articleId}`, `#search-details-${articleId}`];
    detailSelectors.forEach(selector => {
        const detailContainer = document.querySelector(`${selector} .image-edit-container`);
        if (detailContainer) {
            const detailImg = detailContainer.querySelector('.editable-image');
            if (detailImg) {
                if (detailImg.tagName === 'IMG') {
                    console.log('Updating expanded detail image');
                    detailImg.src = newImageUrl;
                } else {
                    // Replace placeholder with actual image in expanded view
                    console.log('Replacing placeholder in expanded view');
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

function removeArticleImages(articleId) {
    console.log(`Removing images for article ${articleId}`);
    
    // Remove main table image (replace with placeholder)
    const mainImageContainer = document.querySelector(`.main-image-container[data-article-id="${articleId}"]`);
    if (mainImageContainer) {
        const mainImg = mainImageContainer.querySelector('.article-image, .article-image-placeholder');
        if (mainImg) {
            console.log('Replacing main table image with placeholder');
            const placeholder = document.createElement('div');
            placeholder.className = 'article-image-placeholder';
            placeholder.innerHTML = '<span>📷</span>';
            mainImg.replaceWith(placeholder);
        }
    }
    
    // Remove expanded detail images (replace with placeholder)
    const detailSelectors = [`#details-${articleId}`, `#search-details-${articleId}`];
    detailSelectors.forEach(selector => {
        const detailContainer = document.querySelector(`${selector} .image-edit-container`);
        if (detailContainer) {
            const detailImg = detailContainer.querySelector('.editable-image');
            if (detailImg) {
                console.log('Replacing expanded detail image with placeholder');
                const placeholder = document.createElement('div');
                placeholder.className = 'd-flex align-items-center justify-content-center bg-white border rounded shadow-sm editable-image';
                placeholder.style.cssText = 'width: 200px; height: 200px;';
                placeholder.innerHTML = '<span class="text-muted fs-1">📷</span>';
                detailImg.replaceWith(placeholder);
            }
        }
    });
}

function showImageViewer(imageUrl, articleName) {
    const modal = document.getElementById('imageViewerModal');
    const img = document.getElementById('fullscreenImg');
    const title = document.getElementById('imageViewerModalLabel');
    
    if (modal && img) {
        img.src = imageUrl;
        img.alt = articleName || 'Artikel bild';
        
        if (title) {
            title.textContent = `Bildvisning - ${articleName || 'Artikel'}`;
        }
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Add keyboard navigation
        const handleKeyPress = (e) => {
            if (e.key === 'Escape') {
                bsModal.hide();
            }
        };
        
        document.addEventListener('keydown', handleKeyPress);
        
        // Remove event listener when modal is hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.removeEventListener('keydown', handleKeyPress);
        }, { once: true });
    }
}

function downloadImage(imageUrl, filename) {
    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = filename.replace(/[^a-z0-9.-]/gi, '_') + '.jpg';
    
    // For external URLs, we need to fetch and convert to blob
    if (imageUrl.startsWith('http')) {
        fetch(imageUrl)
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                link.href = url;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Error downloading image:', error);
                // Fallback: open in new tab
                window.open(imageUrl, '_blank');
            });
    } else {
        // For local images, direct download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
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