#!./.env/bin/python
# codng: utf-8

'''Video Trimmer

Cut down videos with transcoding.


'''

import shutil
import os
import sys
import re
import datetime
import time
#from urllib.request import urlopen
#from urllib.error import URLError
import subprocess
import argparse
import json
import logging
#import youtube_dl
from tqdm import tqdm

#monofix = False

FORMAT = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log_file_only = logging.getLogger()
log.setLevel(logging.DEBUG)
log_file_only.setLevel(logging.DEBUG)
path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'choppy.log')
fh = logging.FileHandler(path)
fh.setFormatter(FORMAT)
ch = logging.StreamHandler()
log.addHandler(fh)
log.addHandler(ch)
log_file_only.addHandler(fh)

'''
# Create options.txt if it doesn't exist
if not os.path.exists('options.txt'):
    open('options.txt', 'w').close()

parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument('-res', type=int, default=720)
parser.add_argument('-fast', '--skip-encoding', action='store_true', default=False)
parser.add_argument('-encoding', type=str, default='prores -profile:v 2')
parser.add_argument('-framerate', type=float, default=29.97)
args = parser.parse_args(['@options.txt'] + sys.argv[1:])
if args.res == 720:
    WIDTH, HEIGHT = (1280, 720)
elif args.res == 1080:
    WIDTH, HEIGHT = (1920, 1080)
elif args.res == 2160:
    WIDTH, HEIGHT = (3840, 2160)
else:
    log.warning('Unsupported resolution for -res argument.  Supported resolutions are: 720, 1080, 2160')
    os._exit(os.EX_OK)
'''

# Set paths
DOWNLOAD_LOCATION = os.path.expanduser('~/Desktop/ChoppyChop/')
DOWNLOADING = os.path.join(DOWNLOAD_LOCATION, '.downloading/')
ENCODING = os.path.join(DOWNLOAD_LOCATION, '.encoding/')
'''
YOUTUBE_CAPTION_FORMATS = set(['.srt', '.sbv', '.sub', '.mpsub', '.lrc', '.cap', '.smi',
                                '.sami', '.rt', '.vtt', '.ttml', '.dfxp', '.scc', '.stl',
                                '.tds', '.cin', '.asc'])
YOUTUBE_VIDEO_FORMATS = set(['.flv', '.3gp', '.mp4', '.webm', '.mkv', '.ogv', '.wmv', '.mpg'])
YDL_COMMON_OPTS = {'restrictfilenames': True,
                   'outtmpl': "{path}%(title)s.%(ext)s".format(path=DOWNLOADING),
                   'logger': log,
                   'subtitleslangs': ['en']}
YDL_OPTS_SPECIFIC_RES = {'format': 'bestvideo[width={width}][height={height}]+bestaudio'.format(width=WIDTH, height=HEIGHT)}
YDL_OPTS_BEST_RES = {'format': 'bestvideo+bestaudio/best'}
FFMPEG_MP4_CONTAINER = ['ffmpeg', '-i',
                        '{inpath}', '-ss', '{startpoint}',
                        '-to', '{runtime}',
                        '-c:v', 'copy',
                        '-c:a', 'libfdk_aac',
                        '{outpath}']
FFMPEG_PRORES = ['ffmpeg', '-i',
                 '{inpath}', '-ss', '{startpoint}',
                 '-to', '{runtime}',
                 '-c:v', '{encoding}'.format(encoding=args.encoding),
                 '-r', '{framerate}'.format(framerate=args.framerate),
                 '-c:a', 'pcm_s24le',
                 '-ar', '48000',
                 '{outpath}']
FFMPEG_PRORES_CAPS = ['ffmpeg', '-i',
                      '{inpath}', '-ss', '{startpoint}',
                      '-to', '{runtime}',
                      '-vf',
                      'subtitles={subtitles}',
                      '-c:v', '{encoding}'.format(encoding=args.encoding),
                      '-r', '{framerate}'.format(framerate=args.framerate),
                      '-c:a', 'pcm_s24le',
                      '-ar', '48000',
                      '{outpath}']
FFMPEG_PRORES_LETTERBOX = ['ffmpeg', '-i',
                           '{inpath}', '-ss', '{startpoint}',
                           '-to', '{runtime}',
                           '-vf',
                           ("'scale=(sar*iw)*min({width}/(sar*iw)\,{height}/ih)"
                           ':ih*min({width}/(sar*iw)\,{height}/ih), '
                           'pad={width}:{height}:({width}-(sar*iw)*min'
                           '({width}/(sar*iw)\,{height}/ih))/2:({height}-'
                           'ih*min({width}/(sar*iw)\,'
                           "{height}/ih))/2'"),
                           '-c:v', args.encoding,
                           '-r', str(args.framerate),
                           '-c:a pcm_s24le',
                           '-ar 48000',
                           '{outpath}']
FFMPEG_PRORES_LETTERBOX_CAPS = ['ffmpeg', '-i',
                                '{inpath}', '-ss', '{startpoint}',
                                '-to', '{runtime}',
                                '-vf',
                                ("'scale=(sar*iw)*min({width}/(sar*iw)\,{height}/ih)"
                                ':ih*min({width}/(sar*iw)\,{height}/ih), '
                                'pad={width}:{height}:({width}-(sar*iw)*min'
                                '({width}/(sar*iw)\,{height}/ih))/2:({height}-'
                                'ih*min({width}/(sar*iw)\,'
                                "{height}/ih))/2',subtitles={subtitles}"),
                                '-c:v', args.encoding,
                                '-r', str(args.framerate),
                                '-c:a pcm_s24le',
                                '-ar 48000',
                                '{outpath}']
FFMPEG_MONOFIX = ['rm Temp_mono.mov;',
                 'ffmpeg', '-i',
                 '{inpath}', 
                 '-c:v copy',
                 '-ac 1',
                 'Temp_Mono.mov',
                 '&&',
                 'ffmpeg', '-i',
                 'Temp_Mono.mov', 
                 '-c:v copy',
                 '-ac 2',
                 '{outpath}',
                 '&& rm Temp_Mono.mov']     
FFMPEG_NORM =   [' && ffmpeg-normalize',
                '{outpath}',
                '-o',
                '{outpath}',
                '-f']
'''

