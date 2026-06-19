# ============================================================
#  update_wa_log.ps1  —  fixed version
#  Replaces the WA log thread block in sk_dashboard.html
# ============================================================

$filePath = "C:\Users\Joseph\Desktop\sk_contact_base\templates\contacts\sk_dashboard.html"

if (-not (Test-Path $filePath)) {
    Write-Host "ERROR: File not found at $filePath" -ForegroundColor Red
    exit 1
}

# Backup
$backupPath = $filePath + ".bak"
Copy-Item $filePath $backupPath -Force
Write-Host "Backup created: $backupPath" -ForegroundColor Cyan

# Read file as single string
$content = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)

# ── NEW BLOCK (written to a temp file to avoid PS parsing issues) ──
$newBlockPath = "C:\Users\Joseph\Desktop\sk_contact_base\wa_log_new_block.html"

$newBlock = @"
          `{% for log in wa_logs %`}
          <div class="wa-thread" style="`{% if log.direction == 'in' %`}background:var(--green-50);border-left:3px solid var(--green);`{% endif %`}">

            <div class="wa-thread-avatar" style="`{% if log.direction == 'in' %`}background:linear-gradient(135deg,var(--green),#128C7E);`{% endif %`}">
              `{% if log.contact %`}`{{ log.contact.full_name|slice:":2"|upper `}}`{% else %`}??`{% endif %`}
            </div>

            <div class="wa-thread-info">
              <div class="wa-thread-name">
                `{% if log.contact %`}`{{ log.contact.full_name `}}`{% else %`}`{{ log.phone `}}`{% endif %`}
                `{% if log.direction == 'in' %`}
                  <span style="font-size:10px;font-weight:700;background:var(--green);color:#fff;padding:2px 8px;border-radius:100px;margin-left:6px;">
                    &larr; REPLY
                  </span>
                `{% endif %`}
              </div>
              <div class="wa-thread-preview">
                `{% if log.direction == 'in' %`}
                  <strong style="color:var(--green-700);">They said:</strong> `{{ log.message_text|default:"(no text)" `}}
                `{% else %`}
                  Template: <strong>`{{ log.template `}}</strong>`{% if log.error %`} &mdash; `{{ log.error|truncatechars:60 `}}`{% endif %`}
                `{% endif %`}
              </div>
            </div>

            <div class="wa-thread-meta">
              <div class="wa-thread-time">`{{ log.timestamp|date:"d M H:i" `}}</div>
              <div class="wa-status-pill `{% if log.direction == 'in' %`}wa-status-sent`{% elif log.status == 'sent' %`}wa-status-sent`{% else %`}wa-status-failed`{% endif %`}">
                <i class="fas fa-`{% if log.direction == 'in' %`}reply`{% elif log.status == 'sent' %`}check`{% else %`}times`{% endif %`}-circle"></i>
                `{% if log.direction == 'in' %`}Received`{% else %`}`{{ log.status|title `}}`{% endif %`}
              </div>
            </div>

            `{% if log.direction == 'in' %`}
              `{% if log.contact %`}
                <a href="`{{ log.contact.whatsapp_chat_url `}}" target="_blank" class="wa-open-btn">
                  <i class="fab fa-whatsapp"></i> Reply
                </a>
              `{% elif log.phone %`}
                <a href="https://wa.me/`{{ log.phone `}}" target="_blank" class="wa-open-btn">
                  <i class="fab fa-whatsapp"></i> Reply
                </a>
              `{% endif %`}
            `{% else %`}
              `{% if log.contact %`}
                <a href="`{{ log.contact.whatsapp_chat_url `}}" target="_blank" class="wa-open-btn">
                  <i class="fab fa-whatsapp"></i> Chat
                </a>
              `{% endif %`}
            `{% endif %`}

          </div>
          `{% empty %`}
          <div style="padding:40px;text-align:center;color:var(--gray-400);">
            <i class="fab fa-whatsapp" style="font-size:32px;margin-bottom:12px;display:block;color:var(--gray-200);"></i>
            No messages yet. Use Bulk Messaging to send your first message.
          </div>
          `{% endfor %`}
"@

# Fix backtick escapes — restore real Django tags
$newBlock = $newBlock -replace '`\{', '{' -replace '`\}', '}'

# Save new block to helper file regardless
[System.IO.File]::WriteAllText($newBlockPath, $newBlock, [System.Text.Encoding]::UTF8)
Write-Host "New block saved to: $newBlockPath" -ForegroundColor Cyan

# ── Find the old block start and end ──────────────────────────
$startMarker = '{% for log in wa_logs %}'
$endMarker   = '{% endfor %}'

$startIdx = $content.IndexOf($startMarker)

if ($startIdx -eq -1) {
    Write-Host ""
    Write-Host "WARNING: Could not find the wa_logs for loop in the file." -ForegroundColor Yellow
    Write-Host "Please open sk_dashboard.html, find the line:" -ForegroundColor White
    Write-Host "  $startMarker" -ForegroundColor Gray
    Write-Host "and replace the entire block (to the matching endfor) with the contents of:" -ForegroundColor White
    Write-Host "  $newBlockPath" -ForegroundColor Cyan
    exit 1
}

# Find the endfor AFTER the startMarker (there may be multiple endfor tags)
$endIdx = $content.IndexOf($endMarker, $startIdx)

if ($endIdx -eq -1) {
    Write-Host "ERROR: Found start of wa_logs block but could not find its closing endfor." -ForegroundColor Red
    exit 1
}

# Include the length of the endMarker itself
$endIdx = $endIdx + $endMarker.Length

# Slice out old block and stitch in new block
$before  = $content.Substring(0, $startIdx)
$after   = $content.Substring($endIdx)
$newContent = $before + $newBlock + $after

# Write back
[System.IO.File]::WriteAllText($filePath, $newContent, [System.Text.Encoding]::UTF8)

Write-Host ""
Write-Host "SUCCESS: WA Log block updated!" -ForegroundColor Green
Write-Host ""
Write-Host "Changes made:" -ForegroundColor White
Write-Host "  - Inbound replies: green background + left border" -ForegroundColor Gray
Write-Host "  - REPLY badge on incoming messages" -ForegroundColor Gray
Write-Host "  - Shows reply text (log.message_text)" -ForegroundColor Gray
Write-Host "  - Reply button opens WhatsApp Web to that contact" -ForegroundColor Gray
Write-Host "  - Outbound messages unchanged" -ForegroundColor Gray
Write-Host ""
