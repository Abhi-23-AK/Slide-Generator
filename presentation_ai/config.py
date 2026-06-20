# Configuration settings for presentation_ai
import os
os.environ["TEMP"] = "E:\\Slide_Generator\\temp"
os.environ["TMP"] = "E:\\Slide_Generator\\temp"
os.makedirs("E:\\Slide_Generator\\temp", exist_ok=True)

ARCH_ENGINE_VERSION = "v4"  # Supported values: "v2" | "v3" | "v4"
DRAWIO_CLI_PATH = r"E:\Slide_Generator\presentation_ai\bin\draw.io\draw.io.exe"
