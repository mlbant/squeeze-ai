#!/usr/bin/env python3
"""
Simple migration runner script
"""
import os
import sys

# Set environment variable for local testing
os.environ['DATABASE_URL'] = 'postgresql://squeeze_ai_user:IdbdRXEDeDpxn6oUlSAIJZbUhnsupTyF@dpg-d1t6r0juibrs738vjfr0-a.oregon-postgres.render.com/squeeze_ai'

# Import and run migration
try:
    from migrate_to_postgresql import main
    print("Starting migration...")
    main()
    print("Migration completed!")
except Exception as e:
    print(f"Migration failed: {e}")
    sys.exit(1)