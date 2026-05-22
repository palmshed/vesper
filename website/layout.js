class FaviconManager {
  constructor() {
    this.faviconSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="14" y="20" width="72" height="26" rx="8" fill="#f5f5f0"/>
  <rect x="14" y="54" width="72" height="26" rx="8" fill="#f5f5f0"/>
  <circle cx="30" cy="33" r="5" fill="#080909"/>
  <circle cx="30" cy="67" r="5" fill="#080909"/>
</svg>`;
  }

  init() {
    this.setFavicon();
  }

  setFavicon() {
    let favicon = document.querySelector('link[rel="icon"]');

    if (!favicon) {
      favicon = document.createElement('link');
      favicon.rel = 'icon';
      favicon.type = 'image/svg+xml';
      document.head.appendChild(favicon);
    }

    const svgBlob = new Blob([this.faviconSVG], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(svgBlob);
    favicon.href = url;
  }
}

// Set favicon immediately before page renders
(function() {
  var fav = document.createElement('link');
  fav.rel = 'icon';
  fav.type = 'image/svg+xml';
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="14" y="20" width="72" height="26" rx="8" fill="#f5f5f0"/><rect x="14" y="54" width="72" height="26" rx="8" fill="#f5f5f0"/><circle cx="30" cy="33" r="5" fill="#080909"/><circle cx="30" cy="67" r="5" fill="#080909"/></svg>';
  fav.href = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  document.head.appendChild(fav);
})();

class ResponsiveLayout {
  constructor() {
    this.init();
    window.addEventListener('resize', () => this.handleResize());
    window.addEventListener('orientationchange', () => this.handleOrientationChange());
  }

  init() {
    this.setViewportHeight();
    this.adjustContentForScreen();
  }

  setViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
  }

  adjustContentForScreen() {
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
    const isDesktop = window.innerWidth > 1024;

    document.body.dataset.screenSize = isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop';

    const main = document.querySelector('main');
    const footer = document.querySelector('footer');

    if (main) {
      main.style.minHeight = this.calculateMainMinHeight();
    }

    if (footer) {
      footer.style.marginTop = 'auto';
    }

    this.adjustTableOverflow();
    this.adjustSectionGrid();
  }

  calculateMainMinHeight() {
    const navHeight = 80;
    const footerHeight = 150;
    const availableHeight = `calc(100vh - ${navHeight}px - ${footerHeight}px)`;
    return availableHeight;
  }

  adjustTableOverflow() {
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
      const wrapper = table.parentElement;
      if (window.innerWidth <= 768) {
        if (!wrapper.classList.contains('table-wrapper')) {
          const tableWrapper = document.createElement('div');
          tableWrapper.className = 'table-wrapper';
          table.parentNode.insertBefore(tableWrapper, table);
          tableWrapper.appendChild(table);
          tableWrapper.style.overflowX = 'auto';
          tableWrapper.style.webkitOverflowScrolling = 'touch';
        }
      }
    });
  }

  adjustSectionGrid() {
    const grids = document.querySelectorAll('.section-grid');
    grids.forEach(grid => {
      if (window.innerWidth <= 768) {
        grid.style.gridTemplateColumns = '1fr';
        grid.style.maxWidth = '100%';
      } else if (window.innerWidth <= 1024) {
        grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        grid.style.maxWidth = '100%';
      } else {
        const maxCols = grid.classList.contains('max-2') ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)';
        grid.style.gridTemplateColumns = maxCols;
        grid.style.maxWidth = '1200px';
      }
    });
  }

  handleResize() {
    this.setViewportHeight();
    this.adjustContentForScreen();
  }

  handleOrientationChange() {
    setTimeout(() => {
      this.setViewportHeight();
      this.adjustContentForScreen();
    }, 100);
  }
}

class LayoutManager {
  constructor() {
    this.faviconManager = new FaviconManager();
    this.responsiveLayout = null;
    this.init();
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    this.responsiveLayout = new ResponsiveLayout();
    this.setupGlobalStyles();
  }

  setupGlobalStyles() {
    const style = document.createElement('style');
    style.textContent = `
      :root {
        --vh: 1vh;
        --vh-full: 100vh;
      }

      body {
        min-height: 100vh;
        min-height: calc(var(--vh) * 100);
        display: flex;
        flex-direction: column;
      }

      body > * {
        flex-shrink: 0;
      }

      main {
        flex: 1;
        width: 100%;
        max-width: 1400px;
        margin: 0 auto;
        box-sizing: border-box;
      }

      .table-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin: 0 -5%;
        padding: 0 5%;
      }

      @media (max-width: 768px) {
        .section-grid {
          grid-template-columns: 1fr !important;
          max-width: 100% !important;
        }

        .section-grid.max-2 {
          grid-template-columns: 1fr !important;
        }

        main {
          padding: 40px 5%;
        }

        pre {
          font-size: 0.75rem;
          padding: 12px;
          overflow-x: auto;
        }

        .table td {
          padding-left: 80px !important;
        }
      }

      @media (max-width: 480px) {
        .section-grid {
          grid-template-columns: 1fr !important;
        }

        .hero h1 {
          font-size: 2rem !important;
        }

        .table td {
          padding-left: 0 !important;
          display: block !important;
          text-align: left !important;
        }

        .table td::before {
          display: block !important;
          position: static !important;
          width: auto !important;
          margin-bottom: 4px;
        }
      }
    `;
    document.head.appendChild(style);
  }
}

new LayoutManager();
