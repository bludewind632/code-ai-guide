import {
  SiPython, SiTypescript, SiJavascript, SiReact, SiHtml5, SiCss3,
  SiJson, SiMarkdown, SiDocker, SiGit, SiYaml, SiGnubash,
  SiRust, SiGo, SiSwift, SiKotlin, SiRuby,
  SiNginx, SiPostgresql, SiMysql, SiRedis, SiMongodb,
  SiSvg, SiNextdotjs, SiVuedotjs, SiNodedotjs, SiExpress, SiFastapi,
  SiDjango, SiFlask, SiGraphql, SiPrisma, SiTailwindcss, SiSass,
  SiWebpack, SiVite, SiEslint, SiPrettier, SiJest, SiCypress,
  SiTerraform, SiKubernetes, SiGithubactions, SiJenkins, SiNpm,
} from 'react-icons/si';
import {
  FaJava, FaPhp, FaLaravel, FaReact, FaCss3,
  FaDocker, FaPython, FaNodeJs, FaGitAlt, FaFolder, FaFolderOpen,
  FaMarkdown, FaLock, FaCog, FaDatabase, FaCode,
  FaFileAlt, FaFileImage, FaFilePdf, FaFileArchive, FaFileExcel,
  FaFileCode, FaFileCsv, FaFileAudio, FaFileVideo, FaFileWord,
} from 'react-icons/fa';
import {
  IoLogoJavascript, IoLogoCss3, IoLogoHtml5, IoLogoReact,
  IoLogoNodejs, IoLogoVue, IoLogoAngular,
} from 'react-icons/io5';
import { VscFile, VscFolder, VscFolderOpened } from 'react-icons/vsc';
import { type IconType } from 'react-icons';

// ═════════════════════════════════════════════════════════════
// 类型定义
// ═════════════════════════════════════════════════════════════

type FileIconEntry = {
  icon: IconType;
  color: string;
};

// ═════════════════════════════════════════════════════════════
// 目录图标 —— 根据目录名称返回不同颜色
// ═════════════════════════════════════════════════════════════

const DIR_COLORS: Record<string, string> = {
  src: '#60a5fa',        // 蓝
  app: '#818cf8',        // 靛蓝
  components: '#a78bfa', // 紫
  pages: '#f472b6',      // 粉
  routes: '#22d3ee',     // 青
  services: '#34d399',   // 翠绿
  utils: '#fbbf24',      // 琥珀
  lib: '#fb923c',        // 橙
  config: '#94a3b8',     // 灰
  public: '#f87171',     // 红
  assets: '#e879f9',     // 紫红
  styles: '#c084fc',     // 淡紫
  tests: '#4ade80',      // 绿
  docs: '#2dd4bf',       // 青绿
  scripts: '#facc15',    // 黄
  data: '#a3e635',       // 黄绿
  models: '#38bdf8',     // 天蓝
  hooks: '#c084fc',      // 淡紫
  types: '#60a5fa',      // 蓝
  api: '#f87171',        // 红
  node_modules: '#9ca3af',
  '.git': '#f87171',
  '.github': '#111827',
};

export function getDirIcon(folderName: string): { icon: IconType; color: string } {
  const base = folderName.toLowerCase();
  const color = DIR_COLORS[base] || '#dcb67a';
  return { icon: VscFolder, color };
}

export function getDirOpenIcon(folderName: string): { icon: IconType; color: string } {
  const base = folderName.toLowerCase();
  const color = DIR_COLORS[base] || '#dcb67a';
  return { icon: VscFolderOpened, color };
}

// ═════════════════════════════════════════════════════════════
// 文件图标 —— 根据扩展名/文件名匹配
// ═════════════════════════════════════════════════════════════

