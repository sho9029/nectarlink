#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate Japanese resource coverage, format arguments, and plural forms."""
from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / 'android/app/src/main/res'
ARG = re.compile(r'%(?:\d+\$)?[-+#0 ,]*(?:\d+)?(?:\.\d+)?[sdfxX]|%L?\d+|%n|%%|\\[nrt]')

def arguments(source, target, label):
    assert target and target.strip(), f'{label}: empty translation'
    assert Counter(ARG.findall(source)) == Counter(ARG.findall(target)), f'{label}: format arguments differ: {source!r} -> {target!r}'
    assert source.count('%') == target.count('%'), f'{label}: percent sign lost'
    assert not re.search(r'ZXQ|QXZ|X\d{6}X', target), f'{label}: draft marker left behind'

english = ET.parse(ANDROID / 'values/strings.xml').getroot()
japanese = ET.parse(ANDROID / 'values-ja/strings.xml').getroot()
entries = {e.get('name'): e for e in japanese}
assert len(entries) == len(japanese), 'duplicate Android resource name'
strings = plurals = 0
for entry in english:
    if entry.get('translatable') == 'false':
        continue
    label = entry.get('name')
    assert label in entries, f'missing Android resource: {label}'
    target = entries[label]
    assert entry.tag == target.tag, f'{label}: resource type changed'
    if entry.tag == 'plurals':
        assert [i.get('quantity') for i in target] == ['other'], f'{label}: Japanese needs one other plural form'
        source = next(i for i in entry if i.get('quantity') == 'other')
        arguments(source.text, target[0].text, label)
        plurals += 1
    else:
        arguments(entry.text, target.text, label)
        strings += 1

locale_config = ET.parse(ANDROID / 'xml/locales_config.xml').getroot()
assert any(e.get('{http://schemas.android.com/apk/res/android}name') == 'ja' for e in locale_config), 'Japanese is not registered with Android'
assert '"ja" to "日本語"' in (ROOT / 'android/app/src/main/kotlin/app/nectarlink/android/ui/AppLanguage.kt').read_text()

def messages(tree):
    return {(c.findtext('name'), m.findtext('source')): m for c in tree.findall('context') for m in c.findall('message')}

template = messages(ET.parse(ROOT / 'desktop/app/i18n/template/nectarlink.ts'))
catalogue_tree = ET.parse(ROOT / 'desktop/app/i18n/nectarlink_ja.ts')
assert catalogue_tree.getroot().get('language') == 'ja_JP'
catalogue = messages(catalogue_tree)
assert template.keys() == catalogue.keys(), 'Qt catalogue differs from the source template'
for key, entry in catalogue.items():
    translation = entry.find('translation')
    assert translation is not None and translation.get('type') not in ('unfinished', 'obsolete', 'vanished'), f'{key}: unfinished'
    if entry.get('numerus') == 'yes':
        forms = translation.findall('numerusform')
        assert len(forms) == 1, f'{key}: Japanese needs one numerus form'
        target = forms[0].text
    else:
        target = translation.text
    arguments(key[1], target, key)
assert '("ja", "日本語")' in (ROOT / 'desktop/app/src/i18n.rs').read_text()
print(f'Japanese OK: Android {strings} strings + {plurals} plurals; Qt {len(catalogue)} messages.')
