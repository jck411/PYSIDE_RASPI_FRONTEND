# Developer Notes: Alarm System Implementation

This document provides technical insights and tips for developers working on the alarm system. It complements the user-facing documentation in `frontend/qml/ALARM_SYSTEM_DOCUMENTATION.md`.

## Architecture Overview

The alarm system follows a timer-based approach rather than periodic checking:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  QML Interface  │◄────┤ AlarmController │◄────┤  AlarmManager   │
│  (UI Layer)     │     │  (Bridge Layer) │     │  (Data Layer)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                       ▲                        ▲
        │                       │                        │
        ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   QML Models    │     │  Python Models  │     │  Timer System   │
│  (Data Binding) │     │ (Data Transfer) │     │ (Scheduling)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Key Implementation Details

### Timer-Based Alarm Triggering

The system uses dedicated QTimers for each alarm instead of periodic checking:

```python
# In AlarmManager._schedule_alarm
timer = QTimer()
timer.setSingleShot(True)
timer.setInterval(ms_until_trigger)
timer.timeout.connect(lambda: self._handle_alarm_triggered(alarm_id))
self._alarm_timers[alarm_id] = timer
timer.start()
```

**Benefits:**
- Precise triggering at exact alarm times
- Minimal CPU usage (only active when needed)
- Scales efficiently with many alarms

**Potential Challenges:**
- System time changes can affect timer accuracy
- Sleep/hibernate can disrupt timers
- Timer limits on some platforms

### Audio Playback System

The audio system uses a combination of Qt's audio classes and custom buffer management:

```python
# Key components
self.audioDevice = QueueAudioDevice()  # Custom QIODevice subclass
self.audioSink = QAudioSink(device, audio_format)  # Qt audio output
```

**Critical Insights:**
1. The audio device must be reset between alarm sounds:
   ```python
   def _reset_audio_device(self):
       # Stop the audio sink if it's active
       if self.audioSink.state() == QAudio.State.ActiveState:
           self.audioSink.stop()
           
       # Clear the buffer
       self.audioDevice.clear_buffer()
       
       # Close and reopen the audio device
       self.audioDevice.close()
       self.audioDevice.open(QIODevice.OpenModeFlag.ReadOnly)
       
       # Restart the audio sink
       self.audioSink.start(self.audioDevice)
   ```

2. Avoid using asyncio in QML-triggered methods:
   ```python
   # WRONG - will cause "no running event loop" errors
   @Slot()
   def play_alarm_sound(self):
       asyncio.create_task(self.play_alarm_sound_async())
   
   # RIGHT - use synchronous methods for QML callbacks
   @Slot()
   def play_alarm_sound(self):
       self._reset_audio_device()
       with open(alarm_path, 'rb') as f:
           chunk = f.read()
           self.audioDevice.writeData(chunk)
   ```

### Data Flow Between Python and QML

The system uses a bridge pattern to maintain compatibility:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  QML Format     │     │ Controller      │     │ Manager Format  │
│  {              │     │ _convert_alarm_ │     │  {              │
│   name: "Wake", │◄───►│  to_qml()       │◄───►│   label: "Wake",│
│   enabled: true │     │ _convert_recur_ │     │   is_enabled:   │
│   recurrence:   │     │  rence_to_days()│     │   days_of_week: │
│  }              │     └─────────────────┘     │  }              │
└─────────────────┘                             └─────────────────┘
```

**Key Conversion Points:**
- `label` in backend → `name` in QML
- `is_enabled` in backend → `enabled` in QML
- `days_of_week` in backend → `recurrence` in QML

## Common Pitfalls and Solutions

### 1. Audio Playback Issues

**Problem:** Audio doesn't play for subsequent alarms.

**Solution:** Reset the audio device between playbacks:
```python
def play_alarm_sound(self):
    # Reset the audio device and sink to ensure it's in a clean state
    self._reset_audio_device()
    
    # Then play the sound
    with open(alarm_path, 'rb') as f:
        chunk = f.read()
        self.audioDevice.writeData(chunk)
```

### 2. Asyncio in QML Callbacks

**Problem:** "No running event loop" errors when using asyncio in QML-triggered methods.

**Solution:** Use synchronous methods for QML callbacks:
```python
# Instead of:
@Slot()
def some_method(self):
    asyncio.create_task(self.some_async_method())

# Use:
@Slot()
def some_method(self):
    # Direct synchronous implementation
    # Or use a thread if needed for long operations
    threading.Thread(target=self._thread_method).start()
