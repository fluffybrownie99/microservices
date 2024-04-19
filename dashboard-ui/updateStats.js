const STATS_API_URL = "http://acit3855audit.westus3.cloudapp.azure.com/processing/home/media/stats"
const EVENTS_URL = {
    mediaupload: "http://acit3855audit.westus3.cloudapp.azure.com/audit_log/home/media/upload",
    mediaplayback: "http://acit3855audit.westus3.cloudapp.azure.com/audit_log/home/media/playback",
    anomalyhigh: "http://acit3855audit.westus3.cloudapp.azure.com/anomalies/anomalies?anomaly_type=TooHigh",
    anomalylarge: "http://acit3855audit.westus3.cloudapp.azure.com/anomalies/anomalies?anomaly_type=TooMany",
}

// Fetch and update the general statistics
const getStats = (statsUrl) => {
    fetch(statsUrl)
        .then(res => res.json())
        .then((result) => {
            console.log("Received stats", result);
            updateStatsHTML(result['0']);
        }).catch((error) => {
            updateStatsHTML(error.message, error = true);
        })
}

// Fetch a single event from the audit service
const getEvent = (eventType) => {
    const eventIndex = Math.floor(Math.random() * 100);

    fetch(`${EVENTS_URL[eventType]}?index=${eventIndex}`)
        .then(res => {
            if (!res.ok) {
                throw new Error(`Error: status code ${res.status}`);
            }
            return res.json();
        })
        .then((result) => {
            console.log("Received event", result);
            updateEventHTML({...result['payload'], index: eventIndex}, eventType);
        }).catch((error) => {
            updateEventHTML({error: error.message, index: eventIndex}, eventType, error = true);
        })
}

// Fetch the first anomaly of a specific type
const getFirstAnomaly = (anomalyType) => {
    fetch(EVENTS_URL[anomalyType])
        .then(res => res.json())
        .then((result) => {
            if (result && result.length > 0) {
                console.log(`Received ${anomalyType} anomaly`, result[0]);
                updateAnomalyHTML(result[0], anomalyType);
            } else {
                throw new Error("No anomalies found");
            }
        }).catch((error) => {
            updateAnomalyHTML({error: error.message}, anomalyType, true);
        })
}

// Update the HTML for an anomaly event
const updateAnomalyHTML = (data, anomalyType, error = false) => {
    const elem = document.getElementById(`event-${anomalyType}`);
    elem.innerHTML = `<h5>Anomaly Event</h5>`;

    if (error) {
        const errorMsg = document.createElement("code");
        errorMsg.innerHTML = data.error;
        elem.appendChild(errorMsg);
        return;
    }

    Object.entries(data).forEach(([key, value]) => {
        const labelElm = document.createElement("span");
        const valueElm = document.createElement("span");
        labelElm.innerText = key + ": ";
        valueElm.innerText = value;
        const pElm = document.createElement("p");
        pElm.style.display = "flex";
        pElm.style.flexDirection = "column";
        pElm.appendChild(labelElm);
        pElm.appendChild(valueElm);
        elem.appendChild(pElm);
    });
}

// Update the main statistics div
const updateStatsHTML = (data, error = false) => {
    const elem = document.getElementById("stats");
    if (error) {
        elem.innerHTML = `<code>${data}</code>`;
        return;
    }
    elem.innerHTML = "";
    Object.entries(data).map(([key, value]) => {
        const pElm = document.createElement("p");
        pElm.innerHTML = `<strong>${key}:</strong> ${value}`;
        elem.appendChild(pElm);
    })
}

const setup = () => {
    getStats(STATS_API_URL);
    getEvent("mediaupload");
    getEvent("mediaplayback");
    getFirstAnomaly("anomalyhigh");
    getFirstAnomaly("anomalylarge");
    const interval = setInterval(() => {
        getStats(STATS_API_URL);
        getEvent("mediaupload");
        getEvent("mediaplayback");
        getFirstAnomaly("anomalyhigh");
        getFirstAnomaly("anomalylarge");
    }, 5000); // Update every 5 seconds
}

document.addEventListener('DOMContentLoaded', setup);
