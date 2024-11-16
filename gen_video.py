import os
import random
import ffmpeg
import subprocess
import time
import glob
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

# 通过 https://spotifydown.com/ 下载音乐放在music目录下
# pinterest下载图片，放在images目录下
audio_path = glob.glob(os.path.join('music', "*.mp3"))[0]
# TODO: 提取不到cover时需要手动填充cover_path和作者名
cover_path = 'music/logo.jpg'
find_cover_author = True
song_author = ''
# 提取封面、歌曲名
audio = MP3(audio_path, ID3=EasyID3)
song_name = os.path.basename(audio_path).split(' - ', 1)[-1].rsplit('.', 1)[0]
if find_cover_author:
    song_logo = None
    author = None
    tags = ID3(audio_path)
    for tag in tags.values():
        if tag.FrameID == 'TPE1':
            author = tag.text
            break
    for tag in tags.values():
        if isinstance(tag, APIC):
            song_logo = tag.data
            with open(cover_path, 'wb') as img_file:
                img_file.write(song_logo)
            break
    if song_logo and author:
        song_author = "&".join(author)
    else:
        print("请手动输入歌曲封面、作者")
        exit(1)

background_video_path = 'background_videos'
font_file = 'laihuti.ttf'
image_folder = 'images/'
output_image_folder = 'processed_images/'
back_img_path = 'static/back.png'

os.makedirs(output_image_folder, exist_ok=True)

# 获取

# 处理图片
images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg'))]
scaled_images = []
for idx, img in enumerate(images):
    img_info = ffmpeg.probe(img, v='error', select_streams='v', show_entries='stream=width,height')
    img_width = int(img_info['streams'][0]['width'])
    img_height = int(img_info['streams'][0]['height'])

    if img_width < img_height * 1.3:
        scaled_images.append(ffmpeg.input(img).filter('scale', 1300, -1).filter('crop', 1300, 1000, (img_height - 1000) // 2))
    else:
        scaled_images.append(ffmpeg.input(img).filter('scale', -1, 1000).filter('crop', 1300, 1000, (img_width - 1300) // 2, 0))

processed_image_paths = []
for idx, scaled_img in enumerate(scaled_images):
    output_image_path = os.path.join(output_image_folder, f"processed_image_{idx+1}.png")
    processed_image_paths.append(output_image_path)
    ffmpeg.output(scaled_img, output_image_path).run(overwrite_output=True)

# 获取音频时长
audio_info = ffmpeg.probe(audio_path, v='error', select_streams='a', show_entries='stream=duration')
audio_duration = float(audio_info['streams'][0]['duration'])
print(f"音频时长: {audio_duration}秒")

# 获取mp4文件
random.seed(int(time.time() * 1000))
mp4_files = [file for file in os.listdir(background_video_path) if file.endswith('.mp4')]
random_video = random.choice(mp4_files)
video_path = os.path.join(background_video_path, random_video)
print(f"随机选择的视频文件: {random_video}")

# 获取视频时长
video_info = ffmpeg.probe(video_path, v='error', select_streams='v', show_entries='stream=duration')
video_duration = float(video_info['streams'][0]['duration'])
print(f"视频时长: {video_duration}秒")

# 合成视频
loop_count = int(audio_duration // video_duration)
remaining_duration = audio_duration % video_duration
ffmpeg.input(video_path, stream_loop=loop_count).output('tmp2.mp4', vcodec='copy', acodec='copy', an=None).run(overwrite_output=True)
ffmpeg.input('tmp2.mp4', ss='00:00:00', t=audio_duration).output('tmp1.mp4', vcodec='copy', acodec='copy').run(overwrite_output=True)
command = [
    'ffmpeg', 
    '-i', 'tmp1.mp4', 
    '-i', audio_path, 
    '-c:v', 'copy', 
    '-c:a', 'copy', 
    '-strict', 'experimental', 
    'tmp2.mp4',
    '-y'
]
subprocess.run(command, check=True)

# 增加标题、字幕和图片
current_date = time.strftime('%Y-%m-%d', time.localtime())
video_info = ffmpeg.probe(video_path, v='error', select_streams='v:0', show_entries='stream=width,height')
video_width = int(video_info['streams'][0]['width'])
video_height = int(video_info['streams'][0]['height'])
title_font_file = 'Arial.ttf'
title_text = f"日推 {current_date}"
ffmpeg.input('tmp2.mp4').output('tmp1.mp4',
                                  filter_complex=(
                                      # 标题、作者
                                      f"drawtext=text='{title_text}':fontfile={font_file}:fontcolor='#f8f8f8':fontsize={video_height * 0.04}:x={video_width * 0.04}:y={video_height * 0.04},"
                                      f"drawtext=text='{song_name}':fontfile={font_file}:fontcolor='#ffffff':fontsize={video_height * 0.1}:x={video_width * 0.04}:y={video_height * 0.75},"
                                      f"drawtext=text='{song_author}':fontfile={font_file}:fontcolor='#ffffff':fontsize={video_height * 0.04}:x={video_width * 0.05}:y={video_height * 0.88},"
                                  ),
                                  vcodec='libx264', acodec='copy', crf=0).run(overwrite_output=True)
# 调整图片比例

# 增加背景图片
back_width = video_height * 1.93
back_height = video_height * 1.52
command = [
    'ffmpeg',
    '-i', 'tmp1.mp4',
    '-i', back_img_path,
    '-filter_complex', f"[1:v]scale={back_width}:{back_height}[back];"
                       f"[0:v][back]overlay={video_width * 0.44 + video_height * 0.33 * 1.3 - 0.475 * back_width}:{video_height * 0.49 - 0.463 * back_height};",
    '-vcodec', 'libx264',
    '-acodec', 'copy',
    '-crf', '0',
    'tmp2.mp4',
    '-y'
]
subprocess.run(command, check=True)


# 增加logo和图片
command = [
    'ffmpeg',
    '-i', 'tmp2.mp4',
    '-i', cover_path,
]


image_duration = audio_duration / len(processed_image_paths)
overlay_filter = (
        f"[1:v]scale=-1:{video_height * 0.48}[logo];"
        f"[0:v][logo]overlay={video_width * 0.05}:{video_height * 0.2}[link0];"
    )
for i, img in enumerate(processed_image_paths):
    print()
    overlay_filter += (
        f"[{i+2}:v]scale=-1:{video_height * 0.66}[img{i+1}];"
        f"[link{i}][img{i+1}]overlay={video_width * 0.44}:{video_height * 0.16}:enable='between(t,{0 + i * image_duration},{image_duration + i * image_duration})'[link{i+1}];"
    )
    command.append('-i')
    command.append(img)
overlay_filter += f"[link{len(processed_image_paths)}]format=yuv420p"
command += [
    '-filter_complex', overlay_filter,
    '-vcodec', 'libx264',
    '-acodec', 'copy',
    '-crf', '0',
    'tmp1.mp4',
    '-y'
]
subprocess.run(command, check=True)
ffmpeg.input('tmp1.mp4').output("【Spotify Pinterest日推】{song_name} - {song_author}.mp4", vcodec='copy', acodec='copy').run(overwrite_output=True)
