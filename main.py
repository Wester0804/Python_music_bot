import asyncio
import discord
from discord.ext import commands,tasks
from discord import app_commands
from discord.utils import get
import os
import yt_dlp as youtube_dl
from youtubesearchpython import *

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/',intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''

result = None
search_ctx = None
music_queue = []
search_embed = discord.Embed(title='搜尋結果', description='點擊歌曲標題下連結可在瀏覽器開啟', color=0xff0000)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)
    
    music_queue.clear()

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.2):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        videoname = data.get('title', None)
        music_queue.append([filename,videoname])


class YTSearch():
    def __init__(self, keyword):
        self.search = CustomSearch(keyword, VideoSortOrder.relevance, limit=5)
    def getChannelName(self, index):
        return self.search.result()['result'][index]['channel']['name']
    def getLink(self, index):
        return self.search.result()['result'][index]['link']
    def getTitle(self, index):
        return self.search.result()['result'][index]['title']
    def nextPage(self):
        self.search.next()


@bot.hybrid_command(name='search_song', help='尋找歌曲')
async def search(ctx, keyword):
    global result, resultMsg
    currentKeyword = keyword
    if (search_embed.fields == []) | (currentKeyword != str(search_embed.title)[:-5]):
        result = YTSearch(keyword)
    search_embed.clear_fields()
    search_embed.title = keyword + '的搜尋結果'
    for index in range(5): #limit of YTSearch
        channelName = result.getChannelName(index)
        videoLink = result.getLink(index)
        videoTitle = result.getTitle(index)
        resultTitle = str(index + 1) + '\t-\t' + videoTitle + '\n'
        search_embed.add_field(name=resultTitle, value=f'{"頻道：" + channelName}' + '\t' + f'[YT連結]({videoLink})', inline= False)
    resultMsg = await ctx.send(embed = search_embed)
    await resultMsg.add_reaction('⏩')

    def check(reaction, user):
        return str(reaction.emoji) == '⏩' and reaction.count > 1

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=10.0, check=check)
    except asyncio.TimeoutError:
        print('timeout')
    else:
        # print(resultMsg.id)
        # print(reaction)
        # print(user)
        print('success')
        result.nextPage()
        await search(ctx, keyword)

@bot.hybrid_command(name='join', help='讓機器人加入語音')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f"{ctx.message.author.name} 請先加入語音頻道")
        return
    else:
        channel = ctx.message.author.voice.channel
        await ctx.send(f'已加入語音頻道: **{ctx.message.author.voice.channel}**')
    await channel.connect()

@bot.hybrid_command(name='leave', help='離開語音')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        music_queue.clear()
        await ctx.send('離開語音')
    else:
        await ctx.send("機器人並沒有加入語音頻道")


def nextSong():
    if len(music_queue) > 1:
        voice = discord.utils.get(bot.voice_clients)
        del music_queue[0]
        print(music_queue)
        voice.play(discord.FFmpegPCMAudio(executable="D:\\program\\wawa\\wawabot\\wawabot\\ffmpeg-6.1-full_build\\bin\\ffmpeg.exe", source=f"{music_queue[0][0]}"),after = lambda x: nextSong())

def endsong():
    voice = discord.utils.get(bot.voice_clients)
    music_queue.clear()
    if voice.is_playing() :
        voice.stop()
        

@bot.hybrid_command(name='play', help='播歌')
async def play(ctx,url):
    # server = ctx.message.guild
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if voice_channel.is_playing():
        await ctx.send(f'**處理中請稍後**')
        await YTDLSource.from_url(url)
        print(music_queue)
        await ctx.send(f"{music_queue[-1][1]}已加入撥放清單")
    else:

        await ctx.send(f'**處理中請稍後**')

        await YTDLSource.from_url(url)
        print(music_queue)

        voice_channel.play(discord.FFmpegPCMAudio(executable="D:\\program\\wawa\\wawabot\\wawabot\\ffmpeg-6.1-full_build\\bin\\ffmpeg.exe", source=f"{music_queue[0][0]}"),after = lambda x: nextSong())
        
        await ctx.send(f'**正在播放：{music_queue[0][1]}**')


@bot.hybrid_command(name='pause', help='暫停歌')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send('已暫停播放歌曲')
    else:
        await ctx.send("目前並沒有播放歌曲")
    
@bot.hybrid_command(name='resume', help='恢復播放')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send('重新開始撥放')
    else:
        await ctx.send("現在並沒有歌曲，使用/play [URL]來加入歌曲")
    
@bot.hybrid_command(name='skip', help='下一首')
async def skip(ctx):
    voice_client = ctx.message.guild.voice_client
    if len(music_queue) > 1:
        await ctx.send(f'下一首\n現正撥放：{music_queue[1][1]}')
        voice_client.stop()

       
    else:
        voice_client.stop()
        await ctx.send("現無下一首歌曲，使用/play [URL]來加入歌曲")
    
@bot.hybrid_command(name='list', help='播放清單')
async def list(ctx):
    voice_client = ctx.message.guild.voice_client
    if len(music_queue) > 0:
        songlist = ''
        for song in music_queue:
            songlist += song[1]+'\n'
        await ctx.send(f'播放清單：\n{songlist}')
     
    else:
        voice_client.stop()
        await ctx.send("現在並沒有歌曲，使用/play [URL]來加入歌曲")

@bot.hybrid_command(name='stop', help='停止歌')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        endsong()
        await ctx.send('已停止歌曲')
    else:
        await ctx.send("機器人現在並沒有播放歌曲")

@bot.hybrid_command(name='shutdown', help='關閉Wawabot')
async def shutdown(ctx):
    await ctx.send('閃人掰掰')
    await bot.close()

if __name__ == "__main__" :
    bot.run("MTE3MzQ5MTY0OTQxNDk3MTM5Mg.Gil8lX.MzbwmztzjVsu2u4LCyeNPskhojP-qcuJZetvUs")
