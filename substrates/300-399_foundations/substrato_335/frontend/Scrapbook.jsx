// Scrapbook.jsx — Componente React do Feed do Orkut 2.0
import React, { useState } from 'react';
import { InlineMath } from 'react-katex';
import 'katex/dist/katex.min.css';

const Scrapbook = ({ onScrapSubmit }) => {
  const [scrapText, setScrapText] = useState('');
  const [previewLatex, setPreviewLatex] = useState('');

  const handleScrap = () => {
    onScrapSubmit({ text: scrapText, rendered: previewLatex });
    setScrapText('');
  };

  const handleTextChange = (e) => {
    const text = e.target.value;
    setScrapText(text);
    // Simples parser para preview de LaTeX inline
    const latexMatch = text.match(/\$([^$]+)\$/g);
    if (latexMatch) {
      setPreviewLatex(latexMatch.join(' '));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4 border-l-4" style={{ borderColor: '#6A5ACD' }}>
      <textarea
        value={scrapText}
        onChange={handleTextChange}
        placeholder="No que você está pensando, pesquisador? (Use $...$ para LaTeX)"
        className="w-full h-24 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
        style={{ fontFamily: 'Inter, sans-serif' }}
      />
      {previewLatex && (
        <div className="my-2 p-2 bg-gray-100 rounded">
          <InlineMath math={previewLatex} />
        </div>
      )}
      <button
        onClick={handleScrap}
        className="mt-2 px-6 py-2 rounded-full text-white font-semibold"
        style={{ backgroundColor: '#6A5ACD' }}
      >
        Scrap!
      </button>
    </div>
  );
};

export default Scrapbook;
