import { useState } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentModel, setCurrentModel] = useState('gpt-3.5-turbo');
  const [inputValue, setInputValue] = useState('');
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  


  const handleModelChange = (model) => {
    fetch('http://localhost:8000/switch_model', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_name: model
      })
    })
    .then(response => {
      if (response.ok) {
        setCurrentModel(model);
      }
    })
    .catch(error => console.error('Error:', error));
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: 'user'
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    
    fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: inputValue,
        model: currentModel
      })
    })
    .then(response => response.json())
    .then(data => {
      const aiMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: 'ai'
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    })
    .catch(error => {
      console.error('Error:', error);
      setIsTyping(false);
    });
  };

  return (
    <div className="app">
      <div className="history-sidebar">
        <div className="conversation-list">
          {conversations.map(conv => (
            <div 
              key={conv.id} 
              className={`conversation-item ${currentConversationId === conv.id ? 'active' : ''}`}
              onClick={() => setCurrentConversationId(conv.id)}
            >
              {conv.title || `Conversation ${conv.id}`}
            </div>
          ))}
          <button 
            className="new-conversation" 
            onClick={() => {
              const newId = Date.now();
              setCurrentConversationId(newId);
              setConversations([...conversations, {id: newId, title: 'New Conversation'}]);
              setMessages([]);
            }}
          >
            + New
          </button>
        </div>
      </div>
      <div className="chat-container">
        <div className="messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}`}>
              {message.text}
            </div>
          ))}
          {isTyping && (
            <div className="message ai typing">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          )}
        </div>
        
        <div className="input-area">
          <input 
            type="text" 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type a message..."
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <button onClick={handleSendMessage}>Send</button>
        </div>
        
        <div className="model-selector">
          <select 
            value={currentModel}
            onChange={(e) => handleModelChange(e.target.value)}
            className="model-dropdown"
          >
            <option value="azure">Azure OpenAI</option>
            <option value="deepseek">DeepSeek</option>
          </select>
        </div>
      </div>
    </div>
  )
}

export default App
