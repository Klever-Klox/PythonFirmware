let currentSettings = {};
let availableSongs = [];

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        currentSettings = await res.json();

        const songsRes = await fetch('/songs');
        availableSongs = await songsRes.json();
        applySettings();
    } catch (err) {
        console.error('Failed to load settings from device:', err);
    }
}

function applySettings() {

    document.getElementById('sdWarning').classList.toggle('hidden', currentSettings.sdCardOk !== false);
    document.getElementById('buttonWarning').classList.toggle('hidden', currentSettings.buttonsOk !== false);
    document.getElementById('volumeInput').value = currentSettings.volume;
    document.getElementById('AlarmOnBtn').textContent = currentSettings.alarmOn ? 'Alarms Active' : 'Alarms Off';
    document.getElementById('LEDOnBtn').textContent = currentSettings.LEDOn ? 'LED On' : 'LED Off';
    document.getElementById('AlarmRingingBtn').textContent = currentSettings.alarmRinging ? 'Alarm Ringing' : 'Alarm Stopped';
    document.getElementById('contrastInput').value = currentSettings.contrast;
    document.getElementById('SW').checked = currentSettings.screenTimeoutEnabled;
    document.getElementById('FLED').checked = currentSettings.LEDFadeEnabled;
    document.getElementById('ColIn').style.setProperty('--hue', currentSettings.hue * 3.6 / 2.55);
    document.getElementById('BrtIn').style.setProperty('--brightness', currentSettings.brightness * 3.6 / 2.55);
    document.getElementById('ColIn').value = currentSettings.hue;
    document.getElementById('BrtIn').value = currentSettings.brightness;
    document.getElementById('12H').checked = currentSettings.twelveHour;
    document.getElementById('contrast').textContent = currentSettings.contrast;
    document.getElementById('volume').textContent = currentSettings.volume;
    document.getElementById('AUTOUPD').checked = !!currentSettings.autoUpdate;
    const otaUrlField = document.getElementById('fwUrl');
    // Leave the field alone while it has focus, or a background push wipes
    // out whatever is being typed.
    if (document.activeElement !== otaUrlField) otaUrlField.value = currentSettings.otaUrl || '';

    updateClock();


    // Build alarm UI
    alarmsContainer.innerHTML = '';
    currentSettings.alarms.forEach(alarm => createAlarm(alarm));

    const SongSelect = document.querySelector('.song-select');
    populateSelect(SongSelect, availableSongs, currentSettings.song);
    
    const ColourSelect = document.querySelector('.colour-select');
    const CustomSelect = document.querySelector('.custom-sliders');
    const availableColours = ['Custom', 'Red', 'Green', 'Blue', 'Yellow', 'Magenta', 'Cyan', 'White', 'Rainbow'];
    populateSelect(ColourSelect, availableColours, currentSettings.colour);
    ColourSelect.addEventListener('change', e => {
        currentSettings.colour = e.target.value;
        saveSettings();
        if (e.target.value === 'Custom') {
            CustomSelect.classList.remove('hidden');
        } else {
            CustomSelect.classList.add('hidden');
        }
    });
    if (currentSettings.colour === 'Custom') {
        CustomSelect.classList.remove('hidden');
    } else {
        CustomSelect.classList.add('hidden');
    }
}

loadSettings();

function populateSelect(select, values, selectedValue) {
    select.innerHTML = '';
    values.forEach(value => {
        const option = new Option(value, value, false, value === selectedValue);
        select.add(option);
    });
}

function updateClock() {
  const now = new Date();

  const days = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday',
    'Thursday', 'Friday', 'Saturday'
  ];

  const months = [
    'January', 'February', 'March', 'April',
    'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'
  ];

  let hours = now.getHours();
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const seconds = now.getSeconds().toString().padStart(2, '0');

  // 12 / 24 hour handling
  let suffix = '';
  if (currentSettings.twelveHour) {
    suffix = hours >= 12 ? ' PM' : ' AM';
    hours = hours % 12 || 12;
  }

  const timeStr = `${hours.toString().padStart(2, '0')}:${minutes}:${seconds}${suffix}`;
  const dayStr = days[now.getDay()];
  const monthStr = months[now.getMonth()];
  const dateStr = `${dayStr}, ${monthStr} ${now.getDate()} ${now.getFullYear()}`;

  document.getElementById('clock').textContent =
    `${timeStr} ${dateStr}`;
}

updateClock();
setInterval(updateClock, 1000);


async function saveSettings() {
    await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentSettings)
    });
}

