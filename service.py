import io
import json
import os
import re
import sys
import time
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
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

def get_state_file():
    return os.path.join(get_profile_path(), 'service_state.json')

def load_channels():
    ch_file = get_channels_file()
    if os.path.exists(ch_file):
        try:
            with open(ch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def load_state():
    state_file = get_state_file()
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state):
    try:
        with open(get_state_file(), 'w', encoding='utf-8') as f:
            json.dump(state, f)
    except Exception:
        pass

def fetch_http_text(url, tries=2):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
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

def get_rumble_status(slug, default_name):
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
        return None

    scripts = re.findall(r'<script type=["\']application/json["\']>(.*?)</script>', text, re.DOTALL)
    channel_info = None
    live_item = None

    for s in scripts:
        try:
            d = json.loads(s.strip())
            if isinstance(d, dict) and 'items' in d:
                for it in d['items']:
                    if not channel_info and it.get('by'):
                        channel_info = it['by']
                    if it.get('live') and it.get('videos'):
                        live_item = it
                        if not channel_info and it.get('by'):
                            channel_info = it['by']
                        break
        except Exception:
            pass

    display_name = (channel_info.get('title') or channel_info.get('name')) if channel_info else default_name
    pfp_url = channel_info.get('thumb') if channel_info else None

    if live_item:
        return {
            'is_live': True,
            'stream_id': live_item.get('id') or live_item.get('eid'),
            'title': live_item.get('title', ''),
            'name': display_name,
            'pfp_url': pfp_url
        }
    else:
        return {
            'is_live': False,
            'stream_id': None,
            'title': '',
            'name': display_name,
            'pfp_url': pfp_url
        }

def get_avatar_jpg(slug, user_pic):
    if not user_pic:
        return None
    dest_jpg = xbmcvfs.translatePath(f'special://temp/rumble_profile_{slug}.jpg')
    try:
        data_bytes = fetch_http_bytes(user_pic, tries=2)
        if HAS_PIL:
            try:
                im = Image.open(io.BytesIO(data_bytes))
                im.convert('RGB').save(dest_jpg, 'JPEG', quality=95)
                return dest_jpg
            except Exception:
                pass
        with open(dest_jpg, 'wb') as out:
            out.write(data_bytes)
        return dest_jpg
    except Exception as error:
        xbmc.log(f'[{ADDON_ID}] Failed to download avatar for {slug}: {error}', xbmc.LOGWARNING)
        if os.path.exists(dest_jpg):
            return dest_jpg
        return None

def notify_live(name, title, icon_path):
    heading = f'{name} is Live on Rumble!'
    msg = title or 'Now streaming on Rumble'
    if len(msg) > 70:
        msg = msg[:67] + '...'
    icon = icon_path if (icon_path and os.path.exists(icon_path)) else 'info'
    xbmcgui.Dialog().notification(heading, msg, icon, 7000, True)

def get_setting_bool(setting_id, default=True):
    try:
        val = ADDON.getSetting(setting_id)
        if val.lower() in ('true', '1', 'yes'):
            return True
        if val.lower() in ('false', '0', 'no'):
            return False
        return default
    except Exception:
        return default

def get_setting_int(setting_id, default=60):
    try:
        val = ADDON.getSetting(setting_id)
        return int(val) if val else default
    except Exception:
        return default

def run():
    monitor = xbmc.Monitor()
    xbmc.log(f'[{ADDON_ID}] Rumble live monitor service started', xbmc.LOGINFO)

    if monitor.waitForAbort(10):
        return

    state = load_state()
    initial_boot = (len(state) == 0)

    while not monitor.abortRequested():
        enabled = get_setting_bool('enable_notifications', True)
        interval = get_setting_int('check_interval', 60)

        if enabled:
            channels = load_channels()
            for c in channels:
                if monitor.abortRequested():
                    break
                slug = c.get('slug')
                default_name = c.get('name', slug)
                try:
                    status = get_rumble_status(slug, default_name)
                    if not status:
                        continue

                    is_live = status['is_live']
                    current_id = status['stream_id']
                    display_name = status['name'] or default_name
                    avatar_path = get_avatar_jpg(slug, status.get('pfp_url'))

                    chan_state = state.get(slug, {})
                    prev_was_live = chan_state.get('was_live', False)
                    prev_id = chan_state.get('livestream_id')

                    if is_live:
                        if not initial_boot and (not prev_was_live or (current_id and current_id != prev_id)):
                            notify_live(display_name, status.get('title', ''), avatar_path)
                        state[slug] = {'was_live': True, 'livestream_id': current_id}
                    else:
                        state[slug] = {'was_live': False, 'livestream_id': None}
                except Exception as error:
                    xbmc.log(f'[{ADDON_ID}] Rumble check error for {slug}: {error}', xbmc.LOGWARNING)

                if monitor.waitForAbort(2):
                    break

            save_state(state)
            initial_boot = False

        if monitor.waitForAbort(interval):
            break

    xbmc.log(f'[{ADDON_ID}] Rumble live monitor service stopped', xbmc.LOGINFO)

if __name__ == '__main__':
    run()