```

### 3. Timer Accuracy Issues

**Problem:** Timers may not trigger at exact times due to system sleep or time changes.

**Solution:** Implement a time change detection system:
```python
# Pseudo-code for handling time changes
def _handle_system_time_changed(self, old_time, new_time):
    time_diff = new_time - old_time
    
    # If significant time change (more than a few seconds)
    if abs(time_diff) > 5:
        # Reschedule all timers
        for alarm_id in self._alarm_timers:
            self._cancel_alarm_timer(alarm_id)
            alarm = self.get_alarm(alarm_id)
            if alarm and alarm.get('is_enabled', False):
                self._schedule_alarm(alarm)
```

### 4. QML Model Updates

**Problem:** QML ListView doesn't update when model data changes.

**Solution:** Ensure proper model reset signals:
```python
# In AlarmModel
def setAlarms(self, alarms):
    self.beginResetModel()
    self._alarms = alarms
    self.endResetModel()
```

And in QML:
```qml
// Force model refresh if needed
function onAlarmsChanged() {
    alarmListView.model = null
    alarmListView.model = AlarmController.alarmModel()
}
```

## Performance Optimization Tips

### 1. Timer Scheduling

For very distant alarms (e.g., months away), consider using a placeholder timer:

```python
# Pseudo-code for optimizing distant alarms
if ms_until_trigger > ONE_DAY_MS:
    # Set a placeholder timer for 1 day
    timer.setInterval(ONE_DAY_MS)
    timer.timeout.connect(lambda: self._reschedule_distant_alarm(alarm_id))
else:
    # Normal scheduling
    timer.setInterval(ms_until_trigger)
    timer.timeout.connect(lambda: self._handle_alarm_triggered(alarm_id))
```

### 2. Audio Buffer Management

Optimize audio buffer size for better performance:

```python
# For large audio files, consider chunking
def play_large_audio_file(self, file_path):
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)  # e.g., 8192 bytes
            if not chunk:
                break
            self.audioDevice.writeData(chunk)
```

### 3. Model Updates

Minimize model resets for better UI performance:

```python
# For single item changes
def updateAlarmInModel(self, index, alarm):
    # Instead of full model reset
    self._alarms[index] = alarm
    modelIndex = self.index(index, 0)
    self.dataChanged.emit(modelIndex, modelIndex)
```

## Testing Strategies

### 1. Testing Alarm Triggers

Create alarms with short intervals for testing:

```python
# Test function to create an alarm 10 seconds from now
def create_test_alarm():
    now = datetime.now()
    test_minute = (now.minute + 1) % 60
    test_hour = now.hour + (1 if test_minute < now.minute else 0) % 24
    
    return alarm_manager.add_alarm(
        hour=test_hour,
        minute=test_minute,
        label="Test Alarm",
        days_of_week={now.weekday()},
        is_enabled=True
    )
```

### 2. Testing Audio Playback

Test audio with different file formats and sizes:

```python
# Test different audio formats
def test_audio_playback():
    audio_files = [
        "../sounds/alarm.raw",
        "../sounds/beep.wav",
        "../sounds/chime.wav"
    ]
    
    for file in audio_files:
        audio_manager.play_sound_file(file)
        time.sleep(2)  # Wait for playback
```

### 3. Testing Time Changes

Simulate time changes to test timer rescheduling:

```python
# Pseudo-code for testing time changes
def test_time_change_handling():
    # Create test alarms
    create_test_alarms()
    
    # Simulate time change event
    old_time = datetime.now()
    new_time = old_time + timedelta(hours=1)
    alarm_manager._handle_system_time_changed(old_time, new_time)
    
    # Verify timers were rescheduled correctly
    verify_timer_schedules()
```

## Future Development Considerations

### 1. Adding Snooze Functionality

Implement snooze by creating temporary one-time alarms:

```python
def snooze_alarm(self, alarm_id, snooze_minutes=5):
    # Get the original alarm
    original_alarm = self.get_alarm(alarm_id)
    if not original_alarm:
        return
        
    # Calculate snooze time
    now = datetime.now()
    snooze_time = now + timedelta(minutes=snooze_minutes)
    
    # Create a one-time alarm
    return self.add_alarm(
        hour=snooze_time.hour,
        minute=snooze_time.minute,
        label=f"{original_alarm.get('label', 'Alarm')} (Snoozed)",
        days_of_week={now.weekday()},  # Just today
        is_enabled=True
    )
```

### 2. Adding Custom Alarm Sounds

Extend the system to support custom alarm sounds:

```python
# In AlarmManager
def add_alarm(self, hour, minute, label, days_of_week, is_enabled=True, sound_file="default"):
    # Add sound_file parameter to alarm data
    alarm = {
        'id': str(uuid.uuid4()),
        'hour': hour,
        'minute': minute,
        'label': label,
        'days_of_week': days_of_week,
        'is_enabled': is_enabled,
        'sound_file': sound_file  # New field
    }
    # ...rest of method
