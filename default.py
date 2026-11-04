import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else -1
BASE = f'plugin://{ADDON_ID}/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def get_profile_path():
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    if not os.path.exists(profile):
        os.makedirs(profile, exist_ok=True)
    return profile

def get_channels_file():
    return os.path.join(get_profile_path(), 'channels.json')

def load_channels():
    ch_file = get_channels_file()
    if os.path.exists(ch_file):
        try:
            with open(ch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            xbmc.log(f'[{ADDON_ID}] Error loading channels: {e}', xbmc.LOGWARNING)
    return []

def save_channels(channels):
    ch_file = get_channels_file()
    try:
        with open(ch_file, 'w', encoding='utf-8') as f:
            json.dump(channels, f, indent=2)
    except Exception as e:
        xbmc.log(f'[{ADDON_ID}] Error saving channels: {e}', xbmc.LOGERROR)

def fetch_http_text(url, tries=3):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=14) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as error:
            last = error
            time.sleep(0.5)
    raise last

def fetch_http_bytes(url, tries=2):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read()
        except Exception as error:
            last = error
            time.sleep(0.5)
    raise last

def normalize_slug(raw_input):
    slug = raw_input.strip()
    if 'rumble.com/' in slug:
        slug = slug.split('rumble.com/')[-1].strip('/')
    if slug.startswith('c/'):
        slug = slug[2:]
    elif slug.startswith('user/'):
        slug = slug[5:]
    return slug.strip('/')

def fetch_rumble_channel(slug, default_name=None):
    clean_slug = normalize_slug(slug)
    urls = [
        f'https://rumble.com/c/{clean_slug}',
        f'https://rumble.com/user/{clean_slug}'
    ]

    text = None
    for u in urls:
        try:
            text = fetch_http_text(u)
            if text and '<script type=' in text:
                break
        except Exception:
            continue

    if not text:
        xbmc.log(f'[{ADDON_ID}] Could not retrieve page for Rumble slug {slug}', xbmc.LOGWARNING)
        return None

    scripts = re.findall(r'<script type=["\']application/json["\']>(.*?)</script>', text, re.DOTALL)
    channel_info = None
    live_item = None
    recent_videos = []

    for s in scripts:
        try:
            d = json.loads(s.strip())
            if isinstance(d, dict) and 'items' in d:
                for it in d['items']:
                    if not channel_info and it.get('by'):
                        channel_info = it['by']
                    if it.get('live') and it.get('videos') and not live_item:
                        live_item = it
                    elif it.get('videos') and it.get('title'):
                        recent_videos.append(it)
        except Exception:
            pass

    display_name = (channel_info.get('title') or channel_info.get('name')) if channel_info else (default_name or clean_slug)
    pfp_url = channel_info.get('thumb') if channel_info else None

    # Parse live stream video URL if available
    playback_url = None
    stream_title = ''
    stream_thumb = None
    stream_id = None
    watching_now = 0

    if live_item:
        stream_title = live_item.get('title', '')
        stream_id = live_item.get('id') or live_item.get('eid')
        stream_thumb = live_item.get('thumb')
        watching_now = live_item.get('watching_now', 0)
        
        for v in live_item.get('videos', []):
            if v.get('type') == 'hls' and v.get('url'):
                playback_url = v['url']
                break
        if not playback_url:
            for v in live_item.get('videos', []):
                if v.get('url'):
                    playback_url = v['url']
                    break

    # Parse clean recent videos
    parsed_recents = []
    for vid in recent_videos[:15]:
        v_url = None
        for v in vid.get('videos', []):
            if v.get('type') == 'hls' and v.get('url'):
                v_url = v['url']
                break
        if not v_url and vid.get('videos'):
            v_url = vid['videos'][0].get('url')
        if v_url:
            parsed_recents.append({
                'title': vid.get('title', 'Video'),
                'duration': vid.get('duration', 0),
                'thumb': vid.get('thumb'),
                'upload_date': vid.get('upload_date', ''),
                'video_url': v_url
            })

    return {
        'slug': clean_slug,
        'name': display_name,
        'is_live': bool(live_item and playback_url),
        'title': stream_title,
        'stream_id': stream_id,
        'watching_now': watching_now,
        'playback_url': playback_url,
        'stream_thumb': stream_thumb,
        'profile_pic': pfp_url,
        'recent_videos': parsed_recents
    }