FFMPEG_CHOP = ['ffmpeg', '-i',
                        '{inpath}', '-ss', '{startpoint}',
                        '-to', '{runtime}',
                        '-c copy',
                        '{outpath}']

def clear():
    '''Clear terminal window'''
    p = subprocess.Popen(['clear'])
    p.communicate()


def intro_message():
    log.info('-------------------------------------------------------------------------')
    log.info('Follow instructions to trim local video whilst avoiding transcode when possible:')
    log.info('Files will be exported to: {path}'.format(path=DOWNLOAD_LOCATION))
 #   if args.skip_encoding:
 #       log.info('Not re-encoding video due to "-fast" option')
 #   else:
 #       log.info('Selected encoding format: {encoding} at {framerate} fps'.format(encoding=args.encoding, framerate=args.framerate))
 #   log.info('Selected output resolution: {width}x{height}'.format(width=WIDTH, height=HEIGHT))
    log.info('-------------------------------------------------------------------------\n')


def make_dirs():
    #Create necessary directories
    for folder in [DOWNLOAD_LOCATION, DOWNLOADING, ENCODING]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def get_url():
    "Prompt user for local file path"
    while True:
        url = input('Drag and drop local file: ')
        #if check_url(url):
        #    return url
        #path = re.sub('\\\\', '', url).strip()
        if check_path(path):
            return path
        log.warning('Something went wrong, please ensure you entered a valid file path.')

'''

def check_url(url):
    #Check if URL is valid
    try:
        urlopen(url)
        return True
    except (URLError, ValueError):
        return False
'''

def check_path(path):
    return os.path.exists(path)