document.getElementById('AlarmOnBtn').addEventListener('click',
    function () {
        currentSettings.alarmOn = !currentSettings.alarmOn;
        this.textContent = currentSettings.alarmOn ? 'Alarm Active' : 'Alarm Off';
        saveSettings();
    }
);
document.getElementById('LEDOnBtn').addEventListener('click',
    function () {
        currentSettings.LEDOn = !currentSettings.LEDOn;
        this.textContent = currentSettings.LEDOn ? 'LED On' : 'LED Off';
        saveSettings();
    }
);
document.getElementById('AlarmRingingBtn').addEventListener('click',
    function () {
        currentSettings.alarmRinging = !currentSettings.alarmRinging;
        this.textContent = currentSettings.alarmRinging ? 'Alarm Ringing' : 'Alarm Stopped';
        saveSettings();
    }
);
document.getElementById('ColIn').addEventListener('change',
    function () {
        currentSettings.hue = this.value;
        saveSettings();
    }
);
document.getElementById('ColIn').addEventListener('input',
    function () {
        this.style.setProperty('--hue', this.value * 3.6 / 2.55);
    }
);
document.getElementById('BrtIn').addEventListener('change',
    function () {
        currentSettings.brightness = this.value;
        saveSettings();
    }
);
document.getElementById('BrtIn').addEventListener('input',
    function () {
        this.style.setProperty('--brightness', this.value / 2.55 + "%");
    }
);
document.querySelector('input[id="SW"]').addEventListener('input',
    function () {
        currentSettings.screenTimeoutEnabled = this.checked;
        saveSettings();
    }
);
document.querySelector('input[id="FLED"]').addEventListener('input',
    function () {
        currentSettings.LEDFadeEnabled = this.checked;
        saveSettings();
    }
);
document.querySelector('input[id="12H"]').addEventListener('input',
    function () {
        currentSettings.twelveHour = this.checked;
        saveSettings();
        updateClock();
    }
);
const volumeInput = document.getElementById('volumeInput');
volumeInput.addEventListener('change', e => {
    currentSettings.volume = Number(e.target.value);
        saveSettings();
});
volumeInput.addEventListener('input', e => {
    document.getElementById("volume").textContent = e.target.value;
});
const contrastInput = document.getElementById('contrastInput');
contrastInput.addEventListener('change', e => {
    currentSettings.contrast = Number(e.target.value);
        saveSettings();
});
contrastInput.addEventListener('input', e => {
    document.getElementById("contrast").textContent = e.target.value;
});

const events = new EventSource('/events');
events.addEventListener('settings', e => {
    try {
        currentSettings = JSON.parse(e.data);
        applySettings();
    } catch (err) {
        console.error('Failed to parse settings event:', err);
    }
});
events.addEventListener('ota', e => {
    try {
        applyOta(JSON.parse(e.data));
    } catch (err) {
        console.error('Failed to parse ota event:', err);
    }
});

// ---------------- Firmware updates ----------------

const fwCurrent = document.getElementById('fwCurrent');
const fwLatest = document.getElementById('fwLatest');
const fwStatus = document.getElementById('fwStatus');
const fwNotes = document.getElementById('fwNotes');
const fwCheckBtn = document.getElementById('fwCheck');
const fwInstallBtn = document.getElementById('fwInstall');
const fwProgress = document.getElementById('fwProgress');
const fwProgressBar = document.getElementById('fwProgressBar');
const fwUrlInput = document.getElementById('fwUrl');
const fwAutoInput = document.getElementById('AUTOUPD');

let otaStatus = {};
let otaPollTimer = null;
let otaRebootTimer = null;

async function loadOta() {
    try {
        const res = await fetch('/api/ota');
        applyOta(await res.json());
    } catch (err) {
        console.error('Failed to load update status:', err);
    }
}