def get_cached_image(url, filename):
    if not url:
        return None
    dest_path = xbmcvfs.translatePath(f'special://temp/{filename}')
    try:
        data_bytes = fetch_http_bytes(url, tries=2)
        if HAS_PIL and (url.endswith('.webp') or 'thumb' in filename or 'profile' in filename):
            try:
                im = Image.open(io.BytesIO(data_bytes))
                im.convert('RGB').save(dest_path, 'JPEG', quality=90)
                return dest_path
            except Exception:
                pass
        with open(dest_path, 'wb') as out:
            out.write(data_bytes)
        return dest_path
    except Exception as e:
        xbmc.log(f'[{ADDON_ID}] Image cache error {filename}: {e}', xbmc.LOGWARNING)
        return dest_path if os.path.exists(dest_path) else None

def play(slug, name, video_url=None):
    if not video_url:
        info = fetch_rumble_channel(slug, name)
        if not info or not info.get('is_live') or not info.get('playback_url'):
            xbmcgui.Dialog().notification('Rumble Live', f'{name} is offline right now.', xbmcgui.NOTIFICATION_INFO)
            if HANDLE >= 0:
                xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            return
        video_url = info['playback_url']
        stream_title = info.get('title') or 'Live Stream'
    else:
        stream_title = name

    item = xbmcgui.ListItem(label=f"{name} — {stream_title}", path=video_url)
    tag = item.getVideoInfoTag()
    tag.setTitle(f"{name} — {stream_title}")
    tag.setMediaType('video')
    item.setContentLookup(False)
    item.setProperty('IsPlayable', 'true')

    if '.m3u8' in video_url:
        item.setMimeType('application/vnd.apple.mpegurl')
        use_ia = ADDON.getSetting('use_inputstream').lower() != 'false'
        if use_ia:
            item.setProperty('inputstream', 'inputstream.adaptive')
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    else:
        item.setMimeType('video/mp4')

    if HANDLE >= 0:
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

