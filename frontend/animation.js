// Day 13 - step-by-step search animation driven by requestAnimationFrame.
// Plays the `visited_nodes` array in order. Speed is read on every frame, so the
// slider can be changed while the animation is running.
class ExploreAnimator {
  constructor({ onVisit, getSpeed, baseNodesPerSecond = 30 }) {
    this.onVisit = onVisit;
    this.getSpeed = getSpeed;
    this.base = baseNodesPerSecond;
    this.token = 0;
    this.playing = false;
  }

  start(sequence, onDone) {
    this.stop();
    const token = ++this.token;
    this.playing = true;
    this._seq = sequence;
    this._idx = 0;
    this._onDone = onDone;
    let last = null;
    let acc = 0;

    const frame = (ts) => {
      if (token !== this.token) return;                 // cancelled or replaced
      if (last === null) last = ts;
      acc += ((ts - last) / 1000) * this.base * this.getSpeed();
      last = ts;
      while (acc >= 1 && this._idx < sequence.length) {
        this.onVisit(sequence[this._idx++], this._idx === sequence.length);
        acc -= 1;
      }
      if (this._idx < sequence.length) {
        this._raf = requestAnimationFrame(frame);
      } else {
        this._finish(token);
      }
    };

    if (sequence.length === 0) { this._finish(token); return; }
    this._raf = requestAnimationFrame(frame);
  }

  skip() {
    if (!this.playing) return;
    const token = this.token;
    cancelAnimationFrame(this._raf);
    while (this._idx < this._seq.length) {
      this.onVisit(this._seq[this._idx++], this._idx === this._seq.length);
    }
    this._finish(token);
  }

  stop() {
    this.token++;
    this.playing = false;
    cancelAnimationFrame(this._raf);
  }

  _finish(token) {
    if (token !== this.token) return;
    this.playing = false;
    const cb = this._onDone;
    this._onDone = null;
    if (cb) cb();
  }
}
