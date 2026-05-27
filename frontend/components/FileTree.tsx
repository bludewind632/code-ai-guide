'use client';

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
        <Node key={node.path} node={node} onSelect={onSelect} annotations={annotations} />
      ))}
    </div>
  );
}

function Node({
  node,
  onSelect,
  annotations,
}: {
  node: TreeNode;
  onSelect: (path: string) => void;
  annotations?: Record<string, string>;
}) {
  if (node.type === 'dir') {
    return (
      <div className="tree-node">
        <div className="tree-dir">📁 {node.name}</div>
        <div style={{ paddingLeft: 14 }}>
          {node.children?.map((child) => (
            <Node key={child.path} node={child} onSelect={onSelect} annotations={annotations} />
          ))}
        </div>
      </div>
    );
  }

  const anno = annotations?.[node.path];
  return (
    <div className="tree-node">
      <button className="tree-file" onClick={() => onSelect(node.path)}>
        📄 {node.name}
      </button>
      {anno && <span className="tree-file-anno"># {anno}</span>}
    </div>
  );
}