def channel_videos(slug, name):
    xbmcplugin.setPluginCategory(HANDLE, f'{name} — Recent Videos')
    xbmcplugin.setContent(HANDLE, 'videos')

    info = fetch_rumble_channel(slug, name)
    recents = info.get('recent_videos', []) if info else []

    if not recents:
        item = xbmcgui.ListItem(label='No recent videos available.')
        xbmcplugin.addDirectoryItem(HANDLE, BASE, item, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return

    for vid in recents:
        v_title = vid['title']
        v_url = vid['video_url']
        v_thumb = vid['thumb']
        
        item = xbmcgui.ListItem(label=v_title)
        tag = item.getVideoInfoTag()
        tag.setTitle(v_title)
        tag.setMediaType('video')
        if vid.get('duration'):
            tag.setDuration(int(vid['duration']))

        if v_thumb:
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', v_title)[:20]
            cached = get_cached_image(v_thumb, f'rumble_vid_{safe_name}.jpg')
            if cached:
                item.setArt({'thumb': cached, 'icon': cached, 'poster': cached, 'fanart': cached})

        item.setProperty('IsPlayable', 'true')
        play_url = f'{BASE}?action=play_url&slug={urllib.parse.quote(slug)}&name={urllib.parse.quote(v_title)}&url={urllib.parse.quote(v_url)}'
        xbmcplugin.addDirectoryItem(HANDLE, play_url, item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)

def add_channel():
    dialog = xbmcgui.Dialog()
    raw_input = dialog.input('Enter Rumble Channel Slug or URL', type=xbmcgui.INPUT_ALPHANUM)
    if not raw_input:
        return

    slug = normalize_slug(raw_input)
    if not slug:
        return

    channels = load_channels()
    if any(normalize_slug(c.get('slug', '')).lower() == slug.lower() for c in channels):
        dialog.notification('Rumble Live', f"'{slug}' is already in your channels.")
        return

    dialog.notification('Rumble Live', f'Verifying {slug} on Rumble...')
    info = fetch_rumble_channel(slug)
    if not info:
        dialog.notification('Rumble Live', f"Could not find channel '{slug}'.", xbmcgui.NOTIFICATION_ERROR)
        return

    channels.append({'slug': info['slug'], 'name': info['name']})
    save_channels(channels)
    dialog.notification('Rumble Live', f"Added {info['name']} to channels!", xbmcgui.NOTIFICATION_INFO)
    xbmc.executebuiltin('Container.Refresh')

def remove_channel(slug, name):
    dialog = xbmcgui.Dialog()
    if not dialog.yesno('Remove Channel', f'Remove {name} from your Rumble channels?'):
        return
    channels = load_channels()
    channels = [c for c in channels if normalize_slug(c.get('slug', '')).lower() != slug.lower()]
    save_channels(channels)
    dialog.notification('Rumble Live', f'Removed {name}', xbmcgui.NOTIFICATION_INFO)
    xbmc.executebuiltin('Container.Refresh')

def listing():
    xbmcplugin.setPluginCategory(HANDLE, 'Rumble Live & Channels')
    xbmcplugin.setContent(HANDLE, 'videos')

    # Add Channel item
    add_item = xbmcgui.ListItem(label='[B][COLOR lightgreen]+ Add Channel / Creator[/COLOR][/B]')
    add_url = f'{BASE}?action=add_channel'
    xbmcplugin.addDirectoryItem(HANDLE, add_url, add_item, isFolder=False)

    channels = load_channels()
    if not channels:
        empty_item = xbmcgui.ListItem(label='No channels added yet. Click "[+ Add Channel]" to add creators!')
        empty_item.setArt({'icon': 'DefaultAddonNone.png'})
        xbmcplugin.addDirectoryItem(HANDLE, add_url, empty_item, isFolder=False)

    for c in channels:
        slug = c.get('slug')
        default_name = c.get('name', slug)
        info = fetch_rumble_channel(slug, default_name)

        is_live = info.get('is_live', False) if info else False
        display_name = (info.get('name') if info else None) or default_name

        if is_live:
            viewers_str = f" ({info.get('watching_now', 0):,} viewers)" if info.get('watching_now') else ""
            label = f'[COLOR lime]● LIVE[/COLOR] {display_name}{viewers_str}'
            plot = f"{info.get('title', '')}\nClick to watch live stream."
        else:
            label = f'[COLOR gray]○ OFFLINE[/COLOR] {display_name}'
            plot = f'{display_name} is currently offline. Click to browse recent videos.'

        item = xbmcgui.ListItem(label=label)
        tag = item.getVideoInfoTag()
        tag.setTitle(label)
        tag.setMediaType('video')
        tag.setPlot(plot)

        thumb_url = (info.get('stream_thumb') or info.get('profile_pic')) if info else None
        if thumb_url:
            cached = get_cached_image(thumb_url, f'rumble_thumb_{slug}.jpg')
            if cached:
                item.setArt({'thumb': cached, 'icon': cached, 'poster': cached, 'fanart': cached})

        if is_live:
            item.setProperty('IsPlayable', 'true')
            target_url = f'{BASE}?action=play&slug={urllib.parse.quote(slug)}&name={urllib.parse.quote(display_name)}'
            is_folder = False
        else:
            target_url = f'{BASE}?action=recent_videos&slug={urllib.parse.quote(slug)}&name={urllib.parse.quote(display_name)}'
            is_folder = True

        remove_url = f'{BASE}?action=remove_channel&slug={urllib.parse.quote(slug)}&name={urllib.parse.quote(display_name)}'
        recent_url = f'{BASE}?action=recent_videos&slug={urllib.parse.quote(slug)}&name={urllib.parse.quote(display_name)}'
        context_menu = [
            ('Browse Recent Videos', f'ActivateWindow(10025,"{recent_url}",return)'),
            ('Remove Channel', f'RunPlugin({remove_url})'),
            ('Refresh Live Status', 'Container.Refresh'),
            ('Rumble Settings', f'Addon.OpenSettings({ADDON_ID})')
        ]
        item.addContextMenuItems(context_menu)

        xbmcplugin.addDirectoryItem(HANDLE, target_url, item, isFolder=is_folder)

    refresh = xbmcgui.ListItem(label='Refresh All')
    xbmcplugin.addDirectoryItem(HANDLE, BASE, refresh, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)

def main():
    params = dict(urllib.parse.parse_qsl(sys.argv[2].lstrip('?'))) if len(sys.argv) > 2 else {}
    action = params.get('action')
    try:
        if action == 'play':
            play(params.get('slug', ''), params.get('name', ''))
        elif action == 'play_url':
            play(params.get('slug', ''), params.get('name', ''), params.get('url'))
        elif action == 'recent_videos':
            channel_videos(params.get('slug', ''), params.get('name', ''))
        elif action == 'add_channel':
            add_channel()
        elif action == 'remove_channel':
            remove_channel(params.get('slug', ''), params.get('name', ''))
        else:
            listing()
    except Exception as error:
        xbmc.log(f'[{ADDON_ID}] Error: {error}', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Rumble Live', 'Error processing request.', xbmcgui.NOTIFICATION_ERROR)
        if action in ('play', 'play_url') and HANDLE >= 0:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        elif HANDLE >= 0:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)

if __name__ == '__main__':
    main()
