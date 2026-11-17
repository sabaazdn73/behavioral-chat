"""Copy the engine into the skill so it runs without the MCP server, then zip it for upload."""
import os, shutil, zipfile

root = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(root, "src", "behavioral_chat")
skill = os.path.join(root, "skills", "behavioral-chat")
dst = os.path.join(skill, "scripts", "behavioral_chat")
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "server.py"))
init = os.path.join(dst, "__init__.py")
os.makedirs(os.path.join(root, "dist"), exist_ok=True)
out = os.path.join(root, "dist", "behavioral-chat-skill.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _, files in os.walk(skill):
        for f in files:
            if "__pycache__" in base:
                continue
            full = os.path.join(base, f)
            z.write(full, os.path.join("behavioral-chat", os.path.relpath(full, skill)))
print("skill zip:", out)
