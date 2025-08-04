# TODO: Implement your data models here
# Consider what data structures you'll need for:
# - Storing URL mappings
# - Tracking click counts
# - Managing URL metadata

from datetime import datetime
from typing import Dict, Optional

class URLStore:
    def __init__(self):
        self._store: Dict[str, Dict]={}
    
    def store_url(self, short_code: str, url: str)->None:
        self._store[short_code] = {
            'url': url,
            'created_at': datetime.utcnow().isoformat(),
            'clicks': 0
        }


    def get_url(self, short_code: str) -> Optional[Dict]:
        return self._store.get(short_code)
        
    def increment_clicks(self, short_code: str) -> None:    
        if short_code in self._store:
            self._store[short_code]['clicks']+=1
    
    def get_all_codes(self)->list:
        return list(self._store.keys())
    
    def clear(self)-> None:
        self._store.clear()
