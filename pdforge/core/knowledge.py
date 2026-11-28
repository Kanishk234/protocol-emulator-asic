"""Hash-verified, versioned line retrieval; retrieved content is never executed."""
from pathlib import Path
import re
import sqlite3
from .evidence import sha

class Index:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS excerpts USING fts5(text,path UNINDEXED,line UNINDEXED,revision UNINDEXED,sha UNINDEXED,url UNINDEXED,license UNINDEXED)')
    def ingest(self, manifest):
        with self.db:
            for item in manifest:
                if set(item) != {'path','revision','sha256','url','license'} or not all(item.values()):
                    raise ValueError('Incomplete knowledge provenance')
                p = Path(item['path'])
                if sha(p)!=item['sha256']: raise ValueError('Knowledge changed')
                self.db.execute('DELETE FROM excerpts WHERE path=?',(str(p),))
                for i,line in enumerate(p.read_text().splitlines(),1):
                    self.db.execute('INSERT INTO excerpts VALUES(?,?,?,?,?,?,?)',
                                    (line,str(p),i,item['revision'],item['sha256'],item['url'],item['license']))
    def search(self, query):
        terms = re.findall(r'\w+', query)
        if not terms: raise ValueError('Empty search')
        return [dict(zip(('excerpt','path','line','revision','sha256','url','license'),row))
                for row in self.db.execute('SELECT * FROM excerpts WHERE excerpts MATCH ? LIMIT 12',
                                           (' OR '.join('"'+x+'"' for x in terms),))]