'''
def strip_features(url):
    #Remove YouTube features from url.
    url = url.split('&list=')[0]
    url = url.split('&feature=')[0]
    url = url.split('?feature=')[0]
    url = url.split('&t=')[0]
    url = url.split('#t=')[0]
    url = url.split('&hl=')[0]
    url = url.split('&gclid=')[0]
    url = url.split('&kw=')[0]
    url = url.split('&ad=')[0]
    url = url.split('&playnext=')[0]
    url = url.split('&playnext_from=')[0]
    url = url.split('&index=')[0]
    url = url.split('&shuffle=')[0]
    url = url.split('&force_ap=')[0]
    url = url.split('&player_embedded=')[0]
    return url

def get_captions():
    #Ask user if they would like to burn captions into video after download.
    user_input = input('Burn captions into video? (yes/no): ') or 'n'
    if not user_input[0].lower() == 'y':
        return False
    return True


def get_auto_captions():
    #If user wants captions, ask if they want them auto-generated by YouTube.

    #This is not available for all videos.
    
    user_input = input('Auto-generated captions? (yes/no): ') or 'n'
    if not user_input[0].lower() == 'y':
        return False
    return True


def download_video(url, captions, auto_captions):
    #Try to download YouTube video in specific resolution.

    #Fall back to bestvideo+bestaudio/best if not available in target resolution.
    
    ydl_opts = YDL_COMMON_OPTS.copy()
    ydl_opts.update(YDL_OPTS_SPECIFIC_RES)

    if args.skip_encoding:
        pass
    elif auto_captions:
        ydl_opts.update({'writeautomaticsub': True})
    elif captions:
        ydl_opts.update({'writesubtitles': True})


    while True:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                break
            except youtube_dl.utils.DownloadError as e:
                if 'format not available' in str(e):
                    log.warning('Resolution {res} not available, downloading best possible resolution.'.format(res=args.res))
                    ydl_opts.update(YDL_OPTS_BEST_RES)
'''

def get_files(local=False):
    #Return dict of filepaths to use for encoding/burning/moving.
    vid = caps = None
    files = os.listdir(DOWNLOADING)
    for f in files:
        if f.startswith('.'):
            continue
        ext = os.path.splitext(f)[1]
        if local:
            vid = f'''
        else:
            if ext in YOUTUBE_CAPTION_FORMATS:
                caps = f
            elif ext in YOUTUBE_VIDEO_FORMATS:
                vid = f'''
    return {'video': os.path.join(DOWNLOADING, vid) if vid else None,
            'captions': os.path.join(DOWNLOADING, caps) if caps else None}