function applyOta(data) {
    otaStatus = data;

    fwCurrent.textContent = data.current || '—';
    fwLatest.textContent = data.latest || (data.state === 'available' ? 'unknown version' : '—');

    fwAutoInput.checked = !!data.autoUpdate;
    // Don't yank the field out from under someone who is mid-edit.
    if (document.activeElement !== fwUrlInput) fwUrlInput.value = data.url || '';

    fwStatus.textContent = data.message || 'Idle';
    fwStatus.classList.toggle('error', data.state === 'error');
    fwStatus.classList.toggle('ready', data.state === 'available' || data.state === 'success');

    fwNotes.textContent = data.notes || '';
    fwNotes.classList.toggle('hidden', !data.notes);

    const busy = !!data.busy;
    const downloading = data.state === 'downloading';

    fwCheckBtn.disabled = busy || data.supported === false || data.state === 'success';
    fwInstallBtn.classList.toggle('hidden', data.state !== 'available');
    fwInstallBtn.disabled = busy || data.supported === false;

    fwProgress.classList.toggle('hidden', !downloading);
    if (downloading) {
        // progress < 0 means the server sent no Content-Length.
        const indeterminate = !(data.progress >= 0);
        fwProgressBar.classList.toggle('indeterminate', indeterminate);
        fwProgressBar.style.width = indeterminate ? '' : data.progress + '%';
    }

    if (data.supported === false) {
        fwStatus.textContent =
            'This build has no OTA partition — reflash over USB with an OTA partition scheme to enable updates.';
        fwStatus.classList.add('error');
    }

    // SSE dies the moment the clock reboots, so fall back to polling whenever
    // something is in flight and watch for the device coming back up.
    if (busy && !otaPollTimer) {
        otaPollTimer = setInterval(loadOta, 2000);
    } else if (!busy && otaPollTimer) {
        clearInterval(otaPollTimer);
        otaPollTimer = null;
    }
    if (data.state === 'success') waitForReboot();
}

// After a successful flash the clock restarts. Poll until it answers again,
// then reload so the page picks up whatever the new firmware serves.
function waitForReboot() {
    if (otaRebootTimer) return;
    if (otaPollTimer) {
        clearInterval(otaPollTimer);
        otaPollTimer = null;
    }
    fwStatus.textContent = 'Update installed — the clock is restarting…';
    fwStatus.classList.remove('error');
    fwStatus.classList.add('ready');
    fwCheckBtn.disabled = true;
    fwInstallBtn.disabled = true;

    otaRebootTimer = setInterval(async () => {
        try {
            const res = await fetch('/api/ota', { cache: 'no-store' });
            if (res.ok) {
                clearInterval(otaRebootTimer);
                otaRebootTimer = null;
                location.reload();
            }
        } catch (err) {
            /* still rebooting - keep waiting */
        }
    }, 3000);
}

async function otaPost(path) {
    try {
        const res = await fetch(path, { method: 'POST' });
        if (!res.ok) {
            fwStatus.textContent = await res.text();
            fwStatus.classList.add('error');
            return;
        }
        fwCheckBtn.disabled = true;
        fwInstallBtn.disabled = true;
        if (!otaPollTimer) otaPollTimer = setInterval(loadOta, 2000);
    } catch (err) {
        fwStatus.textContent = 'Could not reach the clock: ' + err.message;
        fwStatus.classList.add('error');
    }
}

fwCheckBtn.addEventListener('click', () => {
    fwStatus.textContent = 'Checking for updates…';
    fwStatus.classList.remove('error', 'ready');
    otaPost('/api/ota/check');
});

fwInstallBtn.addEventListener('click', () => {
    const target = otaStatus.latest ? 'version ' + otaStatus.latest : 'this firmware image';
    if (!confirm('Install ' + target + '?\n\nThe clock will download the new firmware and restart. '
        + 'Do not unplug it until it comes back.')) return;
    otaPost('/api/ota/install');
});

fwAutoInput.addEventListener('change', function () {
    currentSettings.autoUpdate = this.checked;
    saveSettings();
});

fwUrlInput.addEventListener('change', function () {
    currentSettings.otaUrl = this.value.trim();
    saveSettings();
    loadOta();
});

loadOta();

const alarmsContainer = document.getElementById('alarms');
const addAlarmButton = document.getElementById('addAlarm');




