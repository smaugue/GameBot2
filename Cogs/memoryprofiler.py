import discord
from discord.ext import commands
import sys
import gc
import tracemalloc
import psutil
from collections import Counter
from Packs.Botloader import owner_permission

class MemoryProfiler(commands.Cog):
    """Cog avancé pour monitorer l'utilisation mémoire et les objets Python"""

    def __init__(self, bot):
        self.bot = bot
        tracemalloc.start()  # Démarre le suivi mémoire

    @commands.command(name="memprofile")
    async def memprofile(self, ctx):
        if not owner_permission.check(ctx.author.id):
            return await ctx.reply("Vous ne disposez pas des autorisations nécessaires.")
        """
        Affiche la RAM utilisée, objets existants et qui les référence
        """
        # --- 1. RAM totale utilisée ---
        process = psutil.Process()
        mem_info = process.memory_info()
        rss = mem_info.rss / 1024**2  # Mo

        # --- 2. Compte des objets par type ---
        obj_count = Counter(type(obj).__name__ for obj in gc.get_objects())
        top_objects = obj_count.most_common(10)

        # --- 3. Taille mémoire des objets par type ---
        type_size = {}
        for obj in gc.get_objects():
            t = type(obj).__name__
            type_size[t] = type_size.get(t, 0) + sys.getsizeof(obj)
        top_size = sorted(type_size.items(), key=lambda x: x[1], reverse=True)[:10]

        # --- 4. Analyse des références d’objets importants ---
        ref_info = []
        for obj_type, _ in top_objects[:5]:  # top 5 types par nombre
            for obj in gc.get_objects():
                if type(obj).__name__ == obj_type:
                    # trouver les objets qui réfèrent cet objet
                    referrers = gc.get_referrers(obj)
                    # on ne garde que le type du referrer
                    ref_types = [type(r).__name__ for r in referrers]
                    ref_summary = Counter(ref_types).most_common(3)  # top 3 ref
                    ref_info.append((obj_type, sys.getsizeof(obj), ref_summary))
                    break  # un seul échantillon par type pour la lisibilité

        # --- 5. Top allocations tracemalloc ---
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        # --- 6. Message final ---
        msg = f"**RAM utilisée (RSS)** : {rss:.2f} Mo\n\n"
        msg += "**Top objets par nombre :**\n"
        for t, c in top_objects:
            msg += f"- {t}: {c}\n"

        msg += "\n**Top objets par taille (Mo) :**\n"
        for t, size in top_size:
            msg += f"- {t}: {size/1024**2:.2f} Mo\n"

        msg += "\n**Références d'objets (exemple top 5 types) :**\n"
        for t, size, refs in ref_info:
            refs_str = ", ".join(f"{r[0]}({r[1]})" for r in refs)
            msg += f"- {t} ({size} bytes) référencé par: {refs_str}\n"

        msg += "\n**Top allocations tracemalloc :**\n"
        for stat in top_stats[:3]:
            msg += f"{stat}\n"

        # Envoi dans Discord
        await ctx.reply(msg, ephemeral=True)


async def setup(bot):
    await bot.add_cog(MemoryProfiler(bot))
