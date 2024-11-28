# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
from discord.ext import commands
from discord.ext.commands import Context
import yt_dlp as youtube_dl
import asyncio

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    @commands.hybrid_command(name='join', help='Fait rejoindre le bot à un canal vocal')
    async def join(self, ctx):
        await Music.ljoin(self, ctx)

    async def ljoin(self, ctx: Context,*,ir = "y"):
        if not ctx.message.author.voice:
            await ctx.send(f"Vous n'êtes pas connectez à un channel vocal.")
            return False
        channel = ctx.message.author.voice.channel
        if ctx.voice_client:
            if ctx.voice_client.is_playing() or len(self.queue) > 0:
                await ctx.send("Le bot est déjà en cour d'utilisation.")
                return False
            #elif ctx.voice_client.channel != channel.id:
            else:
                await ctx.voice_client.disconnect()
                await channel.connect(self_deaf=True)
        if ir == "y":
            await ctx.send(f'Connecté à {channel.name}.')
        return True

    @commands.hybrid_command(name='leave', help='Fait quitter le bot du canal vocal')
    async def leave(self, ctx):
        if not ctx.voice_client:
            await ctx.send('Le bot n\'est pas connecté à un canal vocal.')
            return
        await ctx.voice_client.disconnect()

    @commands.hybrid_command(name='play', help="Joue une musique à partir d'une URL ou de mots-clés.")
    async def play(self, ctx, *, url):
        if await Music.ljoin(self,ctx,ir="n") is False:
            return
        if not ctx.voice_client:
            return await ctx.send("Je ne suis pas connecté à un canal vocal.")
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Erreur: {e}') if e else self.play_next(ctx))
            self.queue.append(player)
            await ctx.send(f'🎶 Lecture de: **{player.title}**')

    @commands.hybrid_command(name='stop', help="Arrête la musique.")
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            self.queue = []
            await ctx.send("⏹ Musique arrêtée.")

    @commands.hybrid_command(name='skip', help="Passe à la musique suivante dans la file d'attente.")
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ Musique suivante...")
        else:
            await ctx.send("Aucune musique en cours de lecture.")

    def play_next(self, ctx):
        if len(self.queue) > 1:
            next_song = self.queue.pop(0)
            ctx.voice_client.play(next_song, after=lambda e: print(f'Erreur: {e}') if e else self.play_next(ctx))
        else:
            self.queue = []

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Tu n'es pas connecté à un canal vocal.")
                raise commands.CommandError("L'utilisateur n'est pas dans un canal vocal.")

    @commands.hybrid_command(name='queue', help="Montre la file d'attente actuelle.")
    async def queue_info(self, ctx):
        if self.queue:
            queue_titles = [song.title for song in self.queue]
            await ctx.send(f"🎶 File d'attente :\n" + "\n".join(queue_titles))
        else:
            await ctx.send("La file d'attente est vide.")

    @commands.hybrid_command(name='pause', help="Met en pause la musique.")
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ Musique mise en pause.")

    @commands.hybrid_command(name='resume', help="Reprend la lecture de la musique.")
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Musique reprise.")
