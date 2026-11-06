"""Read local secrets without displaying them; smoke-test actual provider entitlement."""
import os
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.intelligence.earnings_calendar import CalendarConfig, calendar_service
from dashboard.earnings_week import week_bounds

path = Path(__file__).resolve().parents[1] / '.streamlit/secrets.toml'
try:
    settings = tomllib.loads(path.read_text()).get('earnings', {}) if path.exists() else {}
except (OSError, tomllib.TOMLDecodeError):
    print('Local secrets file could not be read. Fix it locally; do not share its contents.')
    sys.exit(1)
config = CalendarConfig(os.environ.get('FINNHUB_API_KEY') or settings.get('api_key', ''), os.environ.get('QI_EARNINGS_USE') or settings.get('use', ''))
start, end = week_bounds(datetime.now(ZoneInfo('America/Toronto')).date())
result = calendar_service.load(config, start, end)
if result.error:
    print(result.error)
    sys.exit(1)
print(f'Authenticated calendar response: {len(result.events)} events; {result.rejected} rejected records. Retrieved {result.retrieved_at.isoformat()}.')
if not result.events:
    print('Empty response: live events/coverage NOT verified. Check date range and entitlement.')
    sys.exit(2)
print('Live retrieval verified. Event confirmation remains unknown; verify issuer announcements separately.')
