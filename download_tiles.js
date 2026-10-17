const https = require('https');
const fs = require('fs');
const path = require('path');

const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const OUT_DIR = 'tiles';

const tiles = JSON.parse(fs.readFileSync('tile_list.json', 'utf-8'));
let done = 0, skipped = 0, failed = 0;

function download(tile) {
  return new Promise((resolve) => {
    const dir = path.join(OUT_DIR, String(tile.z), String(tile.x));
    const file = path.join(dir, tile.y + '.png');

    // Skip if already exists
    if (fs.existsSync(file)) {
      skipped++;
      resolve();
      return;
    }

    fs.mkdirSync(dir, { recursive: true });

    const url = TILE_URL.replace('{z}', tile.z).replace('{x}', tile.x).replace('{y}', tile.y);
    const req = https.get(url, {
      headers: { 'User-Agent': 'TsinghuaCampusMap/1.0 (educational use)' },
      timeout: 10000
    }, (res) => {
      if (res.statusCode === 200) {
        const ws = fs.createWriteStream(file);
        res.pipe(ws);
        ws.on('finish', () => {
          done++;
          if (done % 50 === 0) process.stderr.write(`\r  ${done}/${tiles.length} downloaded, ${skipped} skipped...`);
          resolve();
        });
      } else {
        failed++;
        resolve();
      }
    });
    req.on('error', () => { failed++; resolve(); });
    req.on('timeout', () => { req.destroy(); failed++; resolve(); });
  });
}

async function main() {
  console.log(`Downloading ${tiles.length} tiles...`);
  for (let i = 0; i < tiles.length; i++) {
    await download(tiles[i]);
    // Rate limit: 200ms between requests
    await new Promise(r => setTimeout(r, 200));
  }
  console.log(`\nDone! Downloaded: ${done}, Skipped: ${skipped}, Failed: ${failed}`);
}

main();
