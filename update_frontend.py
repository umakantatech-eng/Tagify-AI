import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the polling logic
old_polling = """
        try:
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
"""

new_polling = """
        try:
          const res = await fetch(`${API_BASE}/jobs-status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_ids: activeJobs.map(j => j.id) }),
          });
          const statusData = await res.json();
          
          if (statusData.eta_seconds !== undefined) {
              setBulkStats({
                  eta: statusData.eta_seconds,
                  exhausted: statusData.exhausted_keys,
                  active: statusData.active_workers
              });
          }
          
          const statusMap = {};
          if (statusData.statuses) {
              statusData.statuses.forEach(s => { statusMap[s.job_id] = s; });
          } else {
              // Fallback just in case
              Object.assign(statusMap, statusData);
          }
          
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
"""

content = content.replace(old_polling.strip(), new_polling.strip())

# Need to add bulkStats state
state_block = """
  const [isProcessing, setIsProcessing] = useState(false);
"""
new_state_block = """
  const [isProcessing, setIsProcessing] = useState(false);
  const [bulkStats, setBulkStats] = useState({ eta: 0, exhausted: 0, active: 0 });
"""
content = content.replace(state_block.strip(), new_state_block.strip())

# Need to add UI for ETA
ui_block = """
              <div className="flex-1 ml-4 relative h-2 bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500" 
                  style={{ width: `${Math.round((processedCount / totalJobsCount) * 100)}%` }}
                ></div>
              </div>
"""

new_ui_block = """
              <div className="flex-1 ml-4 relative h-2 bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500" 
                  style={{ width: `${Math.round((processedCount / totalJobsCount) * 100)}%` }}
                ></div>
              </div>
              
              {bulkStats.eta > 0 && isProcessing && (
                  <div className="ml-4 flex flex-col items-end text-xs">
                      <span className="text-gray-400">ETA: ~{Math.ceil(bulkStats.eta / 60)} min {bulkStats.eta % 60} sec</span>
                      {bulkStats.exhausted > 0 && (
                          <span className="text-red-400">⚠️ {bulkStats.exhausted} Key(s) Exhausted</span>
                      )}
                  </div>
              )}
"""

content = content.replace(ui_block.strip(), new_ui_block.strip())

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
