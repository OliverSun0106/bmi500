"""Small time.time-based section recorder; no Scanpy dependency."""
import csv
import time


class SectionTimer:
    def __init__(self):
        self.rows = []
        self.path = None
        self.started = time.time()

    def finish(self, section):
        elapsed = time.time() - self.started
        self.rows.append({'section': section, 'seconds': elapsed})
        print(f'SECTION {section}: {elapsed:.6f} seconds', flush=True)
        if self.path is not None:
            with self.path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=['section', 'seconds'])
                writer.writeheader()
                writer.writerows(self.rows)
        # Exclude recorder printing and CSV writing from the next section.
        self.started = time.time()