```

Then in AudioManager:

```python
def play_alarm_sound(self, sound_file="default"):
    # Determine the actual file path based on sound_file
    if sound_file == "default":
        file_path = os.path.join(os.path.dirname(__file__), '../sounds/alarm.raw')
    else:
        file_path = os.path.join(os.path.dirname(__file__), f'../sounds/{sound_file}')
    
    # Play the sound
    # ...
```

### 3. Implementing Gradual Volume Increase

Add a gradual volume increase for gentler wake-up:

```python
def play_alarm_with_gradual_volume(self):
    # Reset audio device
    self._reset_audio_device()
    
    # Start with low volume
    self.audioSink.setVolume(0.1)
    
    # Play the sound
    with open(alarm_path, 'rb') as f:
        chunk = f.read()
        self.audioDevice.writeData(chunk)
    
    # Gradually increase volume
    for vol in range(1, 10):
        # Use a timer to delay volume changes
        QTimer.singleShot(vol * 1000, lambda v=vol: self.audioSink.setVolume(v/10))
```

## Debugging Tips

### 1. Audio Issues

Add detailed logging to diagnose audio problems:

```python
def _reset_audio_device(self):
    logger.info("[AudioManager] Resetting audio device and sink")
    logger.info(f"[AudioManager] Audio sink state before reset: {self.audioSink.state()}")
    logger.info(f"[AudioManager] Audio buffer size before reset: {len(self.audioDevice.audio_buffer)}")
    
    # Reset logic here
    
    logger.info(f"[AudioManager] Audio sink state after reset: {self.audioSink.state()}")
    logger.info(f"[AudioManager] Audio device open state after reset: {self.audioDevice.isOpen()}")
```

### 2. Timer Issues

Debug timer scheduling with detailed logging:

```python
def _schedule_alarm(self, alarm):
    # Calculate next trigger time
    next_trigger = self._calculate_next_trigger(alarm)
    logger.debug(f"Next trigger time for alarm {alarm['id']}: {next_trigger}")
    
    # Calculate milliseconds until trigger
    now = datetime.now()
    delta = next_trigger - now
    ms_until_trigger = int(delta.total_seconds() * 1000)
    logger.debug(f"Milliseconds until trigger: {ms_until_trigger}")
    
    # Create and start timer
    # ...
```

### 3. QML-Python Communication

Debug signal connections with logging:

```python
# In AlarmController constructor
def __init__(self):
    # ...
    self._alarm_manager.alarmTriggered.connect(self._log_and_handle_alarm_triggered)
    # ...

def _log_and_handle_alarm_triggered(self, alarm):
    logger.debug(f"Received alarmTriggered signal with alarm: {alarm}")
    self._handle_alarm_triggered_from_manager(alarm)
```

## Code Organization Best Practices

### 1. Separation of Concerns

Maintain clear separation between components:

- **AlarmManager**: Data storage, timer management
- **AlarmController**: Bridge between Python and QML
- **AudioManager**: Audio playback only
- **QML Components**: UI presentation only

### 2. Error Handling

Implement robust error handling throughout:

```python
def play_alarm_sound(self):
    try:
        # Reset audio device
        try:
            self._reset_audio_device()
        except Exception as e:
            logger.error(f"[AudioManager] Error resetting audio device: {e}")
            # Fall back to creating a new device
            self.setup_audio()
        
        # Play sound
        try:
            with open(alarm_path, 'rb') as f:
                chunk = f.read()
                self.audioDevice.writeData(chunk)
        except FileNotFoundError:
            logger.error(f"[AudioManager] Alarm sound file not found: {alarm_path}")
            # Fall back to a beep sound
            self._play_fallback_sound()
        except Exception as e:
            logger.error(f"[AudioManager] Error playing alarm sound: {e}")
    except Exception as e:
        logger.error(f"[AudioManager] Unhandled error in play_alarm_sound: {e}")
```

### 3. Configuration Management

Use a centralized configuration system:

```python
# In a config.py file
ALARM_CONFIG = {
    "default_sound": "alarm.raw",
    "snooze_duration_minutes": 5,
    "volume_level": 0.8,
    "gradual_volume_increase": True,
    "max_alarms": 50
}

# Then in code
from config import ALARM_CONFIG

def play_alarm_sound(self):
    # Use configuration
    self.audioSink.setVolume(ALARM_CONFIG["volume_level"])
    # ...
```

## Conclusion

The alarm system's redesign to use a timer-based approach has significantly improved efficiency and reliability. By following the guidelines in this document, future developers can maintain and extend the system while avoiding common pitfalls.

Remember these key principles:
1. Use dedicated timers instead of periodic checking
2. Reset audio devices between playbacks
3. Use synchronous methods for QML callbacks
4. Maintain proper separation of concerns
5. Implement robust error handling

For user-facing documentation, refer to `frontend/qml/ALARM_SYSTEM_DOCUMENTATION.md`.
