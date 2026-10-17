import type { ReactNode } from "react";

function inline(text: string, compact = false): ReactNode[] {
  const pattern = /(\*\*[^*]+\*\*|__[^_]+__|\*[^*\n]+\*|_[^_\n]+_|`[^`]+`|\[[^\]]+\]\([^\s)]+\))/g;
  const parts = text.split(pattern);
  return parts.map((part, index) => {
    if (!part) return null;
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    const link = part.match(/^\[([^\]]+)\]\(([^\s)]+)\)$/);
    if (link) {
      if (compact) return <span className="md-link" key={index}>{link[1]}</span>;
      try {
        const url = new URL(link[2], window.location.href);
        if (["http:", "https:", "mailto:"].includes(url.protocol)) {
          return <a key={index} href={url.href} target="_blank" rel="noreferrer">{link[1]}</a>;
        }
      } catch {
        // Keep malformed or unsafe Markdown links as plain text.
      }
      return <span key={index}>{link[1]}</span>;
    }
    return <span key={index}>{part}</span>;
  });
}

function isListLine(line: string) {
  return /^\s*(?:[-+*]|\d+\.)\s+/.test(line);
}

export function Markdown({ text, compact = false }: { text: string; compact?: boolean }) {
  const lines = text.replace(/\r\n?/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index++; continue; }

    const fence = line.match(/^\s*```/);
    if (fence) {
      const code: string[] = [];
      index++;
      while (index < lines.length && !/^\s*```/.test(lines[index])) code.push(lines[index++]);
      if (index < lines.length) index++;
      blocks.push(compact
        ? <span className="md-code" key={blocks.length}>{code.join(" ")}</span>
        : <pre key={blocks.length}><code>{code.join("\n")}</code></pre>);
      continue;
    }

    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      blocks.push(compact
        ? <span className="md-heading" key={blocks.length}>{inline(heading[2], compact)}</span>
        : <h3 key={blocks.length}>{inline(heading[2], compact)}</h3>);
      index++;
      continue;
    }

    if (/^\s{0,3}(?:---+|___+|\*\*\*+)\s*$/.test(line)) {
      blocks.push(compact ? <br key={blocks.length} /> : <hr key={blocks.length} />);
      index++;
      continue;
    }

    if (/^\s*>/.test(line)) {
      const quote: string[] = [];
      while (index < lines.length && /^\s*>/.test(lines[index])) quote.push(lines[index++].replace(/^\s*>\s?/, ""));
      blocks.push(compact
        ? <span className="md-quote" key={blocks.length}>{inline(quote.join(" "), compact)}</span>
        : <blockquote key={blocks.length}>{inline(quote.join(" "), compact)}</blockquote>);
      continue;
    }

    if (isListLine(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items: string[] = [];
      while (index < lines.length && isListLine(lines[index])) {
        items.push(lines[index++].replace(/^\s*(?:[-+*]|\d+\.)\s+/, ""));
      }
      blocks.push(compact
        ? <span className="md-list" key={blocks.length}>{items.map((item, i) => <span className="md-list-item" key={i}>{ordered ? `${i + 1}. ` : "• "}{inline(item, compact)}</span>)}</span>
        : ordered
          ? <ol key={blocks.length}>{items.map((item, i) => <li key={i}>{inline(item, compact)}</li>)}</ol>
          : <ul key={blocks.length}>{items.map((item, i) => <li key={i}>{inline(item, compact)}</li>)}</ul>);
      continue;
    }

    const paragraph = [line.trim()];
    index++;
    while (index < lines.length && lines[index].trim() && !/^\s*(?:#{1,6}\s|>|```)/.test(lines[index]) && !isListLine(lines[index])) {
      paragraph.push(lines[index++].trim());
    }
    blocks.push(compact
      ? <span className="md-paragraph" key={blocks.length}>{inline(paragraph.join(" "), compact)}</span>
      : <p key={blocks.length}>{inline(paragraph.join(" "), compact)}</p>);
  }

  return compact ? <span className="markdown-compact">{blocks}</span> : <div className="markdown-body">{blocks}</div>;
}
