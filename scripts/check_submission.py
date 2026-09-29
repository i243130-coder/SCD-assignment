#!/usr/bin/env python3
"""CivicPulse submission checker. Catches mechanical failures."""
import os, sys, re, glob

errors = []
warnings = []

def check(condition, message, is_error=True):
    if not condition:
        (errors if is_error else warnings).append(message)

# Root of repo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# .env tracked?
check(not os.path.exists('.env') or '.env' in open('.gitignore').read(), '.env might be tracked in git')

# Secrets in obvious files
for f in glob.glob('**/*.yaml', recursive=True) + glob.glob('**/*.yml', recursive=True):
    if '.git/' in f: continue
    content = open(f).read()
    check('GROQ_API_KEY:' not in content or 'placeholder' in content.lower() or 'PLACEHOLDER' in content,
          f'Possible secret in {f}')

# Unpinned images
for dockerfile in ['backend/Dockerfile', 'frontend/Dockerfile']:
    if os.path.exists(dockerfile):
        content = open(dockerfile).read()
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.upper().startswith('FROM'):
                parts = stripped.split()
                if len(parts) >= 2:
                    image = parts[1]  # The image is always the second token
                    if ':' not in image and image.lower() != 'scratch':
                        errors.append(f'Unpinned image in {dockerfile}: {stripped}')

# localhost in compose/k8s
for f in ['compose.yaml', 'compose.prod.yaml'] + glob.glob('k8s/**/*.yaml', recursive=True):
    if os.path.exists(f):
        content = open(f).read()
        if 'localhost' in content and 'healthcheck' not in content.lower():
            # localhost in healthcheck is OK
            lines_with_localhost = [l for l in content.split('\n') if 'localhost' in l and 'HEALTHCHECK' not in l.upper() and 'healthcheck' not in l.lower()]
            if lines_with_localhost:
                errors.append(f'localhost in {f} (service-to-service should use service names)')

# Production database ports
if os.path.exists('compose.prod.yaml'):
    content = open('compose.prod.yaml').read()
    check('5432' not in content.split('ports')[0] if 'ports' in content else True,
          'Published database port in compose.prod.yaml', is_error=True)

# :latest deployment
for f in glob.glob('k8s/**/*.yaml', recursive=True):
    if os.path.exists(f):
        content = open(f).read()
        if ':latest' in content:
            errors.append(f':latest found in {f}')

# PostgreSQL Deployment (should be StatefulSet)
for f in glob.glob('k8s/**/*.yaml', recursive=True):
    if 'postgres' in f.lower() and os.path.exists(f):
        content = open(f).read()
        if 'kind: Deployment' in content and 'StatefulSet' not in content:
            errors.append(f'PostgreSQL uses Deployment instead of StatefulSet in {f}')

# Missing important files
required_files = [
    'README.md', 'compose.yaml', 'compose.prod.yaml', '.env.example', '.gitignore',
    'backend/Dockerfile', 'frontend/Dockerfile',
    'backend/alembic.ini', 'backend/alembic/versions/001_create_complaints.py',
    'k8s/base/kustomization.yaml',
    '.github/workflows/ci.yml', '.github/workflows/cd.yml',
    'docs/AI-USAGE.md', 'docs/RUNBOOK.md', 'docs/ENGINEERING-NOTES.md',
    'docs/adr/0001-provider-interface.md',
    'scripts/check_submission.py',
]
for f in required_files:
    check(os.path.exists(f), f'Missing required file: {f}')

# Report
print('\n=== CivicPulse Submission Checker ===\n')
if errors:
    print(f'❌ {len(errors)} ERROR(S):')
    for e in errors:
        print(f'  ❌ {e}')
if warnings:
    print(f'\n⚠️  {len(warnings)} WARNING(S):')
    for w in warnings:
        print(f'  ⚠️  {w}')
if not errors and not warnings:
    print('✅ All checks passed!')
else:
    print(f'\n{len(errors)} errors, {len(warnings)} warnings')

sys.exit(1 if errors else 0)
