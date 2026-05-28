import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const ffprobeStatic = require('ffprobe-static');
console.log('ffprobe path:', ffprobeStatic.path);
