import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))
docx_path = os.path.join(base_dir, "reports_export", "FINAL_YEAR_PROJECT_REPORT.docx")
pdf_path = os.path.join(base_dir, "reports_export", "FINAL_YEAR_PROJECT_REPORT.pdf")

ps_command = f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {{
    $doc = $word.Documents.Open('{docx_path}')
    $doc.SaveAs([ref]'{pdf_path}', [ref]17)
    $doc.Close()
    Write-Output "PDF_CONVERSION_SUCCESS"
}} catch {{
    Write-Output "PDF_CONVERSION_FAILED: $_"
}} finally {{
    $word.Quit()
}}
"""

print(f"Opening Word document {docx_path} to render PDF...")
proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True, text=True)
print("STDOUT:", proc.stdout.strip())
if proc.stderr:
    print("STDERR:", proc.stderr.strip())
