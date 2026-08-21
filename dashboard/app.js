const API_URL = "http://localhost:8080/stats";
const POLL_INTERVAL = 1000;

function updateDOM(id, value) {
    const el = document.getElementById(id);
    if(el.innerText !== value.toString()) {
        el.innerText = value;
    }
}

async function fetchStats() {
    try {
        const res = await fetch(API_URL);
        if(!res.ok) throw new Error("API Offline");
        const data = await res.json();
        
        document.getElementById('pulse').classList.remove('offline');

        updateDOM('val-active', data.active_pipelines);
        updateDOM('val-max', data.max_pipelines);
        updateDOM('val-total', data.total_jobs);
        updateDOM('val-processing', data.processing_jobs);
        updateDOM('val-completed', data.completed_jobs);
        updateDOM('val-failed', data.failed_jobs);

        const pct = Math.min((data.active_pipelines / data.max_pipelines) * 100, 100);
        document.getElementById('prog-active').style.width = `${pct}%`;

    } catch (e) {
        console.error(e);
        document.getElementById('pulse').classList.add('offline');
    }
}

// Initial fetch and start polling
fetchStats();
setInterval(fetchStats, POLL_INTERVAL);
