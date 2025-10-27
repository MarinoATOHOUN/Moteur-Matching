import traceback

try:
    print("Attempting to import main.py...")
    from api import main
    print("Successfully imported main.py")
except Exception as e:
    print("Failed to import main.py. See traceback below:")
    traceback.print_exc()
