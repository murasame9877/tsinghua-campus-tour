const fs = require('fs');
let html = fs.readFileSync('E:/学习/校园讲解/index.html', 'utf-8');

// Replace image: "" with image: "images/[id].jpg"
// Match each building entry and find its id, then replace the image field
const lines = html.split('\n');
const result = [];
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  // Track the current building id
  const idMatch = line.match(/id:\s*"(\w+)"/);
  if (idMatch) {
    currentId = idMatch[1];
  }
  // Replace empty image fields
  if (line.match(/image:\s*""/) && currentId) {
    result.push(line.replace('image: ""', 'image: "images/' + currentId + '.jpg"'));
  } else {
    result.push(line);
  }
}
fs.writeFileSync('E:/学习/校园讲解/index.html', result.join('\n'));
console.log('Done. Updated image paths.');