const EXT_ICONS: Record<string, FileIconEntry> = {
  // ── 语言文件 ──
  py:       { icon: FaPython,     color: '#3776AB' },
  tsx:      { icon: IoLogoReact,  color: '#61DAFB' },
  ts:       { icon: SiTypescript, color: '#3178C6' },
  jsx:      { icon: IoLogoReact,  color: '#61DAFB' },
  js:       { icon: IoLogoJavascript, color: '#F7DF1E' },
  mjs:      { icon: IoLogoJavascript, color: '#F7DF1E' },
  cjs:      { icon: IoLogoJavascript, color: '#F7DF1E' },
  java:     { icon: FaJava,       color: '#ED8B00' },
  go:       { icon: SiGo,         color: '#00ADD8' },
  rs:       { icon: SiRust,       color: '#DEA584' },
  rb:       { icon: SiRuby,       color: '#CC342D' },
  php:      { icon: FaPhp,        color: '#777BB4' },
  swift:    { icon: SiSwift,      color: '#F05138' },
  kt:       { icon: SiKotlin,     color: '#7F52FF' },
  kts:      { icon: SiKotlin,     color: '#7F52FF' },
  c:        { icon: FaCode,       color: '#555555' },
  h:        { icon: FaCode,       color: '#555555' },
  cpp:      { icon: FaCode,       color: '#6295CB' },
  cc:       { icon: FaCode,       color: '#6295CB' },
  cxx:      { icon: FaCode,       color: '#6295CB' },
  hpp:      { icon: FaCode,       color: '#6295CB' },

  // ── 前端 ──
  css:      { icon: FaCss3,       color: '#1572B6' },
  scss:     { icon: SiSass,       color: '#CC6699' },
  sass:     { icon: SiSass,       color: '#CC6699' },
  less:     { icon: FaCss3,       color: '#1D365D' },
  html:     { icon: IoLogoHtml5,  color: '#E34F26' },
  htm:      { icon: IoLogoHtml5,  color: '#E34F26' },
  xml:      { icon: FaFileCode,   color: '#E34F26' },
  svg:      { icon: SiSvg,        color: '#FFB13B' },
  vue:      { icon: IoLogoVue,    color: '#42B883' },

  // ── 数据 & 配置 ──
  json:     { icon: SiJson,       color: '#F59E0B' },
  yml:      { icon: SiYaml,       color: '#CB171E' },
  yaml:     { icon: SiYaml,       color: '#CB171E' },
  toml:     { icon: FaCog,        color: '#9C4221' },
  ini:      { icon: FaCog,        color: '#6B7280' },
  cfg:      { icon: FaCog,        color: '#6B7280' },
  conf:     { icon: FaCog,        color: '#6B7280' },
  env:      { icon: FaLock,       color: '#F59E0B' },

  // ── 数据库 ──
  sql:      { icon: SiPostgresql, color: '#336791' },
  prisma:   { icon: SiPrisma,     color: '#2D3748' },
  graphql:  { icon: SiGraphql,    color: '#E10098' },
  gql:      { icon: SiGraphql,    color: '#E10098' },

  // ── 文档 ──
  md:       { icon: FaMarkdown,   color: '#374151' },
  mdx:      { icon: FaMarkdown,   color: '#374151' },
  txt:      { icon: FaFileAlt,    color: '#6B7280' },
  pdf:      { icon: FaFilePdf,    color: '#EF4444' },
  csv:      { icon: FaFileCsv,    color: '#10B981' },

  // ── Shell & 脚本 ──
  sh:       { icon: SiGnubash,    color: '#4EAA25' },
  bash:     { icon: SiGnubash,    color: '#4EAA25' },
  zsh:      { icon: SiGnubash,    color: '#4EAA25' },
  fish:     { icon: SiGnubash,    color: '#4EAA25' },
  ps1:      { icon: SiGnubash,    color: '#5391FE' },

  // ── 图片 & 媒体 ──
  png:      { icon: FaFileImage,  color: '#EC4899' },
  jpg:      { icon: FaFileImage,  color: '#EC4899' },
  jpeg:     { icon: FaFileImage,  color: '#EC4899' },
  gif:      { icon: FaFileImage,  color: '#EC4899' },
  webp:     { icon: FaFileImage,  color: '#EC4899' },
  ico:      { icon: FaFileImage,  color: '#EC4899' },
  mp3:      { icon: FaFileAudio,  color: '#8B5CF6' },
  wav:      { icon: FaFileAudio,  color: '#8B5CF6' },
  mp4:      { icon: FaFileVideo,  color: '#EF4444' },
  mov:      { icon: FaFileVideo,  color: '#EF4444' },

  // ── 压缩 ──
  zip:      { icon: FaFileArchive, color: '#9CA3AF' },
  tar:      { icon: FaFileArchive, color: '#9CA3AF' },
  gz:       { icon: FaFileArchive, color: '#9CA3AF' },
  rar:      { icon: FaFileArchive, color: '#9CA3AF' },
  '7z':     { icon: FaFileArchive, color: '#9CA3AF' },

  // ── lock 文件 ──
  lock:     { icon: FaLock,       color: '#6B7280' },
};

