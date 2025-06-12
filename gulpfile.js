const { src, dest, series } = require('gulp');
const path = require('path');

function copyIcons() {
  // 拷贝所有节点下的 svg 图标到 dist 目录
  return src('nodes/**/*.svg')
    .pipe(dest('dist/nodes'));
}

exports.build = series(copyIcons);
exports['build:icons'] = copyIcons; 