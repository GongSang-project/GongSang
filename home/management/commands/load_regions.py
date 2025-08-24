import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from home.models import Region

REQUIRED_KR_COLS = ["법정동코드", "시도명", "시군구명", "읍면동명"]

class Command(BaseCommand):
    help = (
        'Load regions from CSV/TSV.\n'
        '- Format A) header has "name" (one full name per row)\n'
        '- Format B) headers include: 법정동코드, 시도명, 시군구명, 읍면동명 (tab or comma delimited)'
    )

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Path to CSV/TSV file')

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts['path']
        created = 0
        batch = []
        seen = set()

        # 구분자 자동 감지 + BOM 처리
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',\t;')
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(f, dialect=dialect)

            headers = [h.strip() for h in (reader.fieldnames or [])]

            def flush():
                nonlocal created, batch
                if batch:
                    Region.objects.bulk_create(batch, ignore_conflicts=True)
                    created += len(batch)
                    batch.clear()

            # Case A: 'name' 컬럼 (풀네임이 이미 들어있는 간단 CSV)
            if 'name' in headers:
                for row in reader:
                    name = (row.get('name') or '').strip()
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    batch.append(Region(name=name))
                    if len(batch) >= 2000:
                        flush()
                flush()
                self.stdout.write(self.style.SUCCESS(f'Imported regions (name CSV). created~={created}'))
                return

            # Case B: 법정동 원본 컬럼
            missing = [c for c in REQUIRED_KR_COLS if c not in headers]
            if missing:
                self.stderr.write(self.style.ERROR(f"누락 컬럼: {', '.join(missing)}"))
                self.stderr.write(self.style.WARNING(f"감지된 헤더: {headers}"))
                return

            for row in reader:
                sido = (row.get('시도명') or '').strip()
                sigungu = (row.get('시군구명') or '').strip()
                eupmyeon = (row.get('읍면동명') or '').strip()

                # 시/구만 있는 행은 자동완성 노이즈라면 건너뛰고, 필요한 경우 유지하세요.
                parts = [sido, sigungu, eupmyeon]
                full_name = " ".join([p for p in parts if p]).strip()
                if not full_name or full_name in seen:
                    continue
                seen.add(full_name)
                batch.append(Region(name=full_name))
                if len(batch) >= 2000:
                    flush()
            flush()
            self.stdout.write(self.style.SUCCESS(f'Imported regions (KR TSV/CSV). created~={created}'))