// ── 完整文件名匹配（优先级高于扩展名）──
const NAME_ICONS: Record<string, FileIconEntry> = {
  // Docker
  dockerfile:          { icon: SiDocker,     color: '#2496ED' },
  'docker-compose.yml':  { icon: SiDocker,   color: '#2496ED' },
  'docker-compose.yaml': { icon: SiDocker,   color: '#2496ED' },
  // Git
  '.gitignore':        { icon: FaGitAlt,     color: '#F05032' },
  '.gitattributes':    { icon: FaGitAlt,     color: '#F05032' },
  // Node
  'package.json':      { icon: SiNpm,        color: '#CB3837' },
  'package-lock.json': { icon: SiNpm,        color: '#CB3837' },
  // 配置
  'makefile':          { icon: SiGnubash,    color: '#4EAA25' },
  'readme.md':         { icon: FaMarkdown,   color: '#2563EB' },
  'nginx.conf':        { icon: SiNginx,      color: '#009639' },
  // 框架配置
  'tailwind.config.js':  { icon: SiTailwindcss, color: '#06B6D4' },
  'tailwind.config.ts':  { icon: SiTailwindcss, color: '#06B6D4' },
  'vite.config.ts':      { icon: SiVite,        color: '#646CFF' },
  'vite.config.js':      { icon: SiVite,        color: '#646CFF' },
  'next.config.js':      { icon: SiNextdotjs,   color: '#111827' },
  'next.config.ts':      { icon: SiNextdotjs,   color: '#111827' },
  'webpack.config.js':   { icon: SiWebpack,     color: '#8DD6F9' },
  '.eslintrc.js':        { icon: SiEslint,      color: '#4B32C3' },
  '.eslintrc.json':      { icon: SiEslint,      color: '#4B32C3' },
  '.prettierrc':         { icon: SiPrettier,    color: '#F7B93E' },
  'tsconfig.json':       { icon: SiTypescript,  color: '#3178C6' },
  // CI/CD
  '.github/workflows/':  { icon: SiGithubactions, color: '#2088FF' },
  'jenkinsfile':         { icon: SiJenkins,     color: '#D24939' },
  // Terraform / K8s
  'terraform':         { icon: SiTerraform,  color: '#7B42BC' },
  'kubernetes':        { icon: SiKubernetes, color: '#326CE5' },
};

// ═════════════════════════════════════════════════════════════
// 导出函数
// ═════════════════════════════════════════════════════════════

export function getFileIcon(fileName: string): { icon: IconType; color: string } {
  const base = fileName.toLowerCase();
  const ext = fileName.split('.').pop()?.toLowerCase() ?? '';

  // 1) 完整文件名匹配
  if (NAME_ICONS[base]) return NAME_ICONS[base];

  // 2) 扩展名匹配
  if (EXT_ICONS[ext]) return EXT_ICONS[ext];

  // 3) 默认
  return { icon: FaFileCode, color: '#6B7280' };
}

export function getFileColor(fileName: string): string {
  return getFileIcon(fileName).color;
}
