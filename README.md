# Hospital Fall Detection System

A real-time AI-powered fall detection system using OpenAI's vision models and Telegram notifications for hospital environments.

## Features

- **Real-time fall detection** using OpenAI GPT-4 Vision
- **Multithreaded analysis** every 5 seconds for optimal performance
- **Terminal logging** - always displays fall detection results in console
- **Optional Telegram notifications** with evidence images (configurable via USE_TELE_ALERT)
- **Evidence collection** - automatically saves frames when falls are detected
- **Cooldown system** to prevent alert spam
- **Live camera monitoring** with timestamp overlay

## System Requirements

- Python 3.8+
- OpenCV compatible camera (USB webcam, IP camera, etc.)
- OpenAI API account
- Telegram Bot (optional but recommended)

## Installation

1. **Clone/Download the project**
```bash
cd video_understading
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp env_template.txt .env
```

Edit the `.env` file with your credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
USE_TELE_ALERT=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

## Configuration Setup

### 1. OpenAI API Key
- Go to [OpenAI API](https://platform.openai.com/api-keys)
- Create a new API key
- Add it to your `.env` file

### 2. Telegram Bot (Optional)
- Set `USE_TELE_ALERT=true` in your `.env` file to enable Telegram notifications
- Set `USE_TELE_ALERT=false` to disable Telegram (fall detection logs will still appear in terminal)
- If enabled:
  - Message [@BotFather](https://t.me/botfather) on Telegram
  - Create a new bot with `/newbot`
  - Get your bot token
  - Get your chat ID by messaging your bot and visiting: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

### 3. Camera Setup
- Connect USB camera or configure IP camera
- Default uses camera index 0 (first camera)
- Modify `camera_index` in `fall_detection_system.py` if needed

## Usage

### 1. Test the System
```bash
python test_system.py
```
This will verify:
- Camera connectivity
- OpenAI API connection
- Telegram bot functionality

### 2. Run the Fall Detection System
```bash
python fall_detection_system.py
```

### 3. Monitor the System
- A window will show the live camera feed
- Timestamp overlay shows current time
- Console shows analysis logs every 5 seconds
- Press 'q' in the camera window to quit

## How It Works

### Detection Process
1. **Frame Capture**: Continuously captures frames from camera
2. **Buffer Management**: Maintains last 10 seconds of frames
3. **Periodic Analysis**: Every 5 seconds, analyzes recent frames using OpenAI GPT-4 Vision
4. **Fall Detection**: AI determines if a fall has occurred based on visual analysis
5. **Alert System**: Sends Telegram notification and saves evidence if fall detected
6. **Cooldown**: 30-second cooldown prevents alert spam

### AI Analysis
The system uses OpenAI's GPT-4 Vision model to analyze frames for:
- Sudden position changes (upright to horizontal)
- Rapid downward movement
- Person lying on floor in distress
- Loss of balance or collapse
- Emergency situations

### Optimization Features
- **Multithreading**: Analysis runs in background threads
- **Frame compression**: JPEG compression reduces API costs
- **Selective frame analysis**: Analyzes 5 frames max per detection cycle
- **Smart buffering**: Only keeps recent frames in memory

## File Structure

```
video_understading/
├── fall_detection_system.py    # Main system
├── test_system.py             # System testing
├── detection.py               # Original detection script
├── camera.py                  # Original camera script
├── requirements.txt           # Dependencies
├── env_template.txt          # Environment template
├── README.md                 # Documentation
└── evidence/                 # Auto-created for evidence images
```

## Troubleshooting

### Common Issues

1. **Camera not found**
   - Check camera connection
   - Try different camera index (0, 1, 2...)
   - Ensure camera drivers are installed

2. **OpenAI API errors**
   - Verify API key is correct
   - Check account balance/credits
   - Ensure stable internet connection

3. **Telegram not working**
   - Verify bot token and chat ID
   - Check bot permissions
   - Test with test_system.py first

4. **False positives**
   - Adjust analysis prompt in `fall_detection_system.py`
   - Modify cooldown period
   - Fine-tune frame selection

### Performance Tuning

- **Reduce analysis frequency**: Increase `analysis_interval` (default: 5 seconds)
- **Adjust frame quality**: Modify JPEG quality in `frames_to_base64()`
- **Change frame count**: Modify `max_frames` parameter (default: 5)
- **Optimize camera resolution**: Adjust in `initialize_camera()`

## System Monitoring

### Logs
The system provides detailed logging:
- Frame capture status
- Analysis results
- Alert notifications
- Error messages

### Evidence Collection
When falls are detected:
- Frame saved to `evidence/` folder
- Telegram notification sent with image
- Timestamp recorded for review

## Deployment Notes

### Production Considerations
- Use dedicated hardware for reliability
- Implement log rotation for long-term operation
- Consider backup notification methods
- Regular system health monitoring
- Camera positioning optimization

### Security
- Secure API keys and tokens
- Use HTTPS for telegram webhooks
- Implement access controls
- Regular security updates

## Contributing

Feel free to contribute improvements:
- Enhanced AI prompts for better accuracy
- Additional notification channels
- Performance optimizations
- UI improvements

## License

This project is for educational and research purposes. Ensure compliance with privacy laws when deploying in healthcare environments.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run `test_system.py` to identify problems
3. Review system logs for error details 