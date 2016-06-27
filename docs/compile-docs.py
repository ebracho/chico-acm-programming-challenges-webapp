#!/usr/bin/env python3.5
import markdown

# api doc
markdown.markdownFromFile('docs/api.md', 'api/api.html', safe_mode='escape')

