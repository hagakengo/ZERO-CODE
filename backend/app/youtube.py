"""Read-only Google API boundary; upstream errors never expose credentials."""
from datetime import date, timedelta
from pathlib import Path
import httpx
from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parents[1] / '.env'

class YouTubeError(Exception):
    pass

def settings():
    return dotenv_values(ENV_PATH)

def configured():
    return all(settings().get(k) for k in ('YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN', 'YOUTUBE_CHANNEL_ID'))

def counter(value):
    if isinstance(value, bool) or not str(value).isdigit() or int(value) > 9007199254740991:
        raise YouTubeError('Invalid YouTube counter; nothing saved.')
    return int(value)

def request(client, method, url, **kwargs):
    try:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except (httpx.HTTPError, ValueError):
        raise YouTubeError('YouTube API failed. Check OAuth, enabled APIs and quota.') from None

def fetch_metrics(today):
    config = settings()
    if not configured():
        raise YouTubeError('YouTube is not configured.')
    with httpx.Client(timeout=20, follow_redirects=False) as client:
        token = request(client, 'POST', 'https://oauth2.googleapis.com/token', data={
            'client_id': config['YOUTUBE_CLIENT_ID'], 'client_secret': config['YOUTUBE_CLIENT_SECRET'],
            'refresh_token': config['YOUTUBE_REFRESH_TOKEN'], 'grant_type': 'refresh_token'})
        access = token.get('access_token')
        if not isinstance(access, str) or not access:
            raise YouTubeError('OAuth did not return an access token.')
        headers = {'Authorization': f'Bearer {access}'}
        channel = request(client, 'GET', 'https://www.googleapis.com/youtube/v3/channels',
                          headers=headers, params={'part': 'statistics', 'mine': 'true'})
        try:
            item = next(item for item in channel['items'] if item['id'] == config['YOUTUBE_CHANNEL_ID'])
            stats = item['statistics']
            if stats.get('hiddenSubscriberCount'):
                raise YouTubeError('Subscriber count is hidden; nothing saved.')
            values = {'youtube_subscribers': counter(stats['subscriberCount']), 'youtube_views': counter(stats['viewCount'])}
        except (KeyError, TypeError, StopIteration):
            raise YouTubeError('Configured channel or required statistics were not returned.') from None
        warning = None
        if config.get('YOUTUBE_ANALYTICS_ENABLED', 'true').lower() == 'true':
            try:
                start = date.fromisoformat(config.get('YOUTUBE_ANALYTICS_START_DATE') or '2005-01-01')
                end = today - timedelta(days=1)
                if start > end:
                    raise ValueError()
                report = request(client, 'GET', 'https://youtubeanalytics.googleapis.com/v2/reports', headers=headers,
                    params={'ids': 'channel==MINE', 'startDate': start.isoformat(), 'endDate': end.isoformat(),
                            'metrics': 'estimatedMinutesWatched,likes,comments'})
                raw = dict(zip([c['name'] for c in report['columnHeaders']], report['rows'][0], strict=True))
                analytics = {field: counter(raw[key]) for key, field in (
                    ('estimatedMinutesWatched', 'youtube_watch_minutes'), ('likes', 'youtube_likes'), ('comments', 'youtube_comments'))}
                values.update(analytics)
                values.update(youtube_analytics_observed_on=today, youtube_analytics_start_on=start, youtube_analytics_end_on=end)
            except (YouTubeError, ValueError, KeyError, TypeError, IndexError):
                warning = 'Analytics unavailable; previous values retained. Check scopes and report dates.'
        return values, warning
