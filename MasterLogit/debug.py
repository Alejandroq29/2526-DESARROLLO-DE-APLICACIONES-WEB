#!/usr/bin/env python
# Debug script
try:
    import forms
    print("Forms imported, contents:", dir(forms))
except Exception as e:
    import traceback
    print("Error importing forms:")
    traceback.print_exc()
