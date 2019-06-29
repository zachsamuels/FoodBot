from PIL import Image, ImageDraw, ImageChops, ImageEnhance
import math
import copy
import random
from io import BytesIO
import discord
from discord.ext import commands
import time
import numpy as np
import pickle
import asyncio
import sys

def sigmoid(i):
    return 9/(1 + math.exp(-i))
    
def connecting(point0, point1, m, hyp, itr: int = 0, r=0):
    x0, y0 = point0
    x1, y1 = point1
    if point0 == point1:
        return [point0 for _ in range(10)]
    link = []

    width, height = x1 - x0, y1 - y0

    def direction(a: int):
        return -1 if a < 0 else 1 if a > 0 else 0

    w, h = direction(width), direction(height)

    widths = tuple(range(x0, x1 + w, w)) if w != 0 else [x0]
    heights = tuple(range(y0, y1 + h, h)) if h != 0 else [y0]
    xyz = (widths, heights)

    if all(1 == len(i) for i in xyz):
        link.append((x0, y0))
        return link

    steps = len(max(xyz, key=len)) if itr <= 1 else itr
    literal_steps = steps - 1
    rotation = (r*(hyp/m))/steps
    rot = 0
    xyz = tuple((i, len(i) - 1) for i in xyz)
    s = int(steps/2)
    c = (128,128)
    diff = (x1-x0)/steps
    for i in range(-s,s):
        i = sigmoid(i)
        progress = i / literal_steps
        x = widths[int(progress * xyz[0][1] + .5)]
        y = heights[int(progress * xyz[1][1] + .5)]
        if rotation:
            if i != s:
                ni = sigmoid(p+1)
                np = ni / literal_steps
                diff = widths[int(np * xyz[0][1] + .5)] - x
            x, y = rotate((x,y), c, rot)
            rot+=rotation
            c = (c[0]+diff,c[1]+diff)
        link.append((x, y))
    return link

def rotate(coords, center, r):
    rp = (coords[0] - center[0], coords[1] - center[1])

    rotated_position = (
        math.cos(math.radians(r)) * rp[0] - math.sin(math.radians(r)) * rp[1],
        math.sin(math.radians(r)) * rp[0] + math.cos(math.radians(r)) * rp[1]
    )

    return (int(rotated_position[0] + center[0]), int(rotated_position[1] + center[1]))
 
def get_final(pixel, coords, inverse):
    x, y = coords
    if inverse:
     h = (765-sum(pixel))/3
    else:
     h= sum(pixel)/3
    side = h/math.sqrt(2)
    return (int(x+side), int(y+side)), h

def get_template(arr, r, m, inverse):
    template = {}
    i = 65535
    for rgb in reversed(arr):
        if rgb == (0,0,0):
            i-=1
            continue
        y, x = divmod(i, 256)
        final, h = get_final((rgb), (x,y), inverse)
        line = connecting((x,y), final, m, h, 10, r)
        template[(x,y)] = line
        i-=1
    return template
    
def process_depth(img, r, type, jiggle, inverse, blur, color, from_start):
    im = Image.new("RGB", (450, 450), "black")
    arr = img.getdata()
    if inverse:
     m = max((765-sum(rgb))/3 for rgb in arr)
    else:
     m = max(sum(rgb)/3 for rgb in arr)
    template = get_template(arr, r, m, inverse)
    frames = []
    if type != "point":
        im.paste(img, (0,0))
    im1 = copy.copy(im)
    for step in range(10):
        j = random.randint(-jiggle, jiggle)
        im1 = copy.copy(im)
        draw = ImageDraw.Draw(im1)
        i = 65535
        for color in reversed(arr):
            if color == (0,0,0):
                i-=1
                continue
            y, x = divmod(i, size[0])
            c = template[(x,y)][step]
            if step == 0:
                coords = c
            else:
                coords = (c[0]+j, c[1])
            if type == "point":
                draw.point([coords], fill=color)
            else:
                if not from_start and step != 0:
                    z = template[(x,y)][step-1]
                    l = (z[0]+last, z[1])
                else:
                    l = (x, y)
                draw.line((l ,coords), fill=color)
                last = j
            i-=1
        if color != 1.0:
            enhance = ImageEnhance.Color(im1)
            im1 = enhance.enhance(color)
        if blur != 1.0:
            en = ImageEnhance.Sharpness(im1)
            im1 = en.enhance(blur)
        frames.append(im1)
    frames += list(reversed(frames))
    return frames
    
def do_depth(img, r=0, type="line", jiggle=0, inverse=False, blur=1.0, color=1.0, from_start=True):
    img = img.resize((256, 256), Image.NEAREST)
    if img.mode != "RGB":
        img = img.convert("RGB")
    im = Image.new("RGB", (256,256), "black")
    draw = ImageDraw.Draw(im)
    draw.ellipse([(0,0),(256,256)], fill="white", outline="white")
    img = ImageChops.multiply(img, im)
    frames = process_depth(img, r, type, jiggle, inverse, blur, color, from_start)
    buff = BytesIO()
    frames[0].save(
        buff, "gif", save_all=True, append_images=frames[1:], duration=100, loop=0
    )
    buff.seek(0)
    return buff

