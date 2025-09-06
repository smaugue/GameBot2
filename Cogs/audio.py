import discord
from discord.ext import commands
from discord.ext.commands import Context

class Audio(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Join ---
    @commands.hybrid_command(name="join", description="Fait rejoindre le bot dans ton salon vocal.")
    @commands.guild_only()
    async def join(self, ctx: Context):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.reply("❌ Vous devez être connecté dans un salon vocal.")

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            if ctx.voice_client.channel.id == channel.id:
                return await ctx.reply("⚠️ Je suis déjà dans ce salon.")
            else:
                await ctx.voice_client.move_to(channel)
                return await ctx.reply(f"🔄 Déplacé dans {channel.mention}")

        await channel.connect(self_deaf=True)  # se mute côté sortie (à True mais debugage en cours)
        await ctx.reply(f"✅ Connecté à {channel.mention}")

    # --- Leave ---
    @commands.hybrid_command(name="leave", description="Fait quitter le bot du salon vocal.")
    @commands.guild_only()
    async def leave(self, ctx: Context):
        if ctx.voice_client is None:
            return await ctx.reply("❌ Je ne suis pas connecté à un salon vocal.")
        await ctx.voice_client.disconnect(force=True)
        await ctx.reply("👋 Déconnecté du salon vocal.")

    # --- Mute ---
    @commands.hybrid_command(name="mute", description="Met le bot en sourdine côté Discord.")
    @commands.guild_only()
    async def mute(self, ctx: Context):
        if ctx.voice_client is None:
            return await ctx.reply("❌ Je ne suis pas connecté à un salon vocal.")
        await ctx.guild.me.edit(mute=True, deafen=True)
        await ctx.reply("🔇 Bot mis en sourdine.")

    # --- Unmute ---
    @commands.hybrid_command(name="unmute", description="Rétablit le son du bot.")
    @commands.guild_only()
    async def unmute(self, ctx: Context):
        if ctx.voice_client is None:
            return await ctx.reply("❌ Je ne suis pas connecté à un salon vocal.")
        await ctx.guild.me.edit(mute=False, deafen=False)
        await ctx.reply("🔊 Bot rétabli.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Audio(bot))
