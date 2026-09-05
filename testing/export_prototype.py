"""Export the Prototype PF & Q tab without recalculating the source workbook.

python export_prototype.py [fresh-download.xlsx]
Requires openpyxl. Use a fresh Google Sheets XLSX export to refresh the data.
The XLSX is read only. Missing pressure observations become '-' in the CSV;
numeric zero remains zero when backed by a numeric manometer measurement.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import openpyxl


def export(source, output):
    wb = openpyxl.load_workbook(source, data_only=True)
    ws = wb['Prototype PF & Q']
    rows = [[c.value for c in row] for row in ws]
    while rows and all(v is None for v in rows[-1]):
        rows.pop()
    width = max(i+1 for row in rows for i,v in enumerate(row) if v is not None)
    if rows[1][5] != 'Q (L/min)' or rows[1][6] != 'log(PF@.3)':
        raise ValueError('Sheet columns changed: inspect the export mapping before continuing')
    # Pressure layout: K/L calculated pressure; Y/Z manometer observations.
    # Reject a moved column rather than normalising unrelated data.
    for col in (10,11,24,25):
        label = str(rows[1][col]).lower()
        if 'centre' not in label and 'bag' not in label and 'manometer' not in label:
            raise ValueError(f'Pressure column {col+1} changed: {label}')
    for row in rows[3:]:
        if not row[0]:
            continue
        for computed, raw in ((10,24),(11,25)):
            missing = row[raw] is None or str(row[raw]).strip() in ('','-','NM','Not measured')
            if missing:
                row[raw] = '-'
                if row[computed] is None or row[computed] == 0:
                    row[computed] = '-'
            elif row[computed] is None:
                row[computed] = '-'
    with output.open('w',encoding='utf-8',newline='') as file:
        csv.writer(file).writerows([['' if v is None else v for v in row[:width]] for row in rows])
    meta = {'source_file':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'sheet':'Prototype PF & Q','exported_utc':datetime.now(timezone.utc).isoformat(),
            'rows':len(rows),'columns':width,
            'note':'Export time is not the Google Sheet retrieval time. Source XLSX is unchanged; pressure blanks are displayed as dashes.'}
    output.with_suffix('.source.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    wb.close()
    return meta


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('xlsx',nargs='?',type=Path,default=Path(__file__).with_name('filter_testing.xlsx'))
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('prototype_pf_q.csv'))
    args=parser.parse_args()
    print(json.dumps(export(args.xlsx,args.output),indent=2))
