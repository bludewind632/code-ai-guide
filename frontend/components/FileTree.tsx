'use client';

import { useState } from 'react';
import { VscChevronRight } from 'react-icons/vsc';
import { getFileIcon, getDirIcon } from './fileIcons';

type TreeNode = {
  name: string;
  path: string;
  type: 'dir' | 'file';
  children?: TreeNode[];
};

export default function FileTree({
  nodes,
  onSelect,
  annotations,
}: {
  nodes: TreeNode[];
  onSelect: (path: string) => void;
  annotations?: Record<string, string>;
}) {
  return (
    <div className="tree-container">
      {nodes.map((node) => (
        <TreeNodeItem key={node.path} node={node} onSelect={onSelect} annotations={annotations} />
      ))}
    </div>
  );
}

function TreeNodeItem({
  node,
  onSelect,
  annotations,
  depth = 0,
}: {
  node: TreeNode;
  onSelect: (path: string) => void;
  annotations?: Record<string, string>;
  depth?: number;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const hasChildren = node.type === 'dir' && node.children && node.children.length > 0;

  if (node.type === 'dir') {
    const { icon: DirIcon, color: dirColor } = getDirIcon(node.name);
    return (
      <div className="tree-node">
        <button
          className={`tree-dir-btn ${hasChildren ? 'has-children' : ''}`}
          onClick={() => hasChildren && setCollapsed(!collapsed)}
          style={{ paddingLeft: depth * 14 }}
        >
          <VscChevronRight
            size={14}
            className={`tree-chevron ${!collapsed && hasChildren ? 'rotated' : ''} ${!hasChildren ? 'hidden' : ''}`}
          />
          <DirIcon size={16} style={{ marginRight: 6, flexShrink: 0, color: dirColor }} />
          <span className="tree-dir-name">{node.name}</span>
        </button>
        {!collapsed && hasChildren && (
          <div className="tree-children">
            {node.children!.map((child) => (
              <TreeNodeItem key={child.path} node={child} onSelect={onSelect} annotations={annotations} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  }

  const { icon: FileIcon, color: iconColor } = getFileIcon(node.name);
  const anno = annotations?.[node.path];

  return (
    <div className="tree-node">
      <button
        className="tree-file"
        onClick={() => onSelect(node.path)}
        style={{ paddingLeft: depth * 14 + 20 }}
      >
        <FileIcon
          size={16}
          style={{ marginRight: 6, verticalAlign: 'middle', flexShrink: 0, color: iconColor }}
        />
        {node.name}
      </button>
      {anno && <span className="tree-file-anno"># {anno}</span>}
    </div>
  );
}
