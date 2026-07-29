import React, { useState, useEffect, useRef } from 'react';
import { Grid, Key, Layers, Settings, Sun, Moon, Bell, ChevronDown, KeyRound, Mic, Send, Copy, Download, Plus, AlertTriangle, Trash2, Edit2, User, Menu, X, Headphones } from 'lucide-react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

function App() {
  // --- State ---
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [activeTab, setActiveTab] = useState('studio');
  const [activeSettingsTab, setActiveSettingsTab] = useState('api');
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth > 768);
  const [toastMessage, setToastMessage] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const chatEndRef = useRef(null);
  
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || 'user825');
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem('userEmail') || 'user825@gmail.com');

  const [apiKeys, setApiKeys] = useState(() => {
    try { return JSON.parse(localStorage.getItem('apiKeys')) || []; }
    catch { return []; }
  });
  const [usageCount, setUsageCount] = useState(() => {
    return parseInt(localStorage.getItem('usageCount') || '0', 10);
  });
  
  const [inputValue, setInputValue] = useState('');
  
  const [chatHistory, setChatHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem('chatHistory')) || []; }
    catch { return []; }
  });
  const [jobs, setJobs] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tagifyJobs')) || []; }
    catch { return []; }
  });
  
  const [isProcessing, setIsProcessing] = useState(false);

  // Sync state to LocalStorage
  useEffect(() => { localStorage.setItem('theme', theme); document.documentElement.setAttribute('data-theme', theme); }, [theme]);
  useEffect(() => { localStorage.setItem('apiKeys', JSON.stringify(apiKeys)); }, [apiKeys]);
  useEffect(() => { localStorage.setItem('usageCount', usageCount.toString()); }, [usageCount]);
  useEffect(() => { localStorage.setItem('tagifyJobs', JSON.stringify(jobs)); }, [jobs]);
  useEffect(() => { localStorage.setItem('chatHistory', JSON.stringify(chatHistory)); }, [chatHistory]);
  useEffect(() => { localStorage.setItem('userName', userName); }, [userName]);
  useEffect(() => { localStorage.setItem('userEmail', userEmail); }, [userEmail]);

  // Toast Timer
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(''), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Table data extraction
  const tableJobs = chatHistory.flatMap(m => m.type === 'table' ? m.jobIds : []);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  const showToast = (msg, type = 'success') => { setToastMessage({ text: msg, type }) };

  // Limits
  const validApiKeys = apiKeys.filter(k => typeof k === 'string' ? k.trim().length > 0 : k?.key?.trim().length > 0);
  const maxLimit = validApiKeys.length === 0 ? 25 : (validApiKeys.length >= 4 ? 3999 : 999);
  const isLimitExceeded = usageCount >= maxLimit;

  // Polling for jobs
  useEffect(() => {
    const activeJobs = jobs.filter(j => j.status === 'queued' || j.status === 'processing');
    if (activeJobs.length === 0) {
      if (isProcessing) setIsProcessing(false);
      return;
    }
    
    if (!isProcessing) setIsProcessing(true);

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs-status`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_ids: activeJobs.map(j => j.id) }),
        });
        const statusMap = await res.json();
        
        setJobs(prev => prev.map(job => {
          const updated = statusMap[job.id];
          if (updated) {
            // Refund quota if job failed or was cancelled
            if ((job.status === 'queued' || job.status === 'processing') && 
                (updated.status === 'failed' || updated.status === 'cancelled')) {
              setUsageCount(u => Math.max(0, u - 1));
            }
            return { ...job, status: updated.status, result: updated.result || job.result };
          }
          return job;
        }));
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [jobs, isProcessing]);

  const cancelJobs = async () => {
    const activeJobs = jobs.filter(j => j.status === 'queued' || j.status === 'processing');
    if (activeJobs.length === 0) return;
    
    try {
      await fetch(`${API_BASE}/cancel-bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: activeJobs.map(j => j.id) }),
      });
      showToast("Cancellation requested. Stopping remaining jobs...", "success");
    } catch (e) {
      console.error("Cancel error:", e);
      showToast("Failed to cancel jobs", "error");
    }
  };

  // Handle Chat & Tagging Submission
  const handleSubmit = async () => {
    if (!inputValue.trim() || isLimitExceeded) return;
    
    const userMessage = { id: Date.now().toString(), role: 'user', content: inputValue };
    setChatHistory(prev => [...prev, userMessage]);
    
    const urls = inputValue.split(/[\s,]+/).filter(u => u.startsWith('http'));
    const inputCopy = inputValue;
    const customPromptText = inputValue.replace(/https?:\/\/[^\s]+/g, '').replace(/,/g, ' ').trim();
    setInputValue('');
    
    if (urls.length > 0) {
      // IMAGE TAGGING FLOW
      const newUsage = usageCount + urls.length;
      if (newUsage > maxLimit) {
        showToast(`Limit exceeded! You can only process ${maxLimit - usageCount} more images on this plan.`, 'error');
        return;
      }
      setUsageCount(newUsage);
      
      const validKeys = apiKeys.filter(k => typeof k === 'string' && k.trim().length > 0);
      const activeKeysStr = validKeys.length > 0 ? validKeys.join(',') : '';
      try {
        const response = await fetch(`${API_BASE}/analyze-bulk`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-User-API-Key': activeKeysStr
          },
          body: JSON.stringify({ urls: [...new Set(urls)], custom_prompt: customPromptText }),
        });
        const data = await response.json();
        if (response.ok && data.jobs) {
          const newJobs = data.jobs.map((j, idx) => ({
            id: j.job_id,
            status: 'queued',
            result: null,
            filename: `Image_${jobs.length + idx + 1}`,
            previewUrl: j.url
          }));
          setJobs(prev => [...prev, ...newJobs]);
          
          setChatHistory(prev => [...prev, { 
            id: Date.now().toString() + 'ai', 
            role: 'ai', 
            type: 'table',
            jobIds: data.jobs.map(j => j.job_id)
          }]);
        } else {
          console.error("Backend error:", data);
          showToast(`Server Error: ${data.detail || 'Could not queue jobs'}`, 'error');
          setUsageCount(prev => prev - urls.length); // Refund quota
        }
      } catch (e) {
        console.error("Analyze error:", e);
        showToast("Network Error: Could not connect to server.", "error");
        setUsageCount(prev => prev - urls.length); // Refund quota
      }
    } else {
      // NORMAL CHAT FLOW
      setUsageCount(prev => prev + 1);
      const validKeys = apiKeys.filter(k => typeof k === 'string' && k.trim().length > 0);
      const activeKeysStr = validKeys.length > 0 ? validKeys.join(',') : '';
      try {
        const response = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-User-API-Key': activeKeysStr
          },
          body: JSON.stringify({ message: inputCopy, history: chatHistory.slice(-10) }),
        });
        const data = await response.json();
        if (data.response) {
          setChatHistory(prev => [...prev, { id: Date.now().toString() + 'ai', role: 'ai', content: data.response }]);
        }
      } catch (e) {
        console.error("Chat error:", e);
        setChatHistory(prev => [...prev, { id: Date.now().toString() + 'ai', role: 'ai', content: "Sorry, I couldn't connect to the server. Please make sure the backend is running." }]);
      }
    }
  };

  const navTo = (tab) => {
    setActiveTab(tab);
    setIsSidebarOpen(false);
  };

  const renderUserMessage = (content) => {
    const urlRegex = /(https?:\/\/[^\s,]+)/g;
    const urls = content.match(urlRegex) || [];
    
    if (urls.length === 0) return <div style={{whiteSpace: 'pre-wrap'}}>{content}</div>;

    const textPart = content.replace(urlRegex, '').replace(/,/g, ' ').trim();
    
    return (
      <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
        {textPart && <div style={{fontWeight: 'bold'}}>{textPart}</div>}
        <div className="link-list">
          <div style={{color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4}}>{urls.length} images attached:</div>
          {urls.slice(0, 3).map((url, i) => (
             <a key={i} href={url} target="_blank" rel="noreferrer" style={{color: '#3b82f6', textDecoration: 'none', display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '100%'}}>
               {url}
             </a>
          ))}
          {urls.length > 3 && (
             <div style={{color: 'var(--text-secondary)', fontSize: 12, marginTop: 4, fontStyle: 'italic'}}>
               + {urls.length - 3} more links hidden...
             </div>
          )}
        </div>
      </div>
    );
  };

  // Views rendering
  const renderSidebar = () => (
    <>
      <div className={`mobile-overlay ${isSidebarOpen ? 'open' : ''}`} onClick={() => setIsSidebarOpen(false)}></div>
      <div className={`sidebar ${isSidebarOpen ? 'open desktop-open' : 'desktop-closed'}`}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 30, width: '100%', paddingLeft: isSidebarOpen ? '20px' : '0', paddingRight: isSidebarOpen ? '20px' : '0', justifyContent: isSidebarOpen ? 'space-between' : 'center'}}>
          <div className="brand-icon" style={{marginBottom: 0}}>T</div>
          {isSidebarOpen && <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(false)} style={{display: window.innerWidth > 768 ? 'none' : 'block'}}><X size={24}/></button>}
        </div>
        <div className={`nav-item ${activeTab === 'studio' ? 'active' : ''}`} onClick={() => navTo('studio')} title="Tagging Studio">
          <Grid size={22} /> <span className="nav-item-text">Tagging Studio</span>
        </div>
        <div className={`nav-item ${activeTab === 'keys' ? 'active' : ''}`} onClick={() => navTo('keys')} title="API Settings">
          <Key size={22} /> <span className="nav-item-text">API Settings</span>
        </div>
        <div className={`nav-item ${activeTab === 'plans' ? 'active' : ''}`} onClick={() => navTo('plans')} title="Upgrade Plans">
          <Layers size={22} /> <span className="nav-item-text">Upgrade Plans</span>
        </div>
        <div style={{flex: 1}}></div>
        <div className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => navTo('settings')} title="Settings">
          <Settings size={22} /> <span className="nav-item-text">Settings</span>
        </div>
      </div>
    </>
  );

  const renderTopbar = (title) => (
    <div className="topbar">
      <div className="topbar-left">
        <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
          <Menu size={22} />
        </button>
        <div className="desktop-only-title" style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <div className="brand-icon" style={{width: 24, height: 24, fontSize: 12, marginBottom: 0}}>T</div>
          {title}
        </div>
      </div>
      <div className="topbar-right">
        {isLimitExceeded && (
           <div className="limit-exceeded-badge" style={{color: 'white', backgroundColor: '#ef4444', padding: '6px 12px', borderRadius: 20, fontSize: 13, fontWeight: 'bold', whiteSpace: 'nowrap'}}>
             Daily limit exceeded
           </div>
        )}
        {activeTab === 'studio' && (
          <button className="icon-button" onClick={() => { setChatHistory([]); localStorage.setItem('chatHistory', '[]'); }} title="Clear Chat">
            <Trash2 size={20} />
          </button>
        )}
        <button className="icon-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <div className="profile-pill hide-on-mobile">
          <div className="profile-avatar"></div>
          {userName}
        </div>
      </div>
    </div>
  );

  const renderPlans = () => {
    const validCount = validApiKeys.length;
    let currentPlan = 'demo';
    if (validCount >= 1 && validCount < 4) currentPlan = 'standard';
    else if (validCount >= 4) currentPlan = 'pro';

    return (
    <div className="view-container">
      <h1 className="page-title" style={{textAlign: 'center'}}>Scale your limits for free</h1>
      <p className="page-subtitle" style={{textAlign: 'center'}}>Bypass daily limits by connecting multiple free Google Gemini API keys.</p>
      
      <div className="plans-grid">
        <div className={`plan-card ${currentPlan === 'demo' ? 'highlight' : ''}`}>
          <div className="plan-title">Demo</div>
          <div className="plan-price">0 <span style={{fontSize: 12, color: 'var(--text-secondary)'}}>API Keys required</span></div>
          <div className="plan-desc">Essential features for testing and light usage.</div>
          {currentPlan === 'demo' ? (
            <button className="plan-btn">Your current plan</button>
          ) : (
            <button className="plan-btn" onClick={() => navTo('keys')}>Downgrade to Demo</button>
          )}
          <ul className="feature-list">
            <li><Grid size={16}/> Basic AI tagging models</li>
            <li><CheckIcon/> 25 images per day limit</li>
            <li><CheckIcon/> No setup required</li>
          </ul>
        </div>

        <div className={`plan-card ${currentPlan === 'standard' ? 'highlight' : ''}`}>
          <div className="plan-title">Standard <span className="popular-badge">Popular</span></div>
          <div className="plan-price">1 <span style={{fontSize: 12, color: 'var(--text-secondary)'}}>API Keys required</span></div>
          <div className="plan-desc">Unlock the full experience for standard catalogs.</div>
          {currentPlan === 'standard' ? (
            <button className="plan-btn primary">Your current plan</button>
          ) : (
            <button className={`plan-btn ${currentPlan === 'demo' ? 'primary' : ''}`} onClick={() => navTo('keys')}><KeyRound size={16}/> Add API Keys</button>
          )}
          <ul className="feature-list">
            <li><Layers size={16} color="var(--brand-color)"/> Distributed load balancing</li>
            <li><CheckIcon/> 999 images per day limit</li>
            <li className="warn"><AlertTriangle size={16}/> Requires unique Google accounts</li>
          </ul>
        </div>

        <div className={`plan-card ${currentPlan === 'pro' ? 'highlight' : ''}`}>
          <div className="plan-title">Pro</div>
          <div className="plan-price">4 <span style={{fontSize: 12, color: 'var(--text-secondary)'}}>API Keys required</span></div>
          <div className="plan-desc">Maximize productivity for enterprise scale.</div>
          {currentPlan === 'pro' ? (
            <button className="plan-btn primary">Your current plan</button>
          ) : (
            <button className="plan-btn" onClick={() => navTo('keys')}><KeyRound size={16}/> Add API Keys</button>
          )}
          <ul className="feature-list">
            <li><Settings size={16} color="#3b82f6"/> Maximum concurrency</li>
            <li><CheckIcon/> 3,999 images per day limit</li>
            <li className="warn"><AlertTriangle size={16}/> Requires unique Google accounts</li>
          </ul>
        </div>
      </div>
      <p style={{textAlign: 'center', fontSize: 12, color: 'var(--text-secondary)', marginTop: 40}}>
        Completely free. Limits are enforced based on the combined quotas of your connected Google Gemini free tier API keys.
      </p>
    </div>
    );
  };

  const renderApiSettings = () => {
    const handleAddKey = () => {
      if(apiKeys.length >= 4) return;
      setApiKeys([...apiKeys, '']);
    };
    const handleUpdateKey = (idx, val) => {
      const updated = [...apiKeys];
      updated[idx] = val;
      setApiKeys(updated);
    };
    const handleDeleteKey = (idx) => {
      setApiKeys(apiKeys.filter((_, i) => i !== idx));
    };
    
    const handleSaveProfile = () => {
      localStorage.setItem('userName', userName);
      localStorage.setItem('userEmail', userEmail);
      showToast('Profile saved successfully!');
    };

    const handleSaveKeys = () => {
      const currentValidCount = apiKeys.filter(k => typeof k === 'string' ? k.trim().length > 0 : k?.key?.trim().length > 0).length;
      if (currentValidCount > 0) {
        setUsageCount(0);
        localStorage.setItem('usageCount', '0');
      } else {
        setUsageCount(25); // Prevent free-tier reset exploit
        localStorage.setItem('usageCount', '25');
      }
      localStorage.setItem('apiKeys', JSON.stringify(apiKeys));
      showToast('API Keys saved successfully!');
    };

    return (
      <div className="view-container" style={{maxWidth: 1000, margin: '0 auto'}}>
        <h1 className="page-title">API Settings & Profile</h1>
        <p className="page-subtitle">Manage your account, view your current plan, and configure API integrations.</p>
        
        <div className="settings-tabs">
          <div className={`settings-tab ${activeSettingsTab === 'api' ? 'active' : ''}`} onClick={() => setActiveSettingsTab('api')}>
            <Key size={16} style={{display:'inline', marginRight: 8}}/> API Configuration
          </div>
          <div className={`settings-tab ${activeSettingsTab === 'guide' ? 'active' : ''}`} onClick={() => setActiveSettingsTab('guide')}>API Guide</div>
          <div className={`settings-tab ${activeSettingsTab === 'account' ? 'active' : ''}`} onClick={() => setActiveSettingsTab('account')}>Account Details</div>
        </div>

        {activeSettingsTab === 'api' && (
          <>
            <div className="alert-box">
              <AlertTriangle size={24} color="var(--error-color)" />
              <div>
                <div className="title">CRITICAL RULE: ONE GMAIL = ONE API KEY</div>
                <div className="desc">
                  Tagify AI exclusively uses the <b>Google Gemini API</b>. If you need to add 2 or more API keys to scale your limits, <b>you MUST generate those keys from completely DIFFERENT Gmail accounts.</b><br/>
                  If you generate multiple API keys from the same Gmail ID, they share the exact same limit and the system will reject the duplicates.
                </div>
              </div>
            </div>

            <div className="api-card">
              <div className="api-card-header">
                <div style={{display: 'flex', alignItems: 'center', gap: 8}}><KeyRound size={18} color="var(--brand-color)"/> Your API Keys</div>
                <div className="api-count">{apiKeys.length} / 4 Connected</div>
              </div>
              
              {apiKeys.map((key, idx) => (
                <div className="api-input-group" key={idx}>
                  <label>Gemini API Key {idx + 1} {idx === 0 && '(Primary)'}</label>
                  <div className="api-input-row">
                    <input 
                      type="password" 
                      className="api-input" 
                      value={key} 
                      onChange={(e) => handleUpdateKey(idx, e.target.value)} 
                      placeholder="AIzaSy..." 
                    />
                    <button className="api-btn"><Edit2 size={16}/></button>
                    <button className="api-btn delete" onClick={() => handleDeleteKey(idx)}><Trash2 size={16}/></button>
                  </div>
                </div>
              ))}

              {apiKeys.length < 4 && (
                <button className="plan-btn" style={{marginBottom: 0, width: 'auto'}} onClick={handleAddKey}>
                  <Plus size={16}/> Add New API Key
                </button>
              )}

              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 40}}>
                 <div style={{fontSize: 12, color: 'var(--text-secondary)'}}>Stored securely in your browser's local storage.</div>
                 <button className="save-btn" onClick={handleSaveKeys}><Copy size={18}/> Save Edits</button>
              </div>
            </div>
          </>
        )}

        {activeSettingsTab === 'guide' && (
          <div className="api-card" style={{padding: 40}}>
             <h2 style={{marginBottom: 30}}>How to get a Free Gemini API Key</h2>
             <div className="timeline">
               <div className="timeline-step">
                 <div className="timeline-number">1</div>
                 <div className="timeline-content">
                    <div className="timeline-title">Go to Google AI Studio</div>
                    <div className="timeline-desc">Visit <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{color: 'var(--brand-color)'}}>aistudio.google.com</a> and sign in with your Gmail account.</div>
                 </div>
               </div>
               <div className="timeline-step">
                 <div className="timeline-number">2</div>
                 <div className="timeline-content">
                    <div className="timeline-title">Click "Get API Key"</div>
                    <div className="timeline-desc">In the left sidebar menu, find and click on the "Get API key" button.</div>
                 </div>
               </div>
               <div className="timeline-step">
                 <div className="timeline-number">3</div>
                 <div className="timeline-content">
                    <div className="timeline-title">Create API Key in new project</div>
                    <div className="timeline-desc">Click the blue button that says "Create API key". A pop-up will appear with your new key starting with AIzaSy...</div>
                 </div>
               </div>
               <div className="timeline-step">
                 <div className="timeline-number">4</div>
                 <div className="timeline-content">
                    <div className="timeline-title">Copy and Paste</div>
                    <div className="timeline-desc">Copy the key and paste it into the Tagify AI Dashboard configuration box. You're ready to tag!</div>
                 </div>
               </div>
             </div>
             <div style={{display: 'flex', justifyContent: 'center', marginTop: 40}}>
               <button className="save-btn" onClick={() => window.open('https://aistudio.google.com', '_blank')}>Go to Google AI Studio</button>
             </div>
          </div>
        )}

        {activeSettingsTab === 'account' && (
          <div className="account-form">
            <h2 style={{marginBottom: 20}}>Public Profile</h2>
            
            <div className="api-input-group">
              <label>DISPLAY NAME</label>
              <input 
                className="api-input" 
                value={userName} 
                onChange={(e) => setUserName(e.target.value)} 
                placeholder="e.g. John Doe" 
                style={{width: '100%', fontFamily: 'inherit'}}
              />
            </div>
            
            <div className="api-input-group">
              <label>EMAIL ADDRESS</label>
              <input 
                className="api-input" 
                value={userEmail} 
                onChange={(e) => setUserEmail(e.target.value)} 
                placeholder="email@example.com"
                style={{width: '100%', fontFamily: 'inherit'}}
              />
            </div>
            
            <button className="save-btn" style={{float: 'none', width: '100%', justifyContent: 'center'}} onClick={handleSaveProfile}>Save Profile changes</button>
          </div>
        )}
      </div>
    );
  };

  const renderTable = (jobIds) => {
    const tableJobs = jobs.filter(j => jobIds.includes(j.id));
    const completedCount = tableJobs.filter(j => j.status === 'completed' || j.status === 'failed').length;
    const progressPercent = tableJobs.length === 0 ? 0 : Math.round((completedCount / tableJobs.length) * 100);

    const possibleCols = [
      "Color", "Fit/Shape", "Neck", "Occasion", "Ornamentation", 
      "Pattern", "PnP", "Sleeve Styling", "Length", 
      "Sleeve Length"
    ];
    const completedJobsData = tableJobs.filter(j => j.status === 'completed' && j.result);
    
    const visibleCols = possibleCols.filter(col => {
      if (completedJobsData.length === 0) return true;
      return completedJobsData.some(j => {
        const val = j.result[col];
        return val && val !== '-' && val !== 'Not Available' && val !== 'Not Applicable';
      });
    });

    const copyToClipboard = () => {
      if (completedJobsData.length === 0) return;
      const header = ["SL.NO", "IMAGE", ...visibleCols].join('\t');
      const rows = completedJobsData.map((j, idx) => {
        const r = [idx + 1, j.previewUrl];
        visibleCols.forEach(c => r.push(j.result[c] || ''));
        return r.join('\t');
      }).join('\n');
      navigator.clipboard.writeText(`${header}\n${rows}`);
      showToast('Copied to clipboard!');
    };

    const exportCSV = () => {
      if (completedJobsData.length === 0) return;
      const header = ["SL.NO", "IMAGE", ...visibleCols].join(',');
      const rows = completedJobsData.map((j, idx) => {
        const r = [idx + 1, j.previewUrl];
        visibleCols.forEach(c => {
          const val = (j.result[c] || '').toString().replace(/"/g, '""');
          r.push(`"${val}"`);
        });
        return r.join(',');
      }).join('\n');
      const blob = new Blob([`${header}\n${rows}`], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tagify_export_${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    };

    return (
      <div className="studio-table-wrapper" style={{margin: '10px 0'}}>
        <div className="studio-table-header">
          <div style={{fontWeight: 600}}>Processed Images</div>
          <div className="progress-bar-container">
            <div className="progress-text">
              <span>{completedCount} / {tableJobs.length} PROCESSED</span>
              <span>{progressPercent}%</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{width: `${progressPercent}%`}}></div>
            </div>
          </div>
            <div className="table-actions">
              {isProcessing && (
                <button className="btn-solid" onClick={cancelJobs} style={{ backgroundColor: '#451a1a', color: '#f87171', border: '1px solid #7f1d1d' }}>
                  <X size={16}/> Cancel
                </button>
              )}
              <button className="btn-outline brand" onClick={copyToClipboard}><Copy size={16}/> Copy for Sheets</button>
              <button className="btn-solid" onClick={exportCSV}><Download size={16}/> Export CSV</button>
            </div>
        </div>
        
        <div className="table-scroll" style={{maxHeight: '400px'}}>
          <table className="tag-table">
            <thead>
              <tr>
                <th>SL.NO</th>
                <th>IMAGE</th>
                {visibleCols.map(c => <th key={c}>{c.toUpperCase()}</th>)}
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {tableJobs.map((job, idx) => (
                <tr key={job.id}>
                  <td>{idx + 1}</td>
                  <td><img src={job.previewUrl} className="td-image" alt="item" onClick={() => setSelectedImage(job.previewUrl)} style={{cursor: 'pointer'}} title="Click to view full image"/></td>
                  {visibleCols.map(col => (
                     <td key={col} style={{color: 'var(--text-secondary)'}}>{job.result?.[col] || '-'}</td>
                  ))}
                  <td>
                    {job.status === 'queued' && <span style={{color: '#eab308', fontSize: 12}}>Queued</span>}
                    {job.status === 'processing' && <span style={{color: '#3b82f6', fontSize: 12}}>Processing...</span>}
                    {job.status === 'completed' && <span style={{color: 'var(--success-color)', fontSize: 12}}>Done</span>}
                    {job.status === 'failed' && <span style={{color: 'var(--error-color)', fontSize: 12}}>Failed</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderTaggingStudio = () => {
    return (
      <div className="studio-container">
        {isLimitExceeded && (
          <div style={{position: 'absolute', top: 20, zIndex: 60}} className="limit-banner">
            <AlertTriangle size={20}/> API Limit Exceeded! Please add a new API Key in Settings.
          </div>
        )}

        <div className="chat-stream">
          {chatHistory.length === 0 ? (
            <div className="chat-empty-state">
              <div className="chat-empty-logo">T</div>
              <h2 style={{color: 'var(--text-primary)', marginBottom: 8}}>How can I help you today?</h2>
              <p>Chat with Tagify AI or paste image links to start tagging automatically.</p>
            </div>
          ) : (
            chatHistory.map(msg => (
              <div key={msg.id} className={`chat-message ${msg.role} ${msg.type === 'table' ? 'table-message' : ''}`}>
                <div className="chat-bubble" style={msg.type === 'table' ? {backgroundColor: 'transparent', border: 'none'} : {}}>
                  {msg.type === 'table' ? (
                    <>
                      <div style={{marginBottom: 12, color: 'var(--text-primary)'}}>
                        I've queued <b>{msg.jobIds.length}</b> images for tagging. 
                        <span style={{color: 'var(--brand-color)', marginLeft: 8, fontSize: 13, fontWeight: 500}}>
                          (Estimated time: ~{msg.jobIds.length * 2} seconds)
                        </span>
                        <br/><span style={{fontSize: 13, color: 'var(--text-secondary)'}}>Here are the live results:</span>
                      </div>
                      {renderTable(msg.jobIds)}
                    </>
                  ) : msg.role === 'user' ? (
                    renderUserMessage(msg.content)
                  ) : (
                    <div style={{whiteSpace: 'pre-wrap'}}>{msg.content}</div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="floating-input-wrapper">
          <div className="desktop-input-details">
            <div className="model-selector" style={{display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, cursor: 'pointer', color: 'var(--text-primary)'}}>
              Tagify AI v1 <ChevronDown size={16}/>
            </div>
            {validApiKeys.length > 0 && (
              <div className="usage-text" style={{fontSize: 12, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', whiteSpace: 'nowrap'}}>
                 {usageCount}/{maxLimit} Used
              </div>
            )}
          </div>

          <button className="plus-btn" title="Attach image">
            <Plus size={20} />
          </button>

          <input 
            className="chat-input" 
            placeholder="Ask Tagify AI..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => { if(e.key === 'Enter' && inputValue.trim()) handleSubmit(); }}
            disabled={isLimitExceeded}
          />

          <div className="input-icons">
            {inputValue.trim() ? (
              <button className="send-btn-circle" onClick={handleSubmit} disabled={isLimitExceeded}>
                <Send size={16} />
              </button>
            ) : (
              <>
                <button className="mic-btn"><Mic size={20}/></button>
                <button className="voice-mode-btn"><Headphones size={18}/></button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      {toastMessage && (
        <div className={`toast ${toastMessage.type === 'error' ? 'toast-error' : ''}`}>
          {toastMessage.text}
        </div>
      )}
      
      {renderSidebar()}
      
      <div className="main-area">
        {activeTab === 'studio' && renderTopbar('Tagging Studio')}
        {activeTab === 'keys' && renderTopbar('API Settings')}
        {activeTab === 'plans' && renderTopbar('Upgrade Plan')}
        {activeTab === 'settings' && renderTopbar('Settings')}

        {activeTab === 'studio' && renderTaggingStudio()}
        {activeTab === 'plans' && renderPlans()}
        {activeTab === 'keys' && renderApiSettings()}
        {activeTab === 'settings' && (
           <div className="view-container">
             <h1 className="page-title">Settings</h1>
             <p className="page-subtitle">Additional application preferences.</p>
             <div className="account-form">
               <h3 style={{marginBottom: 16}}>Appearance</h3>
               <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                 <span>Theme Mode:</span>
                 <button className="btn-outline brand" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                    {theme === 'dark' ? <><Sun size={16}/> Switch to Light</> : <><Moon size={16}/> Switch to Dark</>}
                 </button>
               </div>
               
               <h3 style={{marginTop: 40, marginBottom: 16}}>Data Management</h3>
               <div style={{display: 'flex', gap: 12}}>
                 <button className="btn-outline brand" onClick={() => { localStorage.clear(); window.location.reload(); }}>
                    Clear Local Storage (Reset Data)
                 </button>
               </div>
             </div>
           </div>
        )}
      </div>

      {selectedImage && (
        <div className="image-modal-overlay" onClick={() => setSelectedImage(null)} style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.85)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out'}}>
          <img src={selectedImage} alt="Full size" style={{maxWidth: '90vw', maxHeight: '90vh', borderRadius: 12, objectFit: 'contain', boxShadow: '0 10px 40px rgba(0,0,0,0.5)'}} />
        </div>
      )}
    </div>
  );
}

// Simple Check Icon
const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{color: 'var(--success-color)'}}>
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

export default App;