def get_metadata(video_path):
    '''Get video metadata using ffprobe'''
    proc = ['ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path]
    log_file_only.info('subprocess call: {}'.format(proc))
    p = subprocess.Popen(proc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = p.communicate()
    metadata = json.loads(result[0])
    return metadata


def get_resolution(metadata):
    streams = metadata.get('streams')
    if not streams:
        return
    for stream in streams:
        if not stream.get('codec_type') == 'video':
            continue
        if stream.get('width') and stream.get('height'):
            width = int(stream['width'])
            height = int(stream['height'])
            return (width, height)


def get_duration(metadata):
    if metadata.get('format') and metadata['format'].get('duration'):
        duration = metadata['format']['duration']
        return float(duration)

'''
def is_target_resolution(resolution):
    #Check if resolution is the same as (WIDTH, HEIGHT)
    if (resolution[0], resolution[1]) != (WIDTH, HEIGHT):
        return False
    return True


def get_container():
    if 'prores' in args.encoding:
        return '.mov'
    elif any(enc in args.encoding for enc in ['vp8', 'vp9']):
        return '.webm'
    else:
        return '.mp4'
'''
def get_trim():
    # Get trim points for video
#    user_input = input('Would you like to trim the video? (yes/no): ') or 'n'
#    if not user_input[0].lower() == 'y':
#        return False, False
    starttime = get_time('in')
    runtime = get_time('out')
    return starttime, runtime

def get_time(mode):
    while True:
        bs = input('What %s point do you want? (hh:mm:ss, leave blank for default): ' % mode)
        return bs
'''
def get_mono():
    #Fix audio that is only showing in one channel on video that has already been downloaded
    user_input = input('Did the video have audio in only one channel? (yes/no)') or 'n'
    if not user_input[0].lower() == 'y':
        return False
    return True

def get_norm():
    #Normalize audio levels
    user_input = input('Would you like to normalize the audio level? (yes/no)') or 'n'
    if not user_input[0].lower() == 'y':
        return False
    return True
'''
def encode(files, duration, inpoint, outpoint):
    '''Encode video with captions burned in (if present).'''
    video = files['video']
    captions = files['captions']
    ext = '.mp4'
    if not inpoint:
        inpoint = '00:00:00'
    if not outpoint:
        outpoint = time.strftime('%H:%M:%S', time.gmtime(duration + 1))
    new_filename = os.path.splitext(os.path.basename(video))[0] + ext
    outpath = os.path.join(ENCODING, new_filename)
    proc = ' '.join(FFMPEG_CHOP).format(inpath=video, startpoint=inpoint, outpath=outpath, runtime=outpoint)

    log_file_only.info('subprocess call: {}'.format(proc))
    p = subprocess.Popen(proc, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    seconds_encoded = float()
    with tqdm(total=duration, desc='Encoding') as pbar:
        for line in iter(p.stdout.readline, ''):
            log_file_only.info(line.rstrip())

            re1='.*?'	# Non-greedy match on filler
            re2='(time)'	# Word 1
            re3='(=)'	# Any Single Character 1
            re4='(\\d+)'	# Integer Number 1
            re5='(:)'	# Any Single Character 2
            re6='(\\d+)'	# Integer Number 2
            re7='(:)'	# Any Single Character 3
            re8='(\\d+)'	# Integer Number 3
            re9='(\\.)'	# Any Single Character 4
            re10='(\\d+)'	# Integer Number 4

            rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10,re.IGNORECASE|re.DOTALL)
            m = rg.search(line)
            if m:
                int1=m.group(3)
                c2=m.group(4)
                int2=m.group(5)
                c3=m.group(6)
                int3=m.group(7)
                c4=m.group(8)
                int4=m.group(9)

                time_progress = int1+c2+int2+c3+int3+c4+int4
                t = datetime.datetime.strptime(time_progress, '%H:%M:%S.%f')
                total_seconds = (t - datetime.datetime(1900, 1, 1)).total_seconds()
                pbar.update(total_seconds - seconds_encoded)
                seconds_encoded = total_seconds
    p.communicate()

'''
def mp4_container(video_path):
    #Re-wrap video file in mp4 container.

    #Will re-encode audio to AAC using libfdk_aac to conform to mp4.
    
    vid_name, ext = os.path.splitext(os.path.basename(video_path))
    if ext == '.mp4':
        log.info('Already mp4, no need to re-encode audio for mp4 (-fast)')
        return
    new_filename = vid_name + '.mp4'
    outpath = os.path.join(DOWNLOADING, new_filename)
    proc = ' '.join(FFMPEG_MP4_CONTAINER).format(inpath=video_path, outpath=outpath)
    log_file_only.info('subprocess call: {}'.format(proc))
    p = subprocess.Popen(proc, shell=True)
    p.communicate()
    os.remove(video_path)
'''

def move_files():
    '''Move all files from ENCODING folder to DOWNLOAD_LOCATION.

    Will overwrite existing file of same name.
    '''
#    if args.skip_encoding:
#        src = DOWNLOADING
#    else:
#        src = ENCODING
    src = 'MAKE THIS WORK'
    for f in os.listdir(src):
        shutil.move(os.path.join(src, f), os.path.join(DOWNLOAD_LOCATION, f))


def cleanup():
    # Remove downloads/encodes so we can start another.
    global monofix
    monofix = False
    try:
        shutil.rmtree(DOWNLOADING)
        shutil.rmtree(ENCODING)
    except OSError:
        pass


def local_process(path):
    video = os.path.basename(path)
    new_name = re.sub(' ', '_', video)
    shutil.copy2(path, os.path.join(DOWNLOADING, new_name))
    global starttime
    global runtime
#    global monofix
#    global norm
#    monofix = get_mono()
#    if not monofix:
    starttime, runtime = get_trim()
#    else:
#        starttime = False
#        runtime = False
#    norm = get_norm()
    files = get_files(local=True)
    return files

'''
def youtube_process(url):
    url = strip_features(url)
    captions = auto_captions = False
    if not args.skip_encoding:
        captions = get_captions()
        auto_captions = get_auto_captions() if captions else False
        global starttime
        global runtime
        global norm
        starttime, runtime = get_trim()
        norm = get_norm()
    download_video(url, captions, auto_captions)
    files = get_files()
    return files
'''

def main():
    while True:
        cleanup()
        make_dirs()
        clear()
        intro_message()

        url = get_url()
        if check_path(url):
            files = local_process(url)


        video_file = files.get('video')
        if not video_file:
            log.debug('Something went wrong, video not found.')
            break # re-visit this

#        if args.skip_encoding:
#            mp4_container(video_file)
#            move_files()
#            continue

        metadata = get_metadata(video_file)
        resolution = get_resolution(metadata)
#        is_target_res = is_target_resolution(resolution)
        duration = get_duration(metadata)
        encode(files, duration, starttime, runtime)
        move_files()


if __name__ == '__main__':
    main()
