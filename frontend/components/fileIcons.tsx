import {
  SiPython,
  SiTypescript,
  SiJavascript,
  SiReact,
  SiHtml5,
  SiJson,
  SiMarkdown,
  SiDocker,
  SiGit,
  SiYaml,
  SiGnubash,
  SiRust,
  SiGo,
  SiSwift,
  SiKotlin,
  SiRuby,
  SiSass,
  SiTailwindcss,
  SiNginx,
  SiPostgresql,
  SiSvg,
  SiNpm,
} from 'react-icons/si';
import { VscFolder, VscFile } from 'react-icons/vsc';
import { type IconType } from 'react-icons';

// 目录图标
export function getDirIcon(): IconType {
  return VscFolder;
}

// 根据文件名/扩展名返回对应图标
export function getFileIcon(fileName: string): IconType {
  const ext = fileName.split('.').pop()?.toLowerCase() ?? '';
  const base = fileName.toLowerCase();

  // 特殊文件名匹配（无扩展名）
  if (base === 'dockerfile') return SiDocker;
  if (base === 'docker-compose.yml' || base === 'docker-compose.yaml') return SiDocker;
  if (base === '.gitignore') return SiGit;
  if (base === '.env' || base.startsWith('.env.')) return VscFile;
  if (base === 'makefile') return SiGnubash;
  if (base === 'readme.md') return SiMarkdown;
  if (base === 'nginx.conf') return SiNginx;
  if (base === 'tailwind.config.js' || base === 'tailwind.config.ts') return SiTailwindcss;

  // 扩展名匹配
  switch (ext) {
    case 'py':
      return SiPython;
    case 'tsx':
      return SiReact;
    case 'ts':
      return SiTypescript;
    case 'jsx':
      return SiReact;
    case 'js':
    case 'mjs':
    case 'cjs':
      return SiJavascript;
    case 'css':
    case 'scss':
    case 'sass':
      return SiSass;
    case 'html':
    case 'htm':
    case 'xml':
      return SiHtml5;
    case 'json':
      return SiJson;
    case 'md':
    case 'mdx':
      return SiMarkdown;
    case 'yml':
    case 'yaml':
      return SiYaml;
    case 'sh':
    case 'bash':
    case 'zsh':
      return SiGnubash;
    case 'rs':
      return SiRust;
    case 'go':
      return SiGo;
    case 'cpp':
    case 'cc':
    case 'cxx':
    case 'hpp':
      return SiTypescript;
    case 'c':
    case 'h':
      return SiTypescript;
    case 'swift':
      return SiSwift;
    case 'kt':
    case 'kts':
      return SiKotlin;
    case 'rb':
      return SiRuby;
    case 'svg':
      return SiSvg;
    case 'sql':
      return SiPostgresql;
    case 'java':
      return SiTypescript;
    case 'toml':
    case 'ini':
    case 'cfg':
    case 'conf':
    case 'lock':
    case 'log':
    case 'txt':
    default:
      return VscFile;
  }
}

// 获取图标颜色（可选，扩展名对应的品牌色）
export function getFileColor(fileName: string): string | undefined {
  const ext = fileName.split('.').pop()?.toLowerCase() ?? '';
  const base = fileName.toLowerCase();

  if (base === 'dockerfile' || base.startsWith('docker-compose')) return '#2496ED';

  switch (ext) {
    case 'py': return '#3776AB';
    case 'tsx':
    case 'ts': return '#3178C6';
    case 'jsx':
    case 'js':
    case 'mjs':
    case 'cjs': return '#F7DF1E';
    case 'css':
    case 'scss':
    case 'sass': return '#CC6699';
    case 'html':
    case 'htm': return '#E34F26';
    case 'json': return '#000000';
    case 'md':
    case 'mdx': return '#000000';
    case 'rs': return '#000000';
    case 'go': return '#00ADD8';
    case 'java': return '#ED8B00';
    case 'kt':
    case 'kts': return '#7F52FF';
    case 'swift': return '#F05138';
    case 'rb': return '#CC342D';
    case 'sh':
    case 'bash': return '#4EAA25';
    default: return undefined;
  }
}
