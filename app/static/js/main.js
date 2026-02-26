/**
 * Jewelry Store — Public JavaScript
 * Handles: qty stepper, scroll-triggered effects, mobile nav tweaks.
 */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Auto-dismiss flash alerts after 4 s ─────────────────────────── */
  document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });

  /* ── Sticky navbar shadow on scroll ─────────────────────────────── */
  const navbar = document.querySelector('.site-navbar');
  if (navbar) {
    const onScroll = () => {
      navbar.style.boxShadow = window.scrollY > 10
        ? '0 2px 20px rgba(0,0,0,.10)'
        : 'none';
    };
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ── Smooth anchor scroll for hero CTA ──────────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ── Product card "Add to Cart" loading state ────────────────────── */
  document.querySelectorAll('.product-cta form').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = this.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding…';
      }
    });
  });

  /* ── Cart quantity direct input validation ───────────────────────── */
  document.querySelectorAll('.qty-input').forEach(input => {
    input.addEventListener('change', function () {
      const min = parseInt(this.min) || 1;
      const max = parseInt(this.max) || 999;
      let val = parseInt(this.value) || min;
      this.value = Math.min(max, Math.max(min, val));
    });
  });

  /* ── Image preview on admin product upload ───────────────────────── */
  // (also works on public pages if ever needed)
  document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
    input.addEventListener('change', function () {
      const preview = this.closest('.admin-card-body')?.querySelector('.img-preview');
      if (preview && this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => { preview.src = e.target.result; };
        reader.readAsDataURL(this.files[0]);
      }
    });
  });

});
