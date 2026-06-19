with open(r'contacts\views\bulk.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'def _send_with_retry(contact, template, extra_params, retries=3, delay=8):',
    'def _send_with_retry(contact, template, extra_params, retries=3, delay=8, language="en"):'
)
content = content.replace(
    'def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None):',
    'def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None, language="en"):'
)
content = content.replace(
    '        success = _send_with_retry(contact, template, extra_params)',
    '        success = _send_with_retry(contact, template, extra_params, language=language)'
)
content = content.replace(
    '                contact=contact,\n            )',
    '                contact=contact,\n                language=language,\n            )'
)

with open(r'contacts\views\bulk.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
