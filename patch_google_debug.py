with open(r'contacts\services\google_contacts.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        except Exception:
            continue'''
new = '''        except Exception as e:
            print(f'[Google Sync] Failed for {getattr(contact, "id", "?")}: {e}')
            continue'''

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\services\google_contacts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched')
else:
    print('Not found')
