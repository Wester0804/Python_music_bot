自製 Discord 音樂機器人，能夠從 Youtube 撥放音樂並支援基本功能

功能：
- `/search_song`：尋找你想要的歌曲
- `/join`：讓機器人加入語音頻道
- `/play`：播放音樂
- `/pause`：暫停播放
- `/resume`：繼續播放
- `/skip`：略過這首歌
- `/list`：顯示目前的播放列表
- `/stop`：停止播放
- `/shutdown`：離開語音頻道

需求：
- Python 3.8+
- 一個 Discord Bot Token（[申請方式](https://discord.com/developers/applications)）

  你的 Discord Bot Token 放入 main.py 的 client.run("YOUR_BOT_TOKEN") 
  
- [FFmpeg](https://ffmpeg.org/)（音訊處理必需）
