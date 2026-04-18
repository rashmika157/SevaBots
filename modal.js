/**
 * modal.js
 * Handles the "View Details" modal rendering for scheme cards globally.
 * Now receives full Scheme JSON object dynamically.
 */

window.showSchemeModal = function(schemeObj) {
  // If a modal already exists, remove it
  let existingModal = document.getElementById('scheme-details-modal');
  if (existingModal) {
    existingModal.remove();
  }

  const name = schemeObj.name || "Scheme Details";
  const benefits = schemeObj.benefits || "Comprehensive welfare benefits provided by the government.";
  const link = schemeObj.link || "#";
  const linkTarget = schemeObj.link ? 'target="_blank"' : '';
  const btnLabel = schemeObj.link ? 'Visit Official Website &#8599;' : 'Portal Link Unavailable';

  // Extract or Fallback steps
  let steps = schemeObj.steps;
  if (!steps || steps.length === 0) {
    steps = [
      "Visit the official portal or your nearest service center.",
      "Complete the application form with your personal details.",
      "Upload/submit the necessary documents.",
      "Ensure all entries are correct and submit your application."
    ];
  }

  // Extract or Fallback documents
  let documents = schemeObj.documents;
  if (!documents || documents.length === 0) {
    documents = [
      "Aadhaar Card",
      "Valid Identity Proof",
      "Bank Account Details",
      "Income/Caste Certificate (if applicable)"
    ];
  }

  // Create the overlay container
  const modalOverlay = document.createElement('div');
  modalOverlay.id = 'scheme-details-modal';
  modalOverlay.className = 'modal-overlay';
  
  // Close the modal if clicking outside the content
  modalOverlay.addEventListener('click', function(e) {
    if (e.target === modalOverlay) {
      window.closeModal();
    }
  });

  // Construct the HTML for the internal content
  modalOverlay.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">${window.t(name)}</h2>
        <button class="modal-close-btn" onclick="window.closeModal()">&times;</button>
      </div>

      <div class="modal-body">
        <div class="modal-benefits-box">
           <strong>${window.t("Description:")}</strong> ${window.t(benefits)}
        </div>

        <div class="modal-section mt-high">
          <div class="modal-section-title"><span class="icon-emoji">📄</span> ${window.t("Required Documents")}</div>
          <ul class="modal-list docs-list">
            ${documents.map(doc => `<li><span class="doc-item-text">${window.t(doc)}</span></li>`).join('')}
          </ul>
        </div>

        <div class="modal-section mt-high">
          <div class="modal-section-title"><span class="icon-emoji">🛠️</span> ${window.t("How to Apply")}</div>
          <ul class="modal-list steps-list">
            ${steps.map(step => `<li><span class="step-item-text">${window.t(step)}</span></li>`).join('')}
          </ul>
        </div>
        
        <div class="modal-section" style="margin-top: 40px; text-align: center; display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
          <a href="${link}" class="modal-website-btn" ${linkTarget} rel="noopener noreferrer">${window.t(btnLabel)}</a>
          <button class="btn" id="modal-apply-action" style="box-shadow: none; width: auto; padding: 12px 24px; border-radius: 8px;">${window.t("Save to Dashboard")}</button>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn" style="background-color: transparent; color: var(--secondary-text); border: 1px solid var(--border-color); width: auto; box-shadow: none;" onclick="window.closeModal()">${window.t("Close")}</button>
      </div>
    </div>
  `;

  document.body.appendChild(modalOverlay);

  // Hook up the apply button
  const applyBtn = document.getElementById('modal-apply-action');
  if (applyBtn) {
      applyBtn.addEventListener('click', () => {
         const savedSchemesRaw = localStorage.getItem('savedSchemes');
         let savedSchemes = [];
         if (savedSchemesRaw) {
             try { savedSchemes = JSON.parse(savedSchemesRaw); } catch(e) {}
         }
         
         const isAlreadySaved = savedSchemes.some(s => s.name === schemeObj.name);
         if (!isAlreadySaved) {
             savedSchemes.push(schemeObj);
             localStorage.setItem('savedSchemes', JSON.stringify(savedSchemes));
         }
         
         applyBtn.innerText = typeof window.t === 'function' ? window.t('✓ Saved!') : '✓ Saved!';
         applyBtn.style.backgroundColor = '#16a34a';
         applyBtn.style.color = '#fff';
         applyBtn.disabled = true;
     });
  }

  // Prevent background scrolling while modal is open
  document.body.style.overflow = 'hidden';

  // Trigger animation next frame
  requestAnimationFrame(() => {
    modalOverlay.classList.add('active');
  });
};

window.closeModal = function() {
  const modal = document.getElementById('scheme-details-modal');
  if (modal) {
    modal.classList.remove('active');
    setTimeout(() => {
      modal.remove();
      // Restore scrolling
      document.body.style.overflow = '';
    }, 300); // Wait for transition
  }
};