// Function to create an alarm element
function createAlarm(alarmData) {
    const alarmDiv = document.createElement('div');
    alarmDiv.className = 'alarm';

    alarmDiv.innerHTML = `
        <label>
            Time: <input  class="alarm-time-input" type="time" name="alarmTime[]" value="${alarmData.hour.toString().padStart(2, '0')}:${alarmData.minute.toString().padStart(2, '0')}">
        </label>
        <div class="switch-row">
            <span> Alarm Active </span>
            <div class="switch">
                <input type="checkbox" class="settings-switch" id="alarmOn" ${alarmData.active ? 'checked' : ''}>
                <span class="slider-round"></span>
            </div>
            <span> LED Fades On </span>
            <div class="switch">
                <input type="checkbox" class="settings-switch" id="FadeOn" ${alarmData.fadeOn ? 'checked' : ''}>
                <span class="slider-round"></span>
            </div>
        </div>
        <div name="dayBanner">Days of the Week:</div>
        <div class="checkbox-group">
            <label><input type="checkbox" name="alarmDays[]" value="1" ${alarmData.days.includes('1') ? 'checked' : ''}> Monday</label>
            <label><input type="checkbox" name="alarmDays[]" value="2" ${alarmData.days.includes('2') ? 'checked' : ''}> Tuesday</label>
            <label><input type="checkbox" name="alarmDays[]" value="3" ${alarmData.days.includes('3') ? 'checked' : ''}> Wednesday</label>
            <label><input type="checkbox" name="alarmDays[]" value="4" ${alarmData.days.includes('4') ? 'checked' : ''}> Thursday</label>
            <label><input type="checkbox" name="alarmDays[]" value="5" ${alarmData.days.includes('5') ? 'checked' : ''}> Friday</label>
            <label><input type="checkbox" name="alarmDays[]" value="6" ${alarmData.days.includes('6') ? 'checked' : ''}> Saturday</label>
            <label><input type="checkbox" name="alarmDays[]" value="0" ${alarmData.days.includes('0') ? 'checked' : ''}> Sunday</label>
        </div>
        <div>
            Volume:
            <input type="range" name="alarmVolume[]" min="0" max="1" step="0.01" value="${alarmData.volume}">
            <span class="volume-value">
            ${alarmData.volume}
            </span>
        </div>
        <div>
            Song:
            <select class="song-select" name="song-select"></select>
        </div>
        <div>
            Colour:
            <select class="colour-select" name="colour-select"></select>
        </div>
        <button type="button" class="remove-alarm">Remove Alarm</button>
    `;

    function populateSelect(select, values, selectedValue) {
        select.innerHTML = '';
        values.forEach(value => {
            const option = new Option(value, value, false, value === selectedValue);
            select.add(option);
        });
    }

    const removeButton = alarmDiv.querySelector('.remove-alarm');
    removeButton.addEventListener('click', () => {
        currentSettings.alarms =
            currentSettings.alarms.filter(a => a !== alarmData);
        alarmsContainer.removeChild(alarmDiv);
        saveSettings();
    });

    alarmsContainer.appendChild(alarmDiv);

    const SongSelect = alarmDiv.querySelector('.song-select');
    populateSelect(SongSelect, availableSongs, alarmData.song);

    const ColourSelect = alarmDiv.querySelector('.colour-select');
    const availableColours = ['Custom', 'Red', 'Green', 'Blue', 'Yellow', 'Magenta', 'Cyan', 'White', 'Rainbow'];
    populateSelect(ColourSelect, availableColours, alarmData.colour);
    ColourSelect.addEventListener('change', e => {
        alarmData.colour = e.target.value;
        saveSettings();
    });
    SongSelect.addEventListener('change', e => {
        alarmData.song = e.target.value;
        saveSettings();
    });
    const timeInput = alarmDiv.querySelector('.alarm-time-input');
    timeInput.addEventListener('change', e => {
        alarmData.hour = Number(e.target.value.split(':')[0]);
        alarmData.minute = Number(e.target.value.split(':')[1]);
        saveSettings();
    });

    const volumeInput = alarmDiv.querySelector('input[type="range"]');
    volumeInput.addEventListener('change', e => {
        alarmData.volume = Number(e.target.value);
            saveSettings();
    });
    volumeInput.addEventListener('input', e => {
        alarmDiv.querySelector(".volume-value").textContent = e.target.value;
    });

    const fadeOnInput = alarmDiv.querySelector('input[id="FadeOn"]');
    fadeOnInput.addEventListener('change', e => {
        alarmData.fadeOn = e.target.checked;
        saveSettings();
    });
    const activeInput = alarmDiv.querySelector('input[id="alarmOn"]');
    activeInput.addEventListener('change', e => {
        alarmData.active = e.target.checked;
        saveSettings();
    });
    const dayCheckboxes = alarmDiv.querySelectorAll('input[name="alarmDays[]"]');
    dayCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const selectedDays = [];
            dayCheckboxes.forEach(cb => {
                if (cb.checked) selectedDays.push(cb.value);
            });
            alarmData.days = selectedDays;
            saveSettings();
        });
    });
}

// Add button functionality to create new alarms
addAlarmButton.addEventListener('click', () => {
    const newAlarm = {
        hour: 6,
        minute: 30,
        days: ['2', '3', '4', '5', '6', '0', '1'],
        volume: currentSettings.volume,
        song: currentSettings.song,
        colour: currentSettings.colour,
        fadeOn: currentSettings.fadeOn,
        active: currentSettings.alarmOn
    };

    currentSettings.alarms.push(newAlarm);
    createAlarm(newAlarm);
    saveSettings();
});

document.querySelector('.song-select').addEventListener('change', e => {
    currentSettings.song = e.target.value;
    saveSettings();
});