def link(arr, arr2):
    rgb1 = arr.reshape((arr.shape[0] * arr.shape[1], 3))
    rgb2 = tuple(map(tuple, arr2.reshape((arr2.shape[0] * arr2.shape[1], 3))))
    template1 = {x: [0, []] for x in rgb2}
    for x, y in zip(rgb2, rgb1):
        template1[x][1].append(y)
    return template1

def reset_template(template):
    for v in template.values():
        v[0] = 0
    
def process_sorting(img, img2):
    arr = np.array(img)
    arr2 = np.array(img2)

    shape = arr.shape
    npixs = shape[0] * shape[1]
    valid = []
    for i in range(1, npixs + 1):
        num = npixs / i
        if num.is_integer():
            valid.append((int(num), i))

    frames = []
    way_back = []
    for v in valid:
        arr = arr.reshape((v[0], v[1], shape[2]))
        arr.view("uint8,uint8,uint8").sort(order=["f2"], axis=1)
        arr2 = arr2.reshape((v[0], v[1], shape[2]))
        arr2.view("uint8,uint8,uint8").sort(order=["f2"], axis=1)
        new = Image.fromarray(arr.reshape(shape))
        frames.append(new)
        ar2 = copy.copy(arr2)
        way_back.append(ar2)

    template = link(arr, arr2)

    for way in reversed(way_back):
        for i, z in enumerate(way[:,:,]):
            for x, rgb in enumerate(z):
                l = template[tuple(rgb)]
                way[:, :,][i,x] = l[1][l[0]]
                l[0] += 1
        new = Image.fromarray(way.reshape(shape))
        frames.append(new)
        reset_template(template)
        
    for i in range(5):
        frames.insert(0, frames[0])
        frames.append(frames[-1])
    frames += list(reversed(frames))
    return frames

def process_transform(img1, img2):
    img1 = img1.resize((256, 256), Image.NEAREST)
    if img1.mode != "RGB":
        img1 = img1.convert("RGB")
    img2 = img2.resize((256, 256), Image.NEAREST)
    if img2.mode != "RGB":
        img2 = img2.convert("RGB")
    frames = process_sorting(img1, img2)
    buff = BytesIO()
    frames[0].save(
            buff,
            "gif",
            save_all=True,
            append_images=frames[1:] + frames[-1:] * 5,
            duration=125,
            loop=0
        )
    buff.seek(0)
    return buff

def main():
    sent = pickle.loads(sys.stdin.buffer.read())
    data = do_depth(*sent)
    stdout_write = sys.stdout.buffer.write
    buff = data.getbuffer()
    stdout_write(buff)
    sys.exit(0)
    
class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def depth(self, ctx, user:discord.Member=None, rotate:int=0, jiggle:int=0, method="line", blur:float=1.0, color:float=1.0, inverse:str=False, from_start:str=True):
        '''Make a depth gif of someone's avatar'''
        if user is None:
            user = ctx.author
        inverse = inverse == "True"
        from_start = from_start == "True"
        img = Image.open(BytesIO(await user.avatar_url_as(format="png",size=256).read()))
        async with ctx.typing():
            t = time.perf_counter()
            to_send = pickle.dumps((img, rotate, method, jiggle, inverse, blur, color, from_start))
               
            proc = await asyncio.create_subprocess_exec(
                sys.executable, '-m', __name__,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            try:
                data, err = await asyncio.wait_for(proc.communicate(to_send), timeout=30)
            except:
                proc.kill()
                return await ctx.send("Process Errored, try again")
            buff = BytesIO(data)
            t1 = round(time.perf_counter()-t,3)
            await ctx.send(f"Made in {t1}s", file = discord.File(buff,"depth.gif"))

    @commands.command()
    async def transform(self, ctx, user: discord. Member,
    other: discord. Member=None):
        if other is None:
            other = ctx.author
        im1 = Image.open(BytesIO (await
        user.avatar_url_as(format="jpeg", size=256).read()))
        im2 = Image.open(BytesIO (await other.avatar_url_as(format="jpeg", size=256).read()))
        async with ctx.typing():
            t = time.time()
            if other.id == ctx.author.id:
                buff = await self.bot.loop.run_in_executor(None, process_transform, im2, im1)
            else:
                buff = await self.bot.loop.run_in_executor(None, process_transform, im1, im2)
            t = round(time.time() - t, 3)
            await ctx.send(f"Made in {t} seconds", file=discord.File(buff, "transform.gif"))

def setup(bot):
    bot.add_cog(Images(bot))

if __name__ == "__main__":
    main()
