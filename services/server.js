const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const app = express();
const port = 8005;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Basic error checking helper
const getErrorLogs = (logs) => {
    return logs.split('\n').filter(line => 
        line.toLowerCase().includes('error') || 
        line.toLowerCase().includes('exception') ||
        line.toLowerCase().includes('fail')
    ).join('\n');
};

app.get('/', (req, res) => {
    // List all containers that are part of this project (we can just list all docker-compose containers or all in general)
    exec('docker ps -a --format "{{.Names}}|{{.State}}|{{.Status}}"', (err, stdout, stderr) => {
        if (err) {
            return res.status(500).send("Error fetching services: " + err.message);
        }
        const containers = stdout.trim().split('\n').filter(Boolean).map(line => {
            const [name, state, status] = line.split('|');
            return { name, state, status };
        });
        res.render('index', { containers });
    });
});

app.get('/logs/:containerName', (req, res) => {
    const containerName = req.params.containerName;
    const filter = req.query.filter === 'errors';
    
    exec(`docker logs --tail 500 ${containerName}`, (err, stdout, stderr) => {
        let logs = stderr + stdout; 
        if (filter) {
            logs = getErrorLogs(logs);
        }
        res.render('logs', { containerName, logs, filter });
    });
});

app.listen(port, () => {
    console.log(`Service dashboard running at http://localhost:${port}`);
});
