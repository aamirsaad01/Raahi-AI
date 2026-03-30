# 🔄 Setting Up Automatic NDMA Polling

## Option 1: Continuous Poller (Terminal Window)

Keep a terminal window open and run:

```bash
cd backend_scripts
python ndma_poller.py
```

This will:
- ✅ Run continuously
- ✅ Check for new alerts every 1 hour (default)
- ✅ Automatically save new alerts to database
- ✅ Skip duplicates automatically
- ✅ Log all activity

**To stop:** Press `Ctrl+C`

**Custom interval:**
```bash
# Check every 30 minutes
python ndma_poller.py --interval 0.5

# Check every 6 hours
python ndma_poller.py --interval 6
```

---

## Option 2: Windows Task Scheduler (Recommended for Windows)

Set it to run automatically in the background:

### Step-by-Step:

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**
   - Click "Create Basic Task" in the right panel
   - Name: `NDMA Poller`
   - Description: `Automatically scrape NDMA advisories`

3. **Set Trigger**
   - Choose "Daily" or "When the computer starts"
   - Set time (e.g., 9:00 AM)
   - Or choose "Repeat task every: 1 hour"

4. **Set Action**
   - Action: "Start a program"
   - Program/script: `python` (or full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\python.exe`)
   - Add arguments: `D:\Raahi-AI\Raahi-AI\backend_scripts\ndma_poller.py --once`
   - Start in: `D:\Raahi-AI\Raahi-AI\backend_scripts`

5. **Finish**
   - Check "Open the Properties dialog"
   - In Properties → Settings:
     - ✅ Check "Run task as soon as possible after a scheduled start is missed"
     - ✅ Check "If the task fails, restart every: 10 minutes"
     - ✅ Check "Stop the task if it runs longer than: 5 minutes" (optional)

**For hourly polling:**
- Create a task that runs every hour
- Use: `python ndma_poller.py --once` (runs once and exits, Task Scheduler will run it again next hour)

---

## Option 3: Windows Service (Advanced)

For a true background service, you can use `nssm` (Non-Sucking Service Manager):

1. Download NSSM: https://nssm.cc/download
2. Extract and run `nssm.exe install NDMA_Poller`
3. Configure:
   - Path: `python.exe` (full path)
   - Startup directory: `D:\Raahi-AI\Raahi-AI\backend_scripts`
   - Arguments: `ndma_poller.py`
4. Start the service

---

## Option 4: Linux systemd Service (For Linux/Mac)

Create `/etc/systemd/system/ndma-poller.service`:

```ini
[Unit]
Description=NDMA Poller Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Raahi-AI/backend_scripts
ExecStart=/usr/bin/python3 /path/to/Raahi-AI/backend_scripts/ndma_poller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable ndma-poller
sudo systemctl start ndma-poller
sudo systemctl status ndma-poller  # Check status
```

---

## Quick Comparison

| Method | Pros | Cons |
|--------|------|------|
| **Continuous Poller** | Simple, easy to monitor | Terminal must stay open |
| **Task Scheduler** | Runs in background, reliable | Windows only, needs setup |
| **Systemd Service** | Professional, auto-restart | Linux/Mac only |
| **Manual Run** | Full control | Must remember to run |

---

## Recommended Setup

**For Development:**
- Use **Option 1** (Continuous Poller) - easy to monitor and stop

**For Production:**
- Use **Option 2** (Task Scheduler) on Windows
- Use **Option 4** (systemd) on Linux

---

## Testing Automatic Polling

After setting up, verify it's working:

```bash
# Check database after a few hours
python backend_scripts/view_hazard_alerts.py

# Or check logs if using Task Scheduler
# View Task Scheduler → NDMA Poller → History
```

---

## Troubleshooting

### Task Scheduler not running?
- Check Task Scheduler → Task Scheduler Library → NDMA Poller → History
- Verify Python path is correct
- Check "Run whether user is logged on or not" in task properties

### Service not starting?
- Check service logs
- Verify file paths are correct
- Ensure database connection works

### Want to change interval?
- Edit the task in Task Scheduler
- Or modify the `--interval` argument

