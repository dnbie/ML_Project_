import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './ChatInterface.css';

const API_URL = 'http://localhost:8000';

function ChatInterface({ documentInfo, onReset }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        question: input,
        top_k: 4,
        model: 'gpt-4o-mini',
        temperature: 0.2
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        chunks: response.data.chunks
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || 'Failed to get response'}`,
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-card">
        <div className="chat-header">
          <div className="header-info">
            <h2>💬 Chat with Your Documents</h2>
            <div className="doc-info">
              <span>📁 {documentInfo.files.length} file(s) loaded</span>
              <span>📊 {documentInfo.chunks} chunks</span>
            </div>
          </div>
          <button className="reset-button" onClick={onReset}>
            Upload New Files
          </button>
        </div>

        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h3>👋 Welcome!</h3>
              <p>Ask me anything about your uploaded documents.</p>
              <div className="suggestions">
                <button onClick={() => setInput('What is this document about?')}>
                  What is this document about?
                </button>
                <button onClick={() => setInput('Summarize the key points')}>
                  Summarize the key points
                </button>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
                {message.chunks && message.chunks.length > 0 && (
                  <details className="chunks-details">
                    <summary>View source chunks ({message.chunks.length})</summary>
                    {message.chunks.map((chunk, idx) => (
                      <div key={idx} className="chunk">
                        <strong>Chunk {chunk.index}:</strong>
                        <p>{chunk.content}</p>
                      </div>
                    ))}
                  </details>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content loading">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your documents..."
            rows="2"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="send-button"
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
