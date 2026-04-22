class HomeParticleSystem {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.mouse = { clientX: window.innerWidth / 2, clientY: window.innerHeight / 2 };
    this.time = 0;
    this.isRunning = true;
    this.frameId = null;

    this.opts = {
      focalLength: options.focalLength || 800,
      cameraZ: options.cameraZ || 200,
      colors: options.colors || ['#4285F4', '#EA4335', '#FBBC04', '#34A853', '#A0C3FF'],
      waveFreq: options.waveFreq || 0.012,
      ...options, 
    };

    this.particles = [];
    this.gridCols = 70; 
    this.gridRows = 55; 

    this.init();
  }

  init() {
    this.resize();
    this._resizeHandler = () => this.resize();
    window.addEventListener('resize', this._resizeHandler);

    this.mouse = { clientX: this.w / 2, clientY: this.h / 2 };
    this.activeMouseX = this.w / 2;
    this.activeMouseY = this.h / 2;

    this._moveHandler = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.clientX = e.clientX - rect.left;
      this.mouse.clientY = e.clientY - rect.top;
    };
    document.addEventListener('mousemove', this._moveHandler);

    this.createMesh();
    this.animate();
  }

  resize() {
    const parent = this.canvas.parentElement || document.body;
    const rect = parent.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = rect.width;
    this.h = rect.height;

    this.cx = this.w / 2;
    this.cy = this.h / 2;
  }

  createMesh() {
    this.particles = [];
    const viewWidth = 3500;
    const viewDepth = 3000;
    const spacingX = viewWidth / this.gridCols;
    const spacingZ = viewDepth / this.gridRows;

    for (let z = 0; z < this.gridRows; z++) {
      for (let x = 0; x < this.gridCols; x++) {
        const px = -(viewWidth / 2) + (x * spacingX);
        const pz = z * spacingZ;
        const baseY = 250;
        const color = this.opts.colors[(x + z) % this.opts.colors.length];

        this.particles.push({
          x: px,
          z: pz,
          baseY: baseY,
          y: baseY,
          vy: 0,
          rippleOffset: 0,
          color: color,
          size: Math.random() * 1.5 + 1.0,
          projX: 0,
          projY: 0,
          scale: 1,
          alpha: 1
        });
      }
    }
  }

  hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(3)})`;
  }

  getParticle(x, z) {
    if (x < 0 || x >= this.gridCols || z < 0 || z >= this.gridRows) return null;
    return this.particles[z * this.gridCols + x];
  }

  getWaveHeight(x, z, time) {
    return Math.sin(x * 0.002 + time * 0.8) * 45
      + Math.cos(z * 0.003 - time * 1.2) * 35
      + Math.sin((x + z) * 0.0015 + time * 1.5) * 55;
  }

  // Wajib dijaga karena HTML manggil fungsi ini
  dropLetters(word) {
      console.log('Text dropped tapi disembunyikan untuk desain murni Karpet');
  }

  animate() {
    if (!this.isRunning) return;
    this.time += this.opts.waveFreq;

    this.ctx.clearRect(0, 0, this.w, this.h);

    this.activeMouseX += (this.mouse.clientX - this.activeMouseX) * 0.15;
    this.activeMouseY += (this.mouse.clientY - this.activeMouseY) * 0.15;

    // KALKULASI FISIKA WAVE & MAGNETIC REPULSION
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      const waveHeight = this.getWaveHeight(p.x, p.z, this.time);
      const naturalY = p.baseY + waveHeight;

      let z_proj = p.z + this.opts.cameraZ;
      let scale = this.opts.focalLength / z_proj;
      let rawProjX = this.cx + p.x * scale;
      let rawProjY = this.cy + naturalY * scale + (this.h * 0.25);

      const dx = rawProjX - this.mouse.clientX;
      const dy = rawProjY - this.mouse.clientY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      let targetRipple = 0;
      const repelRadius = 250;
      if (dist < repelRadius) {
        const force = Math.pow((repelRadius - dist) / repelRadius, 2);
        targetRipple = force * 220;
      }

      const spring = 0.06;
      const friction = 0.85;
      p.vy += (targetRipple - p.rippleOffset) * spring;
      p.vy *= friction;
      p.rippleOffset += p.vy;

      p.y = naturalY + p.rippleOffset;
      p.projX = this.cx + p.x * scale;
      p.projY = this.cy + p.y * scale + (this.h * 0.25);
      p.scale = scale;

      const maxZ = 3000;
      let alpha = 1 - (p.z / maxZ);
      const frontFadeDepth = 700;
      if (p.z < frontFadeDepth) {
        alpha *= Math.pow(p.z / frontFadeDepth, 1.2);
      }
      const absX = Math.abs(p.x);
      const viewWidthHalf = 3500 / 2;
      const sideFadeDist = viewWidthHalf - 800;
      if (absX > sideFadeDist) {
        alpha *= Math.max(0, 1 - (absX - sideFadeDist) / 800);
      }
      p.alpha = Math.max(0, Math.min(1, alpha));
    }

    // RENDERING THE NEURAL MESH
    for (let z = this.gridRows - 1; z >= 0; z--) {
      const centerIndex = Math.floor(this.gridCols / 2);
      const refParticle = this.getParticle(centerIndex, z);
      if (!refParticle || refParticle.alpha < 0.02) continue;

      this.ctx.globalCompositeOperation = 'source-over';
      this.ctx.lineWidth = 1.0;
      this.ctx.strokeStyle = `rgba(66, 133, 244, ${refParticle.alpha * 0.45})`;

      this.ctx.beginPath();
      for (let x = 0; x < this.gridCols; x++) {
        const p = this.getParticle(x, z);
        if (x < this.gridCols - 1) {
          const pRight = this.getParticle(x + 1, z);
          this.ctx.moveTo(p.projX, p.projY);
          this.ctx.lineTo(pRight.projX, pRight.projY);
        }
        if (z < this.gridRows - 1) {
          const pBottom = this.getParticle(x, z + 1);
          this.ctx.moveTo(p.projX, p.projY);
          this.ctx.lineTo(pBottom.projX, pBottom.projY);
        }
      }
      this.ctx.stroke();

      // Render Nodes
      this.ctx.globalCompositeOperation = 'source-over';
      for (let x = 0; x < this.gridCols; x++) {
        const p = this.getParticle(x, z);
        const finalAlpha = p.alpha * (0.6 + 0.4 * Math.sin(this.time * 2 + p.x));
        this.ctx.fillStyle = this.hexToRgba(p.color, finalAlpha);
        const nodeSize = p.size * p.scale * 3.5;
        this.ctx.beginPath();
        this.ctx.arc(p.projX, p.projY, nodeSize, 0, Math.PI * 2);
        this.ctx.fill();
        if (z < this.gridRows / 2) {
          this.ctx.shadowBlur = nodeSize * 2.5;
          this.ctx.shadowColor = this.ctx.fillStyle;
          this.ctx.fill();
          this.ctx.shadowBlur = 0;
        }
      }
    }

    this.frameId = requestAnimationFrame(() => this.animate());
  }

  destroy() {
    this.isRunning = false;
    if (this.frameId) cancelAnimationFrame(this.frameId);
    if (this._moveHandler) document.removeEventListener('mousemove', this._moveHandler);
    if (this._resizeHandler) window.removeEventListener('resize', this._resizeHandler);
  }
}

// ── Globals ──
const homeParticleSystems = {};

function initHomeParticles(canvasId, options = {}) {
  if (homeParticleSystems[canvasId]) {
    homeParticleSystems[canvasId].destroy();
  }
  homeParticleSystems[canvasId] = new HomeParticleSystem(canvasId, options);
  return homeParticleSystems[canvasId];
}

function destroyHomeParticles(canvasId) {
  if (homeParticleSystems[canvasId]) {
    homeParticleSystems[canvasId].destroy();
    delete homeParticleSystems[canvasId];
  }
}
